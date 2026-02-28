from streamlit.testing.v1 import AppTest

def test_city_sync_app_level():
    """
    Simulates the agent changing the city name mid-run.
    Ensures that the inline map sync logic catches the change, 
    syncs the widget, and fetches the data for the new city before map render.
    """
    at = AppTest.from_file("app.py", default_timeout=30)
    
    # Mock user session to bypass login
    class MockUser:
        def __init__(self, email, id):
            self.email = email
            self.id = id
            
    at.session_state["user_session"] = MockUser("agent@gaiapattern.com", "456")
    at.run()
    
    assert not at.error, f"App Error during initial run: {at.error}"
    assert at.session_state["selected_city_name"] == "New York City, USA"
    assert at.session_state["last_fetched_city"] == "New York City, USA"
    
    # Manually change the selected city name (simulating what the Agent tool does)
    # We leave last_fetched_city as NYC, because the tool only updates the name.
    at.session_state["selected_city_name"] = "Cairo, Egypt"
    
    at.run()
    
    # Verify that the sync logic inside col_map caught the discrepancy, 
    # fetched new data, and updated last_fetched_city.
    assert not at.error, f"App Error during sync run: {at.error}"
    assert at.session_state["last_fetched_city"] == "Cairo, Egypt"
    assert at.session_state["selected_city_name"] == "Cairo, Egypt"
    
    # Verify toggles were activated based on new data availability
    for layer in ["trees", "water", "parks", "buildings", "traffic"]:
        toggle_key = f"toggle_{layer}"
        assert toggle_key in at.session_state
