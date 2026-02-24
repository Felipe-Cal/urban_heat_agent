import html
import pytest

def test_html_escape_sanitizes_xss():
    """Test that html.escape properly sanitizes XSS vectors."""
    payload = "<script>alert('XSS')</script>"
    escaped = html.escape(payload)
    assert escaped == "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;"
    assert "<script>" not in escaped

def test_html_escape_preserves_markdown():
    """Test that html.escape preserves Markdown syntax."""
    payload = "**Bold Text** and *Italic*"
    escaped = html.escape(payload)
    assert escaped == "**Bold Text** and *Italic*"

def test_mixed_content():
    """Test mixed markdown and HTML."""
    payload = "**Hello** <script>bad()</script>"
    escaped = html.escape(payload)
    assert escaped == "**Hello** &lt;script&gt;bad()&lt;/script&gt;"
