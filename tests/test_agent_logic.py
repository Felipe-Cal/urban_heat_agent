"""
Tests for modules/agent_logic.py

Streamlit's session_state is mocked via a simple dict-backed object so tests
run outside the Streamlit runtime.
"""
import sys
import types
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ---------------------------------------------------------------------------
# Mock streamlit before importing agent_logic
# ---------------------------------------------------------------------------

class _FakeSessionState(dict):
    """Dict that also supports attribute-style access, like st.session_state."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def get(self, key, default=None):
        return super().get(key, default)


_session_state = _FakeSessionState()

st_mock = MagicMock()
st_mock.session_state = _session_state
st_mock.secrets = {}

sys.modules.setdefault("streamlit", st_mock)

from modules.agent_logic import AgentSimulator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_session_state():
    """Clear and reinitialise session state before every test."""
    _session_state.clear()
    _session_state["chat_history"] = []
    _session_state["agent_status"] = "IDLE"
    _session_state["selected_city_name"] = "Los Angeles, USA"
    _session_state["simulations"] = []
    _session_state["simulated_cooling"] = 0.0
    _session_state["sandbox_budget"] = 5_000_000.0
    _session_state["green_ledger"] = []
    yield


# ---------------------------------------------------------------------------
# Tests: AgentSimulator.__init__
# ---------------------------------------------------------------------------

class TestAgentSimulatorInit:
    def test_chat_history_initialised(self):
        agent = AgentSimulator()
        assert "chat_history" in _session_state
        assert len(_session_state["chat_history"]) >= 1

    def test_initial_message_is_from_assistant(self):
        agent = AgentSimulator()
        assert _session_state["chat_history"][0]["role"] == "assistant"

    def test_agent_status_initialised(self):
        agent = AgentSimulator()
        assert "agent_status" in _session_state


# ---------------------------------------------------------------------------
# Tests: add_message
# ---------------------------------------------------------------------------

class TestAddMessage:
    def test_adds_user_message(self):
        agent = AgentSimulator()
        before = len(_session_state["chat_history"])
        agent.add_message("user", "Hello")
        assert len(_session_state["chat_history"]) == before + 1
        assert _session_state["chat_history"][-1] == {"role": "user", "content": "Hello"}

    def test_adds_assistant_message(self):
        agent = AgentSimulator()
        agent.add_message("assistant", "Hi there")
        assert _session_state["chat_history"][-1]["role"] == "assistant"

    def test_multiple_messages_appended_in_order(self):
        agent = AgentSimulator()
        agent.add_message("user", "first")
        agent.add_message("assistant", "second")
        roles = [m["role"] for m in _session_state["chat_history"]]
        assert roles[-2] == "user"
        assert roles[-1] == "assistant"


# ---------------------------------------------------------------------------
# Tests: _build_context
# ---------------------------------------------------------------------------

class TestBuildContext:
    def test_returns_dict_with_required_keys(self):
        agent = AgentSimulator()
        ctx = agent._build_context()
        assert "city" in ctx
        assert "temp" in ctx
        assert "resilience" in ctx
        assert "active_layers" in ctx

    def test_city_matches_session_state(self):
        _session_state["selected_city_name"] = "Tokyo, Japan"
        agent = AgentSimulator()
        ctx = agent._build_context()
        assert ctx["city"] == "Tokyo, Japan"

    def test_active_layers_empty_when_none_toggled(self):
        agent = AgentSimulator()
        ctx = agent._build_context()
        assert ctx["active_layers"] == "None"

    def test_active_layers_lists_enabled_layers(self):
        _session_state["toggle_thermal"] = True
        _session_state["toggle_trees"] = True
        agent = AgentSimulator()
        ctx = agent._build_context()
        assert "thermal" in ctx["active_layers"]
        assert "trees" in ctx["active_layers"]


# ---------------------------------------------------------------------------
# Tests: simulate_deployment
# ---------------------------------------------------------------------------

class TestSimulateDeployment:
    def test_adds_two_messages(self):
        agent = AgentSimulator()
        before = len(_session_state["chat_history"])
        agent.simulate_deployment()
        assert len(_session_state["chat_history"]) == before + 2

    def test_status_resets_to_idle(self):
        agent = AgentSimulator()
        agent.simulate_deployment()
        assert _session_state["agent_status"] == "IDLE"


# ---------------------------------------------------------------------------
# Tests: simulate_intervention
# ---------------------------------------------------------------------------

class TestSimulateIntervention:
    def test_adds_two_messages(self):
        agent = AgentSimulator()
        before = len(_session_state["chat_history"])
        agent.simulate_intervention()
        assert len(_session_state["chat_history"]) == before + 2

    def test_status_resets_to_idle(self):
        agent = AgentSimulator()
        agent.simulate_intervention()
        assert _session_state["agent_status"] == "IDLE"


# ---------------------------------------------------------------------------
# Tests: simulate_intervention_on_asset
# ---------------------------------------------------------------------------

class TestSimulateInterventionOnAsset:
    def _make_building_obj(self):
        return {
            "asset_id": "BLDG-999",
            "name": "City Hall",
            "type": "Concrete Mass",
            "lat": 34.05,
            "lon": -118.24,
        }

    def test_adds_simulations_entry(self):
        agent = AgentSimulator()
        agent.simulate_intervention_on_asset(self._make_building_obj())
        assert len(_session_state["simulations"]) == 1

    def test_green_ledger_entry_added(self):
        agent = AgentSimulator()
        agent.simulate_intervention_on_asset(self._make_building_obj())
        assert len(_session_state["green_ledger"]) == 1

    def test_ledger_entry_has_required_keys(self):
        agent = AgentSimulator()
        agent.simulate_intervention_on_asset(self._make_building_obj())
        entry = _session_state["green_ledger"][0]
        for key in ["Timestamp", "Nature ID", "Target Asset", "Intervention",
                    "Cooling Impact (°C)", "Status"]:
            assert key in entry, f"Missing ledger key: {key}"

    def test_simulated_cooling_increases(self):
        agent = AgentSimulator()
        before = _session_state["simulated_cooling"]
        agent.simulate_intervention_on_asset(self._make_building_obj())
        assert _session_state["simulated_cooling"] > before

    def test_budget_decreases(self):
        agent = AgentSimulator()
        before = _session_state["sandbox_budget"]
        agent.simulate_intervention_on_asset(self._make_building_obj())
        assert _session_state["sandbox_budget"] < before

    def test_road_intervention_has_higher_cooling_than_generic(self):
        agent = AgentSimulator()
        road_obj = {
            "asset_id": "TRAFFIC-1",
            "name": "Main Street",
            "type": "Motorway",
            "lat": 34.05,
            "lon": -118.24,
        }
        agent.simulate_intervention_on_asset(road_obj)
        # Road (Bioswale) gives 0.7°C, generic gives 0.2°C
        assert _session_state["simulated_cooling"] >= 0.7

    def test_status_resets_to_idle(self):
        agent = AgentSimulator()
        agent.simulate_intervention_on_asset(self._make_building_obj())
        assert _session_state["agent_status"] == "IDLE"


# ---------------------------------------------------------------------------
# Tests: simulate_verification
# ---------------------------------------------------------------------------

class TestSimulateVerification:
    def test_adds_two_messages(self):
        agent = AgentSimulator()
        before = len(_session_state["chat_history"])
        agent.simulate_verification()
        assert len(_session_state["chat_history"]) == before + 2

    def test_response_contains_no_placeholder(self):
        agent = AgentSimulator()
        agent.simulate_verification()
        last_msg = _session_state["chat_history"][-1]["content"]
        assert "HASH_VALUE_PLACEHOLDER" not in last_msg


# ---------------------------------------------------------------------------
# Tests: auto_analyze_region
# ---------------------------------------------------------------------------

class TestAutoAnalyzeRegion:
    def test_adds_two_messages(self):
        agent = AgentSimulator()
        before = len(_session_state["chat_history"])
        agent.auto_analyze_region()
        assert len(_session_state["chat_history"]) == before + 2

    def test_response_mentions_city(self):
        _session_state["selected_city_name"] = "Mumbai, India"
        agent = AgentSimulator()
        agent.auto_analyze_region()
        last = _session_state["chat_history"][-1]["content"]
        assert "Mumbai" in last
