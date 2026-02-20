import streamlit as st

def load_css():
    st.markdown("""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Outfit:wght@300;500;700&display=swap');

        /* Global Reset & Typography - ELECTRIC THEME */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: #ffffff; /* White text */
            background-color: #050505; /* Deep Black */
        }

        h1, h2, h3 {
            font-family: 'Outfit', sans-serif;
            font-weight: 500;
            color: #ffffff;
        }

        /* Streamlit Container Fixes */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 95% !important;
        }
        
        /* Electric Panel (replaces bio-card) */
        .electric-panel {
            background: rgba(15, 20, 25, 0.8);
            border: 1px solid rgba(0, 229, 255, 0.3); /* Electric Blue Border */
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.1);
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .electric-panel:hover {
            border-color: rgba(0, 229, 255, 0.8);
            box-shadow: 0 0 15px rgba(0, 229, 255, 0.3);
        }

        /* Status Indicators */
        .status-dot {
            height: 10px;
            width: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }

        .status-active {
            background-color: #00e5ff; /* Electric Blue */
            box-shadow: 0 0 0 4px rgba(0, 229, 255, 0.2);
            animation: pulse-blue 2s infinite;
        }

        @keyframes pulse-blue {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(0, 229, 255, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 229, 255, 0); }
        }

        /* Button Styling - Agent Shortcuts */
        div.stButton > button {
            border-radius: 0.5rem;
            border: 1px solid #00e5ff;
            background-color: transparent;
            color: #00e5ff;
            font-weight: 500;
            transition: all 0.2s;
            width: 100%;
        }
        
        div.stButton > button:hover {
            background-color: rgba(0, 229, 255, 0.1);
            border-color: #00e5ff;
            color: #ffffff;
            box-shadow: 0 0 8px rgba(0, 229, 255, 0.5);
        }

        .stSelectbox label {
            color: #00e5ff !important;
        }
        
        /* Chat UI Overrides */
        .stChatInput {
            border-color: #00e5ff !important;
        }

        /* Hide Top Right Menu for clean look */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        
        </style>
    """, unsafe_allow_html=True)
