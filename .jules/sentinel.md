## 2025-05-15 - Stored XSS via Streamlit Markdown
**Vulnerability:** User input rendered directly into `st.markdown(..., unsafe_allow_html=True)` allows arbitrary HTML/JS execution.
**Learning:** Streamlit's `unsafe_allow_html=True` disables all sanitization. Simply escaping HTML with `html.escape()` is sufficient to prevent XSS while preserving Markdown syntax (like `**bold**`).
**Prevention:** Always wrap user-controlled input in `html.escape()` before passing it to `st.markdown(..., unsafe_allow_html=True)`.
