import streamlit.components.v1 as components
import pandas as pd
import json

def df_to_geojson(df, geometry_column, properties=None):
    """Convert a DataFrame to a GeoJSON FeatureCollection."""
    if df.empty:
        return {"type": "FeatureCollection", "features": []}
    
    features = []
    for _, row in df.iterrows():
        feature = {
            "type": "Feature",
            "properties": {p: row[p] for p in properties} if properties else {},
            "geometry": None
        }
        
        geom_val = row.get(geometry_column) if geometry_column else None
        if geometry_column == 'polygon' and geom_val:
            feature["geometry"] = {"type": "Polygon", "coordinates": [geom_val]}
        elif geometry_column == 'path' and geom_val:
            feature["geometry"] = {"type": "LineString", "coordinates": geom_val}
        elif 'lat' in row and 'lon' in row and pd.notnull(row['lat']) and pd.notnull(row['lon']):
            # Assume point if it's lat/lon columns
            feature["geometry"] = {"type": "Point", "coordinates": [row['lon'], row['lat']]}
            if not properties:
                feature["properties"] = {k: v for k, v in row.to_dict().items() if k not in ['lat', 'lon']}
        
        if feature["geometry"]:
            features.append(feature)
    
    return {"type": "FeatureCollection", "features": features}

def prepare_map_data(config):
    """Transform MapConfig data into GeoJSON layers for MapLibre."""
    data = config.data
    toggles = config.toggles
    layers = []

    if toggles.thermal and not data.df_thermal.empty:
        layers.append({
            "id": "Thermal",
            "type": "HeatmapLayer",
            "data": df_to_geojson(data.df_thermal, None)
        })

    if toggles.buildings and not data.df_buildings.empty:
        layers.append({
            "id": "Buildings",
            "type": "PolygonLayer",
            "data": df_to_geojson(data.df_buildings, 'polygon', ['height', 'name']),
            "color": "#ff0055"
        })

    if toggles.traffic and not data.df_traffic.empty:
        layers.append({
            "id": "Traffic",
            "type": "PathLayer",
            "data": df_to_geojson(data.df_traffic, 'path', ['name']),
            "color": "#f59e0b"
        })

    # Nature & Assets
    asset_layers = [
        ("trees", data.df_trees, "Trees", "#059669", 2),
        ("water", data.df_water, "Water", "#0ea5e9", 5),
        ("parks", data.df_parks, "Parks", "#84cc16", 8),
        ("shelters", data.df_shelters, "Shelters", "#f59e0b", 4),
        ("fountains", data.df_fountains, "Fountains", "#38bdf8", 2),
        ("green_roofs", data.df_green_roofs, "GreenRoofs", "#a3e635", 3),
        ("gardens", data.df_gardens, "Gardens", "#4d7c0f", 4),
        ("forests", data.df_forests, "Forests", "#15803d", 10),
        ("wetlands", data.df_wetlands, "Wetlands", "#0c4a6e", 12),
        ("sensors", data.df_sensors, "Sensors", "#3b82f6", 6),
    ]

    for toggle_name, df, layer_id, color, radius in asset_layers:
        if getattr(toggles, toggle_name) and not df.empty:
            layers.append({
                "id": layer_id,
                "type": "ScatterplotLayer",
                "data": df_to_geojson(df, None),
                "color": color,
                "radius": radius
            })

    return layers

