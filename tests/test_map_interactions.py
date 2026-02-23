import pytest
from streamlit.testing.v1 import AppTest

def test_map_interaction_triggers_agent():
    """
    Simulate a user clicking an asset on the map and verify the AI agent 
    processes the click instead of dropping it.
    """
    # Initialize AppTest
    at = AppTest.from_file("app.py", default_timeout=30)
    
    # Run the app initially to load everything
    at.run()
    
    # 1. Simulate authentication so the main dashboard loads
    # Instead of interacting with the UI, we can just inject the session state directly
    class MockUser:
        def __init__(self, email, id):
            self.email = email
            self.id = id
            
    at.session_state["user_session"] = MockUser("test@gaiapattern.com", "123")
    at.run()
    
    # Verify we are on the main dashboard (e.g. agent chat is rendered)
    assert not at.error, f"App threw an error: {at.error}"
    
    # 2. Simulate Map Click Injection
    # When PyDeck selection triggers, it sets these session state variables in app.py
    mock_asset = {
        "id": "tree_123",
        "name": "Pine Tree",
        "type": "Tree Canopy",
        "lat": 34.05,
        "lon": -118.24
    }
    
    # We must explicitly set user_session again because Streamlit might reset it on run
    at.session_state["user_session"] = MockUser("test@gaiapattern.com", "123")
    
    at.session_state["last_clicked_obj_id"] = "tree_123"
    at.session_state["last_clicked_obj"] = mock_asset
    at.session_state["pending_map_click"] = "Selected Pine Tree (tree_123)"
    
    # Run the application (this mimics Pydeck event firing)
    at.run()
    
    # 4. Assertions
    # A. The pending_map_click should be cleared after parsing
    assert at.session_state["pending_map_click"] is None, "pending_map_click was not cleared"
    
    # B. The agent chat history should have recorded the intersection event
    # Instead of dictionary inspection, use Streamlit AppTest's native chat element query
    chat_messages = [msg.markdown[0].value for msg in at.chat_message if msg.markdown]
    
    event_logged = False
    for content in chat_messages:
        if "Pine Tree" in content:
            event_logged = True
            break
            
    assert event_logged, "Map click event was not rendered in the chat UI."
    
    # C. Verify the agent responded with analysis for the nature asset (mocked or real)
    assistant_replied = False
    for content in chat_messages:
        # The new dynamic logic (and its fallback) always prints a header like:
        # Profiling Pine Tree (Tree Canopy)
        if "Profiling Pine Tree" in content or "Tree Canopy" in content:
            assistant_replied = True
            break
            
    assert assistant_replied, "Agent did not output the expected analysis template for a nature asset."

def test_layer_toggles_preserved_on_map_click():
    """
    Simulate a user enabling layers, then clicking the map. Ensure the toggle widgets 
    maintain their True state after the agent finishes.
    """
    at = AppTest.from_file("app.py", default_timeout=30)
    
    class MockUser:
        def __init__(self, email, id):
            self.email = email
            self.id = id
            
    at.session_state["user_session"] = MockUser("test@gaiapattern.com", "123")
    at.run()
    
    # 1. User toggles on "Trees" and "Water" manually
    at.session_state["toggle_trees"] = True
    at.session_state["toggle_water"] = True
    at.run()
    
    # Verify toggles stick initially
    assert at.session_state["toggle_trees"] is True, "Trees toggle failed to set."
    assert at.session_state["toggle_water"] is True, "Water toggle failed to set."
    
    # 2. User clicks on the map while layers are ON
    mock_asset = {
        "id": "tree_456",
        "name": "Pine Tree",
        "type": "Tree Canopy",
        "lat": 34.05,
        "lon": -118.24
    }
    at.session_state["last_clicked_obj_id"] = "tree_456"
    at.session_state["last_clicked_obj"] = mock_asset
    at.session_state["pending_map_click"] = "Selected Pine Tree (tree_456)"
    
    # Run the application (this mimics Pydeck event firing)
    at.run()
    
    # 3. Verify toggles did NOT reset to False after the Click Interaction
    assert at.session_state["toggle_trees"] is True, "Trees toggle was wiped out by the map click loop!"
    assert at.session_state["toggle_water"] is True, "Water toggle was wiped out by the map click loop!"

def test_slider_state_preserves_toggles():
    """
    Simulate a user enabling layers, then adjusting the Temporal Heat Slider. 
    Ensure the toggles maintain their True state because of the on_change callback refactor.
    """
    at = AppTest.from_file("app.py", default_timeout=30)
    
    class MockUser:
        def __init__(self, email, id):
            self.email = email
            self.id = id
            
    at.session_state["user_session"] = MockUser("test@gaiapattern.com", "123")
    at.run()
    
    # 1. User toggles on "Trees" and "Water" manually
    at.session_state["toggle_trees"] = True
    at.session_state["toggle_water"] = True
    at.run()
    
    assert at.session_state["toggle_trees"] is True
    
    # 2. User moves the Time Slider
    from datetime import time as dtime
    
    # Set the key directly or use the widget property
    at.slider(key="time_slider").set_value(dtime(15, 30))
    at.run()
    
    # 3. Verify toggles did NOT reset to False after the Slider Interaction
    assert at.session_state["toggle_trees"] is True, "Trees toggle was wiped out by the Slider!"
    assert at.session_state["toggle_water"] is True, "Water toggle was wiped out by the Slider!"

def test_agent_response_formatting_is_markdown():
    """
    Ensure the agent's responses use Markdown blockquotes and do NOT contain 
    raw HTML <div> tags which break Streamlit's write_stream UI rendering.
    """
    at = AppTest.from_file("app.py", default_timeout=30)
    
    class MockUser:
        def __init__(self, email, id):
            self.email = email
            self.id = id
            
    at.session_state["user_session"] = MockUser("test@gaiapattern.com", "123")
    
    mock_asset = {
        "id": "tree_789",
        "name": "Oak Tree",
        "type": "Tree Canopy",
        "lat": 34.05,
        "lon": -118.24
    }
    at.session_state["last_clicked_obj_id"] = "tree_789"
    at.session_state["last_clicked_obj"] = mock_asset
    at.session_state["pending_map_click"] = "Selected Oak Tree (tree_789)"
    
    at.run()
    
    chat_messages = [msg.markdown[0].value for msg in at.chat_message if msg.markdown]
    
    for content in chat_messages:
        # The assistant messages should not have <div>
        # We explicitly check the mock fallback or streamed text depending on API key state
        if "Profiling" in content:
            assert "<div" not in content.lower(), f"Found raw HTML div tag in agent response! Response text: {content}"
            assert "> *" in content, "Expected Markdown blockquote styling (> *text*) for the agent header, but found none."
