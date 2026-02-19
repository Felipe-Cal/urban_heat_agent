import pydeck as pdk
import streamlit as st

def create_map(df_thermal, df_trees, df_sensors, show_thermal, show_trees, show_sensors, center_lat=34.0522, center_lon=-118.2437):
    """Generates the PyDeck map with toggleable layers."""
    
    layers = []
    
    # 1. Thermal Layer (Heatmap)
    if show_thermal:
        thermal_layer = pdk.Layer(
            "HeatmapLayer",
            data=df_thermal,
            get_position='[lon, lat]',
            get_weight='weight',
            radiusPixels=60,
            intensity=1,
            threshold=0.03,
            opacity=0.6,
            color_range=[
                [65, 182, 196], # Cool (Blue-ish)
                [254, 204, 92], # Warm (Yellow)
                [227, 26, 28]   # Hot (Red)
            ]
        )
        layers.append(thermal_layer)

    # 2. Tree Canopy Layer (Scatterplot)
    if show_trees:
        tree_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_trees,
            get_position='[lon, lat]',
            get_fill_color='[5, 150, 105, 200]', # Emerald-600
            get_radius=30,
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=3,
            radius_max_pixels=10
        )
        layers.append(tree_layer)

    # 3. Sensor Layer (Scatterplot/Icon - using rings for visibility)
    if show_sensors:
        # Outer ring
        sensor_layer_ring = pdk.Layer(
            "ScatterplotLayer",
            data=df_sensors,
            get_position='[lon, lat]',
            get_fill_color='[124, 58, 237, 80]', # Violet-600, transparent
            get_radius=150,
            pickable=False,
        )
        # Inner dot
        sensor_layer_dot = pdk.Layer(
            "ScatterplotLayer",
            data=df_sensors,
            get_position='[lon, lat]',
            get_fill_color='[124, 58, 237, 255]', # Violet-600, solid
            get_radius=40,
            pickable=True,
            auto_highlight=True,
             radius_min_pixels=4,
            radius_max_pixels=8
        )
        layers.append(sensor_layer_ring)
        layers.append(sensor_layer_dot)

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
            "backgroundColor": "rgba(255, 255, 255, 0.9)",
            "color": "#0f172a",
            "fontSize": "12px",
            "borderRadius": "8px",
            "padding": "8px",
            "boxShadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
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
