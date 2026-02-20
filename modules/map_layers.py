"""
Map layer composition for Gaia Heat Sync.

Accepts a single MapConfig dataclass instead of 32 positional arguments,
making the function easier to test, call, and extend.
"""
import pydeck as pdk
import streamlit as st

from modules.models import MapConfig


def create_map(config: MapConfig) -> pdk.Deck:
    """
    Build a PyDeck Deck from a MapConfig.

    Args:
        config: MapConfig dataclass containing all data, toggle states,
                centre coordinates, and any sandbox simulations.

    Returns:
        A pdk.Deck ready to be rendered with st.pydeck_chart.
    """
    data = config.data
    toggles = config.toggles
    layers = []

    # ------------------------------------------------------------------
    # Satellite indices (heatmaps)
    # ------------------------------------------------------------------
    if toggles.thermal:
        if data.current_temp < 15:
            color_range = [[247, 251, 255], [222, 235, 247], [198, 219, 239], [158, 202, 225], [106, 81, 180], [75, 0, 130]]
        elif data.current_temp < 25:
            color_range = [[255, 255, 212], [254, 227, 145], [254, 196, 79], [254, 153, 41], [217, 95, 14], [153, 52, 4]]
        else:
            color_range = [[254, 235, 200], [253, 204, 138], [252, 141, 89], [227, 74, 51], [179, 0, 0]]

        layers.append(pdk.Layer(
            "HeatmapLayer", id="Thermal",
            data=data.df_thermal,
            opacity=0.8,
            get_position=["lon", "lat"],
            get_weight="weight",
            aggregation='"SUM"',
            color_range=color_range,
            intensity=1.0,
            radius_pixels=180,
            threshold=0.01,
        ))

    # ------------------------------------------------------------------
    # Urban drivers
    # ------------------------------------------------------------------
    if toggles.buildings and not data.df_buildings.empty:
        layers.append(pdk.Layer(
            "PolygonLayer", id="Buildings",
            data=data.df_buildings,
            opacity=0.8,
            stroked=False,
            get_polygon="polygon",
            filled=True,
            extruded=True,
            wireframe=True,
            get_elevation="height",
            get_fill_color="[255, 0, 85, 180]",
            get_line_color="[255, 255, 255]",
            pickable=True,
            auto_highlight=True,
        ))

    if toggles.traffic and not data.df_traffic.empty:
        layers.append(pdk.Layer(
            "PathLayer", id="Traffic",
            data=data.df_traffic,
            width_scale=5,
            width_min_pixels=2,
            get_path="path",
            get_color="[245, 158, 11, 255]",
            get_width=3,
            pickable=True,
            auto_highlight=True,
        ))

    # ------------------------------------------------------------------
    # Nature ID assets (scatterplots)
    # ------------------------------------------------------------------
    _scatter_layers = [
        ("trees",      data.df_trees,      "Trees",     "[5, 150, 105, 200]",  30),
        ("water",      data.df_water,      "Water",     "[14, 165, 233, 200]", 40),
        ("parks",      data.df_parks,      "Parks",     "[132, 204, 22, 200]", 60),
        ("shelters",   data.df_shelters,   "Shelters",  "[245, 158, 11, 200]", 80),
        ("fountains",  data.df_fountains,  "Fountains", "[56, 189, 248, 200]", 20),
        ("green_roofs",data.df_green_roofs,"GreenRoofs","[163, 230, 53, 200]", 30),
        ("gardens",    data.df_gardens,    "Gardens",   "[77, 124, 15, 200]",  50),
        ("forests",    data.df_forests,    "Forests",   "[21, 128, 61, 200]",  100),
        ("wetlands",   data.df_wetlands,   "Wetlands",  "[12, 74, 110, 200]",  150),
    ]
    _scatter_min_max = {
        "Trees": (3, 10), "Water": (4, 12), "Parks": (5, 15),
        "Shelters": (6, 18), "Fountains": (3, 8), "GreenRoofs": (4, 10),
        "Gardens": (5, 12), "Forests": (8, 30), "Wetlands": (10, 40),
    }
    for toggle_name, df, layer_id, color, radius in _scatter_layers:
        if getattr(toggles, toggle_name) and not df.empty:
            min_px, max_px = _scatter_min_max.get(layer_id, (4, 12))
            layers.append(pdk.Layer(
                "ScatterplotLayer", id=layer_id,
                data=df,
                get_position=["lon", "lat"],
                get_fill_color=color,
                get_radius=radius,
                pickable=True,
                auto_highlight=True,
                radius_min_pixels=min_px,
                radius_max_pixels=max_px,
            ))

    # ------------------------------------------------------------------
    # Physical sensors
    # ------------------------------------------------------------------
    if toggles.sensors and not data.df_sensors.empty:
        layers.append(pdk.Layer(
            "ScatterplotLayer", id="Sensors",
            data=data.df_sensors,
            get_position="[lon, lat]",
            get_fill_color="color",
            get_radius=150,
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=6,
            radius_max_pixels=12,
        ))

    # ------------------------------------------------------------------
    # Sandbox simulations overlay
    # ------------------------------------------------------------------
    if config.simulations:
        layers.append(pdk.Layer(
            "ScatterplotLayer", id="Simulations",
            data=config.simulations,
            get_position="[lon, lat]",
            get_fill_color="color",
            get_radius="radius",
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=15,
            radius_max_pixels=50,
        ))

    # ------------------------------------------------------------------
    # View state + base map
    # ------------------------------------------------------------------
    view_state = pdk.ViewState(
        latitude=config.center_lat,
        longitude=config.center_lon,
        zoom=13,
        pitch=45,
        bearing=0,
    )

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
            "boxShadow": "0 4px 6px -1px rgba(0, 0, 0, 0.5)",
        },
    }

    mapbox_api_key = None
    if "mapbox" in st.secrets:
        mapbox_api_key = st.secrets["mapbox"].get("access_token")

    if not mapbox_api_key:
        map_style = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
    else:
        map_style = "mapbox://styles/mapbox/light-v10"

    return pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style=map_style,
        api_keys={"mapbox": mapbox_api_key} if mapbox_api_key else None,
        tooltip=tooltip,
    )
