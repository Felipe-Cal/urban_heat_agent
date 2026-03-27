## 2025-10-26 - Streamlit Login Forms need Autocomplete
**Learning:** Streamlit apps often default to generic text inputs for credentials, breaking password manager autofill.
**Action:** Always add `autocomplete="email"` and `autocomplete="current-password"`/`new-password` to `st.text_input` for auth forms.