def maplibre_component(config):
    """
    Custom MapLibre component that renders layers and sends back viewport bounds.
    """
    layers = prepare_map_data(config)
    
    config_dict = {
        "center_lat": config.center_lat,
        "center_lon": config.center_lon,
        "zoom": 13,
        "pitch": 45,
        "layers": layers,
        "map_style": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
    }

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>MapLibre GL JS BBox Component</title>
        <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
        <script src="https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet" />
        <style>
            body { margin: 0; padding: 0; height: 500px; width: 100%; overflow: hidden; background: #000; color: #fff; font-family: monospace; }
            #map { position: absolute; top: 0; bottom: 0; width: 100%; border-radius: 8px; }
            #status { position: absolute; top: 0; left: 0; padding: 4px 8px; background: rgba(0,0,0,0.8); font-size: 10px; z-index: 9999; border-bottom-right-radius: 4px; pointer-events: none; }
        </style>
    </head>
    <body>
    <div id="status">INIT...</div>
    <div id="map"></div>
    <script>
        const statusEl = document.getElementById('status');
        const setStatus = (msg) => { 
            statusEl.innerText = msg; 
            console.log("[Map] " + msg); 
        };

        window.onerror = function(msg, url, line) {
            setStatus("JS ERR: " + msg.substring(0, 20));
            return false;
        };

        let config;
        try {
            config = __CONFIG__;
            setStatus("CFG: " + config.center_lat.toFixed(2) + "," + config.center_lon.toFixed(2));
        } catch (e) {
            setStatus("ERR: " + e.message);
        }


        let map;
        function init() {
            try {
                if (!window.maplibregl) { setStatus("LIB MISSING"); return; }
                
                // Fallback background color
                document.getElementById('map').style.backgroundColor = '#111';

                const styleUrl = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';
                
                map = new maplibregl.Map({
                    container: 'map',
                    style: styleUrl,
                    center: [config.center_lon, config.center_lat],
                    zoom: config.zoom || 13,
                    pitch: config.pitch || 45,
                    antialias: true
                });

                // Style timeout
                const st = setTimeout(() => {
                    if (!map.isStyleLoaded()) setStatus("STYLE TIMEOUT - TILE ERR?");
                }, 8000);

                map.on('load', () => {
                    clearTimeout(st);
                    setStatus("LOADED: " + (config.layers ? config.layers.length : 0) + " L");
                    updateLayers(config.layers || []);
                    setTimeout(() => {
                        statusEl.style.opacity = '0.5';
                    }, 500);
                });

                map.on('error', (e) => {
                    setStatus("ERR: " + (e.error ? e.error.message.substring(0,20) : "STYLE"));
                    console.error(e);
                });

            } catch (e) {
                setStatus("EXC: " + e.message);
            }
        }


        function updateLayers(layers) {
            if (!map || !map.isStyleLoaded()) return;
            
            // Cleanup
            map.getStyle().layers.forEach(l => {
                if (l.id.startsWith('gaia-')) {
                    map.removeLayer(l.id);
                    if (map.getSource(l.id)) map.removeSource(l.id);
                }
            });

            layers.forEach(layer => {
                const sid = `gaia-${layer.id}`;
                try {
                    map.addSource(sid, { type: 'geojson', data: layer.data });
                    if (layer.type === 'HeatmapLayer') {
                        map.addLayer({
                            id: sid, type: 'heatmap', source: sid,
                            paint: {
                                'heatmap-weight': ['get', 'weight'],
                                'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'], 0, 'rgba(0,0,255,0)', 0.5, 'yellow', 1, 'red'],
                                'heatmap-radius': 30, 'heatmap-opacity': 0.7
                            }
                        });
                    } else if (layer.type === 'ScatterplotLayer') {
                        map.addLayer({
                            id: sid, type: 'circle', source: sid,
                            paint: { 'circle-radius': layer.radius || 4, 'circle-color': layer.color || '#00e5ff', 'circle-stroke-width': 1, 'circle-stroke-color': '#fff' }
                        });
                    } else if (layer.type === 'PolygonLayer') {
                        map.addLayer({
                            id: sid, type: 'fill-extrusion', source: sid,
                            paint: { 'fill-extrusion-color': layer.color || '#ff0055', 'fill-extrusion-height': ['get', 'height'] || 0, 'fill-extrusion-opacity': 0.8 }
                        });
                    } else {
                        map.addLayer({ id: sid, type: 'line', source: sid, paint: { 'line-color': layer.color || '#f59e0b', 'line-width': 2 } });
                    }
                } catch (e) { console.warn(sid, e); }
            });
        }

        if (config) init();
    </script>
    </body>
    </html>
    """
    
    html_code = html_template.replace("__CONFIG__", json.dumps(config_dict))
    return components.html(html_code, height=500)
