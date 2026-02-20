import streamlit as st
from typing import Any, Dict, List, Optional
import copy
from dataclasses import asdict
from modules.models import LayerToggles

class StateManager:
    """
    Manages the Streamlit session state to ensure consistency and type safety.
    Centralizes state initialization and updates.
    """

    # Core application state defaults
    _DEFAULTS = {
        "selected_city_name": "Los Angeles, USA",
        "time_of_day":        "14:00",
        "pending_map_click":  None,
        "last_clicked_asset": None,
        "last_clicked_obj":   None,
        "sandbox_mode":       False,
        "simulations":        [],
        "simulated_cooling":  0.0,
        "sandbox_budget":     5_000_000.0,
        "green_ledger":       [],
        "generating_pdf":     False,
        "chat_history":       [{"role": "assistant", "content": "Initializing Gaia Node... ready for queries."}],
        "agent_status":       "IDLE",
        "light_mode":         False,
    }

    # Layer toggle defaults
    _LAYER_KEYS = [
        "thermal", "trees", "water", "parks", "shelters", "fountains",
        "green_roofs", "gardens", "forests", "wetlands", "sensors",
        "ndvi", "albedo", "buildings", "traffic", "population",
    ]

    @classmethod
    def initialize(cls):
        """Initialize session state with default values if they don't exist."""
        # Initialize core defaults
        for key, default in cls._DEFAULTS.items():
            if key not in st.session_state:
                # Use deepcopy to ensure each session gets its own independent mutable objects
                st.session_state[key] = copy.deepcopy(default)

        # Initialize layer toggles
        for layer in cls._LAYER_KEYS:
            key = f"toggle_{layer}"
            if key not in st.session_state:
                st.session_state[key] = False

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Safely get a value from session state."""
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value: Any):
        """Set a value in session state."""
        st.session_state[key] = value

    @staticmethod
    def update(updates: Dict[str, Any]):
        """Update multiple values in session state at once."""
        for key, value in updates.items():
            st.session_state[key] = value

    @staticmethod
    def get_layer_toggles() -> LayerToggles:
        """Retrieve current layer toggles as a typed object."""
        return LayerToggles.from_session_state(st.session_state)

    @staticmethod
    def reset_sandbox():
        """Reset all sandbox-related state."""
        cls.update({
            "sandbox_mode": False,
            "simulations": [],
            "green_ledger": [],
            "simulated_cooling": 0.0,
            "sandbox_budget": 5_000_000.0,
        })
