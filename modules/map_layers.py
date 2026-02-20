import pydeck as pdk
import streamlit as st

def create_map(df_thermal, df_trees, df_water, df_parks, df_shelters, df_fountains, df_green_roofs, df_gardens, df_forests, df_wetlands, df_sensors, df_ndvi, df_albedo, df_buildings, df_traffic, df_population,
               show_thermal, show_trees, show_water, show_parks, show_shelters, show_fountains, show_green_roofs, show_gardens, show_forests, show_wetlands, show_sensors, show_ndvi, show_albedo, show_buildings, show_traffic, show_population,
               center_lat=34.0522, center_lon=-118.2437):
    """Generates the PyDeck map with toggleable layers."""
    
    layers = []
    
    # 1. Thermal Heatmap Layer
    if show_thermal:
        thermal_layer = pdk.Layer(
            "HeatmapLayer",
            data=df_thermal,
            opacity=0.8,
            get_position=['lon', 'lat'],
            get_weight='weight',
            aggregation='"SUM"',
            color_range=[
                [254, 235, 200],  # #feebc8 Light orange
                [253, 204, 138],  # #fdcc8a
                [252, 141, 89],   # #fc8d59 Orange
                [227, 74, 51],    # #e34a33 Red-orange
                [179, 0, 0]       # #b30000 Dark red
            ],
            intensity=1,
            radius_pixels=80,
        )
        layers.append(thermal_layer)
        
    # 1b. NDVI Heatmap Layer (Vegetation Greenness)
    if show_ndvi and not df_ndvi.empty:
        ndvi_layer = pdk.Layer(
            "HeatmapLayer",
            data=df_ndvi,
            opacity=0.7,
            get_position=['lon', 'lat'],
            get_weight='weight',
            aggregation='"SUM"',
            color_range=[
                [247, 252, 245],
                [229, 245, 224],
                [199, 233, 192],
                [161, 217, 155],
                [116, 196, 118],
                [65, 171, 93]
            ],
            intensity=1,
            radius_pixels=70,
        )
        layers.append(ndvi_layer)
        
    # 1c. Albedo Heatmap Layer (Surface Reflectance)
    if show_albedo and not df_albedo.empty:
        albedo_layer = pdk.Layer(
            "HeatmapLayer",
            data=df_albedo,
            opacity=0.7,
            get_position=['lon', 'lat'],
            get_weight='weight',
            aggregation='"SUM"',
            color_range=[
                [80, 80, 80],
                [140, 140, 140],
                [190, 190, 190],
                [230, 230, 230],
                [255, 255, 204],
                [255, 255, 102]
            ],
            intensity=1,
            radius_pixels=70,
        )
        layers.append(albedo_layer)
        
    # 1d. Population Density Heatmap
    if show_population and not df_population.empty:
        population_layer = pdk.Layer(
            "HeatmapLayer",
            data=df_population,
            opacity=0.7,
            get_position=['lon', 'lat'],
            get_weight='weight',
            aggregation='"SUM"',
            color_range=[
                [241, 238, 246],
                [208, 209, 230],
                [166, 189, 219],
                [116, 169, 207],
                [43, 140, 190],
                [4, 90, 141]   # Dark Blue
            ],
            intensity=1,
            radius_pixels=60,
        )
        layers.append(population_layer)
        
    # 1e. Building Mass (3D Extruded Polygons)
    if show_buildings and not df_buildings.empty:
        buildings_layer = pdk.Layer(
            "PolygonLayer",
            data=df_buildings,
            opacity=0.8,
            stroked=False,
            get_polygon="polygon",
            filled=True,
            extruded=True,
            wireframe=True,
            get_elevation="height",
            get_fill_color="[255, 0, 85, 180]", # Neon pink/red for concrete mass
            get_line_color="[255, 255, 255]",
            pickable=True,
            auto_highlight=True,
        )
        layers.append(buildings_layer)
        
    # 1f. Traffic Arteries (Path Layer)
    if show_traffic and not df_traffic.empty:
        traffic_layer = pdk.Layer(
            "PathLayer",
            data=df_traffic,
            width_scale=5,
            width_min_pixels=2,
            get_path="path",
            get_color="[245, 158, 11, 255]", # Amber/Orange for roads
            get_width=3,
            pickable=True,
            auto_highlight=True,
        )
        layers.append(traffic_layer)

    # 2. Tree Canopy Layer (Scatterplot)
    if show_trees and not df_trees.empty:
        tree_layer = pdk.Layer(
            "ScatterplotLayer",
            id="Trees",
            data=df_trees,
            get_position=['lon', 'lat'],
            get_fill_color='[5, 150, 105, 200]', # Emerald-600
            get_radius=30,
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=3,
            radius_max_pixels=10
        )
        layers.append(tree_layer)

    # 3. Water Resources Layer (Scatterplot)
    if show_water and not df_water.empty:
        water_layer = pdk.Layer(
            "ScatterplotLayer",
            id="Water",
            data=df_water,
            get_position=['lon', 'lat'],
            get_fill_color='[14, 165, 233, 200]', # Sky-500
            get_radius=40,
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=4,
            radius_max_pixels=12
        )
        layers.append(water_layer)
        
    # 4. Urban Parks Layer (Scatterplot)
    if show_parks and not df_parks.empty:
        park_layer = pdk.Layer(
            "ScatterplotLayer",
            id="Parks",
            data=df_parks,
            get_position=['lon', 'lat'],
            get_fill_color='[132, 204, 22, 200]', # Lime-500
            get_radius=60,
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=5,
            radius_max_pixels=15
        )
        layers.append(park_layer)

    # 5. Shelters Layer (Amber-500)
    if show_shelters and not df_shelters.empty:
        shelter_layer = pdk.Layer(
            "ScatterplotLayer",
            id="Shelters",
            data=df_shelters,
            get_position=['lon', 'lat'],
            get_fill_color='[245, 158, 11, 200]',
            get_radius=80,
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=6,
            radius_max_pixels=18
        )
        layers.append(shelter_layer)

    # 6. Drinking Fountains Layer (Sky-400)
    if show_fountains and not df_fountains.empty:
        fountain_layer = pdk.Layer(
            "ScatterplotLayer",
            id="Fountains",
            data=df_fountains,
            get_position=['lon', 'lat'],
            get_fill_color='[56, 189, 248, 200]', 
            get_radius=20,
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=3,
            radius_max_pixels=8
        )
        layers.append(fountain_layer)

    # 7. Green Roofs Layer (Lime-400)
    if show_green_roofs and not df_green_roofs.empty:
        roof_layer = pdk.Layer(
            "ScatterplotLayer",
            id="GreenRoofs",
            data=df_green_roofs,
            get_position=['lon', 'lat'],
            get_fill_color='[163, 230, 53, 200]', 
            get_radius=30,
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=4,
            radius_max_pixels=10
        )
        layers.append(roof_layer)

    # 8. Gardens Layer (Lime-700)
    if show_gardens and not df_gardens.empty:
        garden_layer = pdk.Layer(
            "ScatterplotLayer",
            id="Gardens",
            data=df_gardens,
            get_position=['lon', 'lat'],
            get_fill_color='[77, 124, 15, 200]', 
            get_radius=50,
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=5,
            radius_max_pixels=12
        )
        layers.append(garden_layer)

    # 9. Forests Layer (Green-700)
    if show_forests and not df_forests.empty:
        forest_layer = pdk.Layer(
            "ScatterplotLayer",
            id="Forests",
            data=df_forests,
            get_position=['lon', 'lat'],
            get_fill_color='[21, 128, 61, 200]', 
            get_radius=100,
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=8,
            radius_max_pixels=30
        )
        layers.append(forest_layer)

    # 10. Wetlands Layer (Sky-900)
    if show_wetlands and not df_wetlands.empty:
        wetland_layer = pdk.Layer(
            "ScatterplotLayer",
            id="Wetlands",
            data=df_wetlands,
            get_position=['lon', 'lat'],
            get_fill_color='[12, 74, 110, 200]', 
            get_radius=150,
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=10,
            radius_max_pixels=40
        )
        layers.append(wetland_layer)

    # 11. Sensor Layer (AQI Nodes)
    if show_sensors and not df_sensors.empty:
        sensor_layer_dot = pdk.Layer(
            "ScatterplotLayer",
            id="Sensors",
            data=df_sensors,
            get_position='[lon, lat]',
            get_fill_color='color', 
            get_radius=150,
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=6,
            radius_max_pixels=12
        )
        layers.append(sensor_layer_dot)
        
    # 12. Simulated Interventions (Sandbox Mode)
    simulations = st.session_state.get('simulations', [])
    if simulations:
        sim_layer = pdk.Layer(
            "ScatterplotLayer",
            data=simulations,
            get_position='[lon, lat]',
            get_fill_color='color',
            get_radius='radius',
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=15,
            radius_max_pixels=50,
        )
        layers.append(sim_layer)

    # Base Map View
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=13,
        pitch=45,
        bearing=0
    )

    # Tooltip configuration
    tooltip = {
        "html": "{tooltip}",
        "style": {
            "backgroundColor": "rgba(15, 23, 42, 0.95)",
            "color": "#e2e8f0",
            "fontSize": "13px",
            "fontFamily": "Inter, sans-serif",
            "borderRadius": "6px",
            "padding": "12px",
            "border": "1px solid #10b981",
            "boxShadow": "0 4px 6px -1px rgba(0, 0, 0, 0.5)"
        }
    }

    # Retrieve Mapbox Token from Secrets
    mapbox_api_key = None
    if "mapbox" in st.secrets:
        mapbox_api_key = st.secrets["mapbox"]["access_token"]
    
    if not mapbox_api_key:
        st.error("⚠️ Mapbox API Key not found in .streamlit/secrets.toml")
        # Fallback to a style that might work without key (often still needs one for Mapbox, but Carto doesn't)
        map_style = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
        st.caption("Falling back to CartoDB (No Key Required) - styling might differ.")
    else:
        map_style = "mapbox://styles/mapbox/light-v10"

    # Render Deck
    r = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style=map_style,
        api_keys={"mapbox": mapbox_api_key} if mapbox_api_key else None,
        tooltip=tooltip
    )
    
    return r
