
import unittest
import html
from unittest.mock import patch

# Custom session state class to support attribute access
class MockSessionState(dict):
    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError(f"'MockSessionState' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value

class TestSecurityXSS(unittest.TestCase):
    def setUp(self):
        # Patch the streamlit module where it is imported in agent_logic
        self.mock_st_patcher = patch('modules.agent_logic.st')
        self.mock_st = self.mock_st_patcher.start()

        # Use our custom session state
        self.session_state = MockSessionState()
        self.session_state["chat_history"] = []
        self.session_state["simulations"] = []
        self.session_state["green_ledger"] = []
        self.session_state["simulated_cooling"] = 0.0
        self.session_state["sandbox_budget"] = 1000000.0
        self.session_state["agent_status"] = "IDLE"

        self.mock_st.session_state = self.session_state
        self.mock_st.secrets = {}
        # Mock write_stream to return the input iterator as text or something
        # In process_custom_query: assistant_response = st.write_stream(_generate())
        # We need mock_st.write_stream to consume the generator and return the full string.
        def mock_write_stream(stream):
            return "".join(list(stream))
        self.mock_st.write_stream.side_effect = mock_write_stream

        # Import inside test to ensure patching works if possible, or assume already imported
        from modules.agent_logic import AgentSimulator
        self.agent = AgentSimulator()

    def tearDown(self):
        self.mock_st_patcher.stop()

    def test_simulate_intervention_xss(self):
        malicious_name = "<script>alert('XSS')</script>"
        # Also test malicious type
        malicious_type = "<img src=x onerror=alert(1)>"

        obj = {
            "asset_id": "123",
            "name": malicious_name,
            "type": malicious_type,
            "lat": 34.0,
            "lon": -118.0
        }

        self.agent.simulate_intervention_on_asset(obj)

        # Check chat history
        last_message = self.session_state["chat_history"][-1]
        content = last_message["content"]

        # Ensure raw script tag is NOT in the content
        self.assertNotIn("<script>", content, "XSS Vulnerability found in simulate_intervention_on_asset (name)")
        self.assertNotIn("<img", content, "XSS Vulnerability found in simulate_intervention_on_asset (type)")

        # Ensure it IS escaped
        self.assertIn("&lt;script&gt;", content, "Name was not escaped properly")
        self.assertIn("&lt;img", content, "Type was not escaped properly")

    def test_process_custom_query_xss(self):
        malicious_query = "<script>alert('Chat XSS')</script>"

        # Mock OpenAI client to avoid errors
        if "OPENAI_API_KEY" in self.mock_st.secrets:
            del self.mock_st.secrets["OPENAI_API_KEY"]

        self.agent.process_custom_query(malicious_query)

        # Check the user message in history (added first)
        escaped_query = html.escape(malicious_query)

        found = False
        for msg in self.session_state["chat_history"]:
             if msg["role"] == "user" and escaped_query in msg["content"]:
                 found = True
                 break

        self.assertTrue(found, "Sanitized user query not found in chat history")

        # Check that the UNSANITIZED query is NOT present as a raw script
        for msg in self.session_state["chat_history"]:
             if "<script>" in msg["content"]:
                 self.fail(f"Raw script tag found in chat history: {msg['content']}")

if __name__ == "__main__":
    unittest.main()
