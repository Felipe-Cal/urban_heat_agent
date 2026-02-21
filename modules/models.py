"""
Shared data models for the Gaia Heat Sync application.

Using dataclasses instead of bare tuples or long argument lists makes the code
self-documenting, type-safe, and much easier to test and extend.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class CityData:
    """All data produced by generate_mock_data for a single city/time snapshot."""

    df_thermal: pd.DataFrame
    df_trees: pd.DataFrame
    df_water: pd.DataFrame
    df_parks: pd.DataFrame
    df_shelters: pd.DataFrame
    df_fountains: pd.DataFrame
    df_green_roofs: pd.DataFrame
    df_gardens: pd.DataFrame
    df_forests: pd.DataFrame
    df_wetlands: pd.DataFrame
    df_sensors: pd.DataFrame
    df_ndvi: pd.DataFrame
    df_albedo: pd.DataFrame
    df_buildings: pd.DataFrame
    df_traffic: pd.DataFrame
    df_population: pd.DataFrame
    resilience_score: int
    current_temp: float
    current_aqi: int
    # Optional: surface-level error message from data fetching (e.g. OSM timeout)
    fetch_error: str | None = None


@dataclass
class LayerToggles:
    """Boolean toggles for each map layer, mirroring st.session_state toggle_* keys."""

    thermal: bool = False
    trees: bool = False
    water: bool = False
    parks: bool = False
    shelters: bool = False
    fountains: bool = False
    green_roofs: bool = False
    gardens: bool = False
    forests: bool = False
    wetlands: bool = False
    sensors: bool = False
    ndvi: bool = False
    albedo: bool = False
    buildings: bool = False
    traffic: bool = False
    population: bool = False

    @classmethod
    def from_session_state(cls, state: dict) -> "LayerToggles":
        """Build from a dict-like Streamlit session_state object."""
        return cls(
            thermal=state.get("toggle_thermal", False),
            trees=state.get("toggle_trees", False),
            water=state.get("toggle_water", False),
            parks=state.get("toggle_parks", False),
            shelters=state.get("toggle_shelters", False),
            fountains=state.get("toggle_fountains", False),
            green_roofs=state.get("toggle_green_roofs", False),
            gardens=state.get("toggle_gardens", False),
            forests=state.get("toggle_forests", False),
            wetlands=state.get("toggle_wetlands", False),
            sensors=state.get("toggle_sensors", False),
            ndvi=state.get("toggle_ndvi", False),
            albedo=state.get("toggle_albedo", False),
            buildings=state.get("toggle_buildings", False),
            traffic=state.get("toggle_traffic", False),
            population=state.get("toggle_population", False),
        )


@dataclass
class MapConfig:
    """Everything create_map needs, bundled into a single object."""

    data: CityData
    toggles: LayerToggles
    center_lat: float = 34.0522
    center_lon: float = -118.2437
    simulations: list = field(default_factory=list)
    light_mode: bool = False
