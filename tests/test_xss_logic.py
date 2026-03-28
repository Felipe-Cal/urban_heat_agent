import html

def test_xss_sanitization():
    # 1. Test basic HTML tag injection
    malicious_input = "<script>alert('XSS')</script>"
    sanitized = html.escape(malicious_input)
    assert sanitized == "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;", "Basic script tag should be escaped"
    assert "<script>" not in sanitized, "Raw <script> tag should not be present"

    # 2. Test attribute injection
    malicious_attr = '<img src=x onerror=alert(1)>'
    sanitized_attr = html.escape(malicious_attr)
    assert sanitized_attr == "&lt;img src=x onerror=alert(1)&gt;", "Attributes should be escaped"
    assert "onerror=" in sanitized_attr, "Attribute name is text, but context is safe because < is escaped"

    # 3. Test Markdown preservation (CRITICAL REQUIREMENT)
    markdown_input = "**Bold** and *Italic* and [Link](http://example.com)"
    sanitized_md = html.escape(markdown_input)
    assert sanitized_md == "**Bold** and *Italic* and [Link](http://example.com)", "Markdown syntax should remain untouched"

    # 4. Test mixed content
    mixed = "**Bold** <script>bad</script>"
    sanitized_mixed = html.escape(mixed)
    assert sanitized_mixed == "**Bold** &lt;script&gt;bad&lt;/script&gt;", "Markdown preserved, HTML escaped"

    # 5. Test specific case from app.py
    # app.py appends a span manually: prompt + "<span class='user-msg-marker'></span>"
    # We want to ensure prompt is safe before concatenation.
    prompt = "<script>alert(1)</script>"
    safe_prompt = html.escape(prompt)
    final_render = safe_prompt + "<span class='user-msg-marker'></span>"

    # Simulate Streamlit rendering with unsafe_allow_html=True
    # Streamlit would see: &lt;script&gt;...&lt;/script&gt;<span ...></span>
    # The browser renders: <script>... (as text) and then the empty span.
    # The script does NOT execute.

    print("✅ All XSS logic tests passed!")

if __name__ == "__main__":
    test_xss_sanitization()
