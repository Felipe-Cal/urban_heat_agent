
import sys
from unittest.mock import MagicMock
import pandas as pd
import pydeck as pdk
import pytest

# Mock streamlit BEFORE importing modules that use it
st_mock = MagicMock()
st_mock.secrets = {}
sys.modules["streamlit"] = st_mock

from modules.map_layers import create_map
from modules.models import CityData, LayerToggles, MapConfig

def _empty_city_data() -> CityData:
    """A CityData where all DataFrames are empty — safe to pass to create_map."""
    empty = pd.DataFrame()
    return CityData(
        df_thermal=pd.DataFrame(columns=["lon", "lat", "weight"]),
        df_trees=empty,
        df_water=empty,
        df_parks=empty,
        df_shelters=empty,
        df_fountains=empty,
        df_green_roofs=empty,
        df_gardens=empty,
        df_forests=empty,
        df_wetlands=empty,
        df_sensors=empty,
        df_ndvi=pd.DataFrame(columns=["lon", "lat", "weight"]),
        df_albedo=pd.DataFrame(columns=["lon", "lat", "weight"]),
        df_buildings=empty,
        df_traffic=empty,
        df_population=empty,
        resilience_score=50,
        current_temp=25.0,
        current_aqi=40,
    )

def test_map_style_dark_mode():
    config = MapConfig(
        data=_empty_city_data(),
        toggles=LayerToggles(),
        center_lat=34.05,
        center_lon=-118.24,
        light_mode=False
    )
    deck = create_map(config)
    # Since mapbox key is missing in mock secrets, it should use Carto Dark Matter
    assert deck.map_style == "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

def test_map_style_light_mode():
    config = MapConfig(
        data=_empty_city_data(),
        toggles=LayerToggles(),
        center_lat=34.05,
        center_lon=-118.24,
        light_mode=True
    )
    deck = create_map(config)
    # Since mapbox key is missing in mock secrets, it should use Carto Positron
    assert deck.map_style == "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"

def test_tooltip_style_dark_mode():
    config = MapConfig(
        data=_empty_city_data(),
        toggles=LayerToggles(),
        center_lat=34.05,
        center_lon=-118.24,
        light_mode=False
    )
    deck = create_map(config)
    # Check tooltip style
    assert deck._tooltip["style"]["backgroundColor"] == "rgba(15, 23, 42, 0.95)"
    assert deck._tooltip["style"]["color"] == "#e2e8f0"

def test_tooltip_style_light_mode():
    config = MapConfig(
        data=_empty_city_data(),
        toggles=LayerToggles(),
        center_lat=34.05,
        center_lon=-118.24,
        light_mode=True
    )
    deck = create_map(config)
    # Check tooltip style
    assert deck._tooltip["style"]["backgroundColor"] == "rgba(255, 255, 255, 0.95)"
    assert deck._tooltip["style"]["color"] == "#1e293b"
