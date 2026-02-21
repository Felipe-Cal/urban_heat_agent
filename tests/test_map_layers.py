"""
Tests for modules/map_layers.py

Verifies that create_map returns a valid pdk.Deck object and that layer
presence correctly reflects the toggle state in MapConfig.
"""
import sys
from unittest.mock import MagicMock

import pandas as pd
import pydeck as pdk
import pytest

# Mock streamlit before importing map_layers
st_mock = MagicMock()
st_mock.session_state = {}
sys.modules.setdefault("streamlit", st_mock)

from modules.map_layers import create_map
from modules.models import CityData, LayerToggles, MapConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_city_data() -> CityData:
    """A CityData where all DataFrames are empty — safe to pass to create_map."""
    empty = pd.DataFrame()
    return CityData(
        df_thermal=pd.DataFrame(columns=["lon", "lat", "weight"]),
        df_thermal_points=pd.DataFrame(columns=["lon", "lat", "temp", "tooltip"]),
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
        df_buildings=empty,
        df_traffic=empty,
        current_temp=25.0,
        current_aqi=40,
    )


def _config_all_off(**overrides) -> MapConfig:
    toggles = LayerToggles(**overrides)
    return MapConfig(
        data=_empty_city_data(),
        toggles=toggles,
        center_lat=34.0522,
        center_lon=-118.2437,
    )


def _small_df(n: int = 3) -> pd.DataFrame:
    """Tiny lon/lat DataFrame for layer-presence tests."""
    return pd.DataFrame({
        "lon": [-118.24] * n,
        "lat": [34.05] * n,
        "asset_id": [f"ID-{i}" for i in range(n)],
        "name": ["Test"] * n,
        "type": ["Type"] * n,
        "color": [[0, 200, 100, 200]] * n,
        "tooltip": ["<b>Test</b>"] * n,
    })


def _weight_df(n: int = 5) -> pd.DataFrame:
    return pd.DataFrame({
        "lon": [-118.24] * n,
        "lat": [34.05] * n,
        "weight": [0.5] * n,
    })


# ---------------------------------------------------------------------------
# Tests: return type
# ---------------------------------------------------------------------------

class TestCreateMapReturnsValidDeck:
    def test_returns_pydeck_deck_instance(self):
        config = _config_all_off()
        result = create_map(config)
        assert isinstance(result, pdk.Deck)

    def test_all_toggles_off_no_layers(self):
        config = _config_all_off()
        result = create_map(config)
        assert result.layers == []

    def test_view_state_uses_provided_coordinates(self):
        config = MapConfig(
            data=_empty_city_data(),
            toggles=LayerToggles(),
            center_lat=51.5074,
            center_lon=-0.1278,
        )
        result = create_map(config)
        assert result.initial_view_state.latitude == 51.5074
        assert result.initial_view_state.longitude == -0.1278


# ---------------------------------------------------------------------------
# Tests: individual layer toggles
# ---------------------------------------------------------------------------

class TestLayerPresence:
    def _layer_ids(self, deck: pdk.Deck) -> list[str]:
        return [layer.id for layer in deck.layers]

    def test_thermal_layer_added_when_toggled(self):
        data = _empty_city_data()
        data.df_thermal = _weight_df()
        config = MapConfig(data=data, toggles=LayerToggles(thermal=True))
        result = create_map(config)
        assert "Thermal" in self._layer_ids(result)

    def test_no_thermal_layer_when_toggle_off(self):
        data = _empty_city_data()
        data.df_thermal = _weight_df()
        config = MapConfig(data=data, toggles=LayerToggles(thermal=False))
        result = create_map(config)
        assert "Thermal" not in self._layer_ids(result)

    def test_trees_layer_added_when_toggled(self):
        data = _empty_city_data()
        data.df_trees = _small_df()
        config = MapConfig(data=data, toggles=LayerToggles(trees=True))
        result = create_map(config)
        assert "Trees" in self._layer_ids(result)

    def test_sensors_layer_added_when_toggled(self):
        data = _empty_city_data()
        data.df_sensors = _small_df()
        config = MapConfig(data=data, toggles=LayerToggles(sensors=True))
        result = create_map(config)
        assert "Sensors" in self._layer_ids(result)

    def test_multiple_layers_toggled_simultaneously(self):
        data = _empty_city_data()
        data.df_thermal = _weight_df()
        data.df_trees = _small_df()
        data.df_sensors = _small_df()
        config = MapConfig(
            data=data,
            toggles=LayerToggles(thermal=True, trees=True, sensors=True),
        )
        result = create_map(config)
        ids = self._layer_ids(result)
        assert "Thermal" in ids
        assert "Trees" in ids
        assert "Sensors" in ids

    def test_empty_dataframe_prevents_layer_from_being_added(self):
        """Even if toggle is True, an empty DF should not add the layer (avoids pydeck errors)."""
        config = _config_all_off(trees=True)  # df_trees is empty
        result = create_map(config)
        assert "Trees" not in self._layer_ids(result)


# ---------------------------------------------------------------------------
# Tests: sandbox simulations layer
# ---------------------------------------------------------------------------

class TestSimulationsLayer:
    def test_simulation_layer_added_when_simulations_present(self):
        config = _config_all_off()
        config.simulations = [
            {
                "lat": 34.05,
                "lon": -118.24,
                "name": "Green Roof",
                "color": [0, 255, 128, 200],
                "radius": 250,
                "tooltip": "<b>Test</b>",
            }
        ]
        result = create_map(config)
        ids = [layer.id for layer in result.layers]
        assert "Simulations" in ids

    def test_no_simulation_layer_when_list_empty(self):
        config = _config_all_off()
        config.simulations = []
        result = create_map(config)
        ids = [layer.id for layer in result.layers]
        assert "Simulations" not in ids
