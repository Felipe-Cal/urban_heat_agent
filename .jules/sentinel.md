## 2026-02-26 - Streamlit Stored XSS Mitigation
**Vulnerability:** User-controlled chat input and external map asset data were rendered using `st.markdown(..., unsafe_allow_html=True)` without sanitization. This allowed attackers to inject malicious HTML/JS.
**Learning:** `st.markdown(..., unsafe_allow_html=True)` is dangerous for dynamic content. `html.escape()` sanitizes HTML tags while preserving Markdown syntax (like `**bold**`), making it the ideal mitigation for Streamlit apps that need Markdown support but must reject raw HTML.
**Prevention:** Always wrap user-controlled variables (input, external data) with `html.escape(str(variable))` before passing them to `st.markdown` when `unsafe_allow_html=True` is enabled.
