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
        "name": "Oak Tree",
        "type": "Tree Canopy",
        "lat": 34.05,
        "lon": -118.24
    }
    at.session_state["last_clicked_obj_id"] = "tree_123"
    at.session_state["last_clicked_obj"] = mock_asset
    at.session_state["pending_map_click"] = "Selected Oak Tree (tree_123)"
    
    # 3. Trigger a rerun (which simulates St.rerun() from the PyDeck on_select callback)
    at.run()
    
    # 4. Assertions
    # A. The pending_map_click should be cleared after parsing
    assert at.session_state["pending_map_click"] is None, "pending_map_click was not cleared"
    
    # B. The agent chat history should have recorded the intersection event
    chat_history = at.session_state["chat_history"] if "chat_history" in at.session_state else []
    
    # Look for the user message that announces the event
    event_logged = any(
        "**[EVENT]** Map intersection: Oak Tree" in msg.get("content", "") 
        for msg in chat_history 
        if msg.get("role") == "user"
    )
    
    assert event_logged, "Map click event was not passed to the AgentSimulator"
    
    # C. Verify the agent responded with analysis for the nature asset (mocked or real)
    assistant_replied = any(
        "primary cooling anchor" in msg.get("content", "") or 
        "1. **Verify Vitality" in msg.get("content", "")
        for msg in chat_history 
        if msg.get("role") == "assistant"
    )
    
    assert assistant_replied, "Agent did not output the expected analysis template for a nature asset."
