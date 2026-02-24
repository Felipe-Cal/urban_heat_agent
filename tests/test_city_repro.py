from streamlit.testing.v1 import AppTest
import pytest

def test_city_selector_crash_repro():
    """
    Reproduce the AttributeError: st.session_state has no attribute "city_selector".
    This can happen if the callback triggers before the key is initialized.
    """
    at = AppTest.from_file("app.py", default_timeout=30)
    
    # Mock user session
    class MockUser:
        def __init__(self, email, id):
            self.email = email
            self.id = id
            
    at.session_state["user_session"] = MockUser("test@gaiapattern.com", "123")
    at.run()
    
    # Try to change the city using the selectbox
    # The selectbox has key="city_selector"
    try:
        at.selectbox[0].select("London, UK")
        at.run()
    except Exception as e:
        pytest.fail(f"City selector crashed with error: {e}")

    assert not at.error, f"App threw an error: {at.error}"
    assert at.session_state["selected_city_name"] == "London, UK"
