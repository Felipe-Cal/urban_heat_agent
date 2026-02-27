## 2026-02-27 - Reflected XSS in Agent Chat
**Vulnerability:** Reflected Cross-Site Scripting (XSS) in the Gaia Agent chat interface.
**Learning:** Streamlit's `st.markdown(..., unsafe_allow_html=True)` is dangerous when combined with reflected user input or external data (like OSM asset names) that hasn't been strictly sanitized. We found that map asset names and user chat inputs were being reflected back to the user without escaping, allowing arbitrary HTML/JS execution.
**Prevention:**
1. Always use `html.escape()` on any variable that originates from user input or external APIs before interpolating it into a string destined for `unsafe_allow_html=True`.
2. Prefer standard Markdown syntax over HTML where possible, as Markdown parsers generally handle escaping better by default.
3. Validate and sanitize inputs at the entry point (e.g., in `AgentSimulator` methods) *and* at the rendering point (in `app.py`) for defense-in-depth.
