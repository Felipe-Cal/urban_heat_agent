import streamlit as st

def load_css(light_mode=False):
    if light_mode:
        # Light Theme Colors
        css_vars = """
            :root {
                --primary-color: #3b82f6;
                --background-color: #ffffff;
                --secondary-background-color: #f1f5f9;
                --text-color: #1e293b;
                --font: 'Inter', sans-serif;
            }
            /* Override Streamlit's default dark theme backgrounds if present */
            .stApp {
                background-color: var(--background-color);
                color: var(--text-color);
            }
        """
    else:
        # Dark Theme Colors
        css_vars = """
            :root {
                --primary-color: #3b82f6;
                --background-color: #0f172a;
                --secondary-background-color: #1e293b;
                --text-color: #e2e8f0;
                --font: 'Inter', sans-serif;
            }
            .stApp {
                background-color: var(--background-color);
                color: var(--text-color);
            }
        """

    st.markdown(f"""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Outfit:wght@300;500;600;700&display=swap');

        {css_vars}

        /* Global Typography tweaks */
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            color: var(--text-color);
        }}

        h1, h2, h3 {{
            font-family: 'Outfit', sans-serif;
            font-weight: 500;
            color: var(--text-color);
        }}

        /* Subdued Chat Input */
        .stChatFloatingInputContainer {{
            background-color: transparent !important;
        }}

        /* Status Indicators Minimalist */
        .status-dot {{
            height: 10px;
            width: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }}

        .status-active {{
            background-color: #3b82f6; /* Light Blue */
            box-shadow: 0 0 8px rgba(59, 130, 246, 0.5);
        }}
        
        .status-idle {{
            background-color: #94a3b8; /* Slate */
        }}

        /* Hide Top Right Menu for clean look */
        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        /* Reduce Top Gap */
        .block-container {{
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }}
        
        /* Subtle Custom Scrollbar for Chat */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #334155;
            border-radius: 3px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: #475569;
        }}
        
        </style>
    """, unsafe_allow_html=True)
