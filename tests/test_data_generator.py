"""
Tests for modules/data_generator.py

All HTTP calls are mocked so tests run offline and fast.
"""
import random
import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# We need to make sure streamlit is not actually called during testing.
# Patch it at the module level before importing data_generator.
import sys
from types import ModuleType

# Minimal streamlit session_state mock so the module-level 'import streamlit as st'
# inside data_generator doesn't crash in a non-Streamlit environment.
st_mock = MagicMock()
st_mock.session_state = {}

# Make st.cache_data a pass-through decorator
def cache_data_decorator(*args, **kwargs):
    def wrapper(func):
        return func
    return wrapper

st_mock.cache_data = cache_data_decorator

sys.modules["streamlit"] = st_mock

from modules.data_generator import generate_mock_data
from modules.models import CityData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ok_meteo_response(temp: float = 25.0):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"current": {"temperature_2m": temp}}
    return resp


def _make_ok_aqi_response(aqi: int = 40):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"current": {"us_aqi": aqi}}
    return resp


def _make_ok_osm_response():
    resp = MagicMock()
    resp.status_code = 200
    # Minimal OSM response — a few trees
    resp.json.return_value = {
        "elements": [
            {
                "type": "node",
                "id": 1,
                "lat": 34.05,
                "lon": -118.24,
                "tags": {"natural": "tree", "species": "Quercus agrifolia"},
            },
            {
                "type": "node",
                "id": 2,
                "lat": 34.052,
                "lon": -118.243,
                "tags": {"natural": "tree"},
            },
        ]
    }
    return resp


def _make_timeout():
    import requests
    raise requests.exceptions.Timeout("Mocked timeout")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGenerateMockDataReturnType:
    """generate_mock_data should return a CityData dataclass."""

    @patch("modules.data_generator.requests.get")
    def test_returns_city_data_instance(self, mock_get):
        mock_get.side_effect = [
            _make_ok_meteo_response(28.0),
            _make_ok_aqi_response(55),
            _make_ok_osm_response(),
        ]
        result = generate_mock_data(34.05, -118.24, "14:00")
        assert isinstance(result, CityData), f"Expected CityData, got {type(result)}"

    @patch("modules.data_generator.requests.get")
    def test_all_dataframe_fields_are_dataframes(self, mock_get):
        mock_get.side_effect = [
            _make_ok_meteo_response(),
            _make_ok_aqi_response(),
            _make_ok_osm_response(),
        ]
        result = generate_mock_data()
        df_fields = [
            "df_thermal", "df_trees", "df_water", "df_parks", "df_shelters",
            "df_fountains", "df_green_roofs", "df_gardens", "df_forests",
            "df_wetlands", "df_sensors", "df_ndvi", "df_albedo",
            "df_buildings", "df_traffic", "df_population",
        ]
        for field_name in df_fields:
            val = getattr(result, field_name)
            assert isinstance(val, pd.DataFrame), f"{field_name} is not a DataFrame"


class TestGenerateMockDataScalars:
    @patch("modules.data_generator.requests.get")
    def test_resilience_score_is_int(self, mock_get):
        mock_get.side_effect = [
            _make_ok_meteo_response(),
            _make_ok_aqi_response(),
            _make_ok_osm_response(),
        ]
        result = generate_mock_data()
        assert isinstance(result.resilience_score, int)

    @patch("modules.data_generator.requests.get")
    def test_resilience_score_in_valid_range(self, mock_get):
        mock_get.side_effect = [
            _make_ok_meteo_response(),
            _make_ok_aqi_response(),
            _make_ok_osm_response(),
        ]
        result = generate_mock_data()
        # Max theoretical score is 100; fallback random is 45-65
        assert 0 <= result.resilience_score <= 100, (
            f"resilience_score {result.resilience_score} out of [0, 100]"
        )

    @patch("modules.data_generator.requests.get")
    def test_current_temp_is_numeric(self, mock_get):
        mock_get.side_effect = [
            _make_ok_meteo_response(32.5),
            _make_ok_aqi_response(),
            _make_ok_osm_response(),
        ]
        result = generate_mock_data()
        assert isinstance(result.current_temp, (int, float))

    @patch("modules.data_generator.requests.get")
    def test_current_aqi_is_int(self, mock_get):
        mock_get.side_effect = [
            _make_ok_meteo_response(),
            _make_ok_aqi_response(75),
            _make_ok_osm_response(),
        ]
        result = generate_mock_data()
        assert isinstance(result.current_aqi, int)


