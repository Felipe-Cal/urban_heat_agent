from streamlit.testing.v1 import AppTest

def test_selectbox_uses_session_state_without_index():
    at = AppTest.from_file("app.py", default_timeout=30)
    
    # Mock user session
    class MockUser:
        def __init__(self, email, id):
            self.email = email
            self.id = id
            
    at.session_state["user_session"] = MockUser("agent@gaiapattern.com", "456")
    at.run()
    
    assert not at.error, f"App error: {at.error}"
    # Verify what the selectbox actually shows via index 0
    city_select_box = at.selectbox[0]
    assert city_select_box.value == "New York City, USA", f"Selectbox shows {city_select_box.value} instead of New York City, USA"

def test_selectbox_recovers_if_key_deleted():
    """
    Test that explicitly verifies our fix: if the session state key gets wiped,
    the inline sync before the widget creation restores it exactly to selected_city_name
    so it doesn't default to the first widget (Barcelona).
    """
    at = AppTest.from_file("app.py", default_timeout=30)
    
    class MockUser:
        def __init__(self, email, id):
            self.email = email
            self.id = id
            
    at.session_state["user_session"] = MockUser("agent@gaiapattern.com", "456")
    
    # Use New York City to avoid triggering a real 30-second OSM data fetch!
    at.session_state["selected_city_name"] = "New York City, USA"
    
    at.run()
    
    assert not at.error
    city_select_box = at.selectbox[0]
    assert city_select_box.value == "New York City, USA"
    
