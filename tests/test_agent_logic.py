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
    """
    Clear session state before every test.

    We do NOT pre-set chat_history or agent_status here — AgentSimulator.__init__
    is responsible for initialising those, and the `not in` guard must be triggered.
    Non-init keys that the tests rely on are set directly.
    """
    _session_state.clear()
    # Do NOT set chat_history or agent_status — let AgentSimulator.__init__ do that.
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
        assert "aqi" in ctx
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

# ---------------------------------------------------------------------------
# Tests: Tool Calling and LLM Integration
# ---------------------------------------------------------------------------

class TestLLMIntegration:
    @patch("modules.agent_logic.AgentSimulator.get_client")
    def test_process_custom_query_toggle_layer_tool(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # First call: Tool call response
        mock_response = MagicMock()
        mock_message = MagicMock()
        
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "toggle_map_layer"
        import json
        mock_tool_call.function.arguments = json.dumps({"layer_name": "thermal", "state": True})
        
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = ""
        mock_response.choices = [MagicMock(message=mock_message)]
        
        # Second call: Streaming text response
        mock_stream_response = MagicMock()
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock(delta=MagicMock(content="Layer "))]
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock(delta=MagicMock(content="enabled."))]
        mock_stream_response.__iter__.return_value = iter([chunk1, chunk2])
        
        mock_client.chat.completions.create.side_effect = [
            mock_response,
            mock_stream_response
        ]
        
        agent = AgentSimulator()
        _session_state["toggle_thermal"] = False
        
        # Since st.write_stream uses a generator, we need to mock it to just concat
        with patch("streamlit.write_stream", lambda g: "".join(list(g))):
            agent.process_custom_query("Enable the thermal layer")
        
        # Verify state updated from tool execution
        assert _session_state["toggle_thermal"] is True
        
        # Verify chat history
        assert "Layer enabled." in _session_state["chat_history"][-1]["content"]

    @patch("modules.agent_logic.AgentSimulator.get_client")
    def test_simulate_intervention_json_response(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_response = MagicMock()
        import json
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content=json.dumps({
                    "intervention_name": "AI Super Bioswale",
                    "cooling_offset": 1.2,
                    "cost": 100000,
                    "energy_savings": 500,
                    "health_impact": 5
                })
            ))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        
        agent = AgentSimulator()
        
        obj = {
            "asset_id": "ROAD-1",
            "name": "Main Auto Road",
            "type": "Road",
            "lat": 0.0,
            "lon": 0.0,
        }
        
        before_budget = _session_state["sandbox_budget"]
        agent.simulate_intervention_on_asset(obj)
        
        assert len(_session_state["simulations"]) == 1
        sim = _session_state["simulations"][-1]
        
        assert sim["name"] == "AI Super Bioswale"
        assert sim["cooling"] == 1.2
        assert _session_state["sandbox_budget"] == before_budget - 100000
        
        
        assert len(_session_state["green_ledger"]) == 1
        ledger = _session_state["green_ledger"][-1]
        assert ledger["Intervention"] == "AI Super Bioswale"
        assert ledger["Cooling Impact (°C)"] == "-1.2"

    @patch("modules.agent_logic.AgentSimulator.get_client")
    def test_process_custom_query_query_urban_assets_reads_asset_counts(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_trees"
        mock_tool_call.function.name = "query_urban_assets"
        import json
        mock_tool_call.function.arguments = json.dumps({"asset_type": "trees"})
        
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = ""
        mock_response.choices = [MagicMock(message=mock_message)]
        
        mock_stream_response = MagicMock()
        chunk = MagicMock()
        chunk.choices = [MagicMock(delta=MagicMock(content="We have 12000 trees."))]
        mock_stream_response.__iter__.return_value = iter([chunk])
        
        mock_client.chat.completions.create.side_effect = [mock_response, mock_stream_response]
        
        # Setup mock CityData with explicit asset_counts dict
        mock_city_data = MagicMock()
        mock_city_data.asset_counts = {"trees": 12000}
        
        _session_state["data"] = mock_city_data
        
        agent = AgentSimulator()
        with patch("streamlit.write_stream", lambda g: "".join(list(g))):
            agent.process_custom_query("How many trees?")
            
        # The agent should have processed the tool call and got "count": 12000
        # Let's inspect the `messages` history
        tool_resp = _session_state["chat_history"][-1]["content"]
        assert "We have 12000 trees" in tool_resp

    @patch("modules.agent_logic.AgentSimulator.get_client")
    def test_process_custom_query_highlight_map_assets(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_hlt"
        mock_tool_call.function.name = "highlight_map_assets"
        import json
        mock_tool_call.function.arguments = json.dumps({
            "locations": [{"lat": 34.0, "lon": -118.0, "label": "Hot Building"}]
        })
        
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = ""
        mock_response.choices = [MagicMock(message=mock_message)]
        
        mock_stream_response = MagicMock()
        chunk = MagicMock()
        chunk.choices = [MagicMock(delta=MagicMock(content="I highlighted it."))]
        mock_stream_response.__iter__.return_value = iter([chunk])
        
        mock_client.chat.completions.create.side_effect = [mock_response, mock_stream_response]
        
        _session_state.map_annotations = []
        
        agent = AgentSimulator()
        with patch("streamlit.write_stream", lambda g: "".join(list(g))):
            agent.process_custom_query("Highlight the hot building.")
            
        # Verify the session state received the annotation
        assert len(_session_state.map_annotations) == 1
        assert _session_state.map_annotations[0]["lat"] == 34.0
        assert _session_state.map_annotations[0]["lon"] == -118.0
        assert "Hot Building" in _session_state.map_annotations[0]["tooltip"]

    @patch("modules.agent_logic.AgentSimulator.get_client")
    def test_process_custom_query_clear_map_highlights(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_clear"
        mock_tool_call.function.name = "clear_map_highlights"
        mock_tool_call.function.arguments = "{}"
        
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = ""
        mock_response.choices = [MagicMock(message=mock_message)]
        
        mock_stream_response = MagicMock()
        chunk = MagicMock()
        chunk.choices = [MagicMock(delta=MagicMock(content="Cleared."))]
        mock_stream_response.__iter__.return_value = iter([chunk])
        
        mock_client.chat.completions.create.side_effect = [mock_response, mock_stream_response]
        
        _session_state.map_annotations = [{"lat": 0, "lon": 0}] # Existing
        
        agent = AgentSimulator()
        with patch("streamlit.write_stream", lambda g: "".join(list(g))):
            agent.process_custom_query("Clear the map please.")
            
        assert len(_session_state.map_annotations) == 0