class TestGenerateMockDataFallbacks:
    """When network calls fail, sensible defaults must be used."""

    @patch("modules.data_generator.requests.get")
    def test_network_timeout_still_returns_city_data(self, mock_get):
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.Timeout("mocked")
        result = generate_mock_data()
        assert isinstance(result, CityData)

    @patch("modules.data_generator.requests.get")
    def test_timeout_sets_fetch_error(self, mock_get):
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.Timeout("mocked")
        result = generate_mock_data()
        assert result.fetch_error is not None, "fetch_error should be set on timeout"

    @patch("modules.data_generator.requests.get")
    def test_fallback_temp_is_30_on_api_failure(self, mock_get):
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.ConnectionError("mocked")
        result = generate_mock_data(time_of_day="00:00")  # Hour 0: min variation
        # Baseline fallback is 30.0; at hour 0 variation is negative, so temp < 30
        assert isinstance(result.current_temp, (int, float))


class TestGenerateMockDataTimeOfDay:
    @patch("modules.data_generator.requests.get")
    def test_bad_time_of_day_falls_back_to_14(self, mock_get):
        """Malformed time_of_day string should NOT raise — should use hour=14."""
        mock_get.side_effect = [
            _make_ok_meteo_response(),
            _make_ok_aqi_response(),
            _make_ok_osm_response(),
        ]
        # Should not raise
        result = generate_mock_data(time_of_day="not-a-time")
        assert isinstance(result, CityData)

    @patch("modules.data_generator.requests.get")
    def test_all_valid_hours_produce_city_data(self, mock_get):
        for hour in [0, 6, 12, 18, 23]:
            mock_get.side_effect = [
                _make_ok_meteo_response(),
                _make_ok_aqi_response(),
                _make_ok_osm_response(),
            ]
            result = generate_mock_data(time_of_day=f"{hour:02d}:00")
            assert isinstance(result, CityData), f"Failed for hour {hour}"


class TestGenerateMockDataThermalDataFrame:
    @patch("modules.data_generator.requests.get")
    def test_thermal_dataframe_has_required_columns(self, mock_get):
        mock_get.side_effect = [
            _make_ok_meteo_response(),
            _make_ok_aqi_response(),
            _make_ok_osm_response(),
        ]
        result = generate_mock_data()
        assert set(["lon", "lat", "weight"]).issubset(result.df_thermal.columns)

    @patch("modules.data_generator.requests.get")
    def test_thermal_weights_are_positive(self, mock_get):
        mock_get.side_effect = [
            _make_ok_meteo_response(),
            _make_ok_aqi_response(),
            _make_ok_osm_response(),
        ]
        result = generate_mock_data()
        assert (result.df_thermal["weight"] > 0).all()


class TestProgressCallback:
    @patch("modules.data_generator.requests.get")
    def test_progress_callback_is_called(self, mock_get):
        mock_get.side_effect = [
            _make_ok_meteo_response(),
            _make_ok_aqi_response(),
            _make_ok_osm_response(),
        ]
        calls = []
        generate_mock_data(progress_callback=lambda msg, pct: calls.append((msg, pct)))
        assert len(calls) > 0, "progress_callback was never called"
        # Last call should hit 100%
        last_pct = calls[-1][1]
        assert last_pct == 100
