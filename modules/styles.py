import streamlit as st

def load_css():
    st.markdown("""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Outfit:wght@300;500;700&display=swap');

        /* Global Reset & Typography */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: #0f172a; /* Slate 900 */
            background-color: #ffffff;
        }

        h1, h2, h3 {
            font-family: 'Outfit', sans-serif;
            font-weight: 500;
        }

        /* Streamlit Container Fixes */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #f8fafc; /* Slate 50 */
            border-right: 1px solid #e2e8f0;
        }
        
        /* Bio-Minimalist Card Style */
        .bio-card {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .bio-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025);
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
            background-color: #059669; /* Emerald 600 */
            box-shadow: 0 0 0 4px rgba(5, 150, 105, 0.2);
            animation: pulse-green 2s infinite;
        }

        .status-alert {
            background-color: #f59e0b; /* Amber 500 */
            box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.2);
            animation: pulse-amber 2s infinite;
        }

        @keyframes pulse-green {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(5, 150, 105, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(5, 150, 105, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(5, 150, 105, 0); }
        }

        @keyframes pulse-amber {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(245, 158, 11, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
        }

        /* Custom Metric */
        .metric-label {
            font-size: 0.875rem;
            color: #64748b; /* Slate 500 */
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .metric-value {
            font-size: 1.5rem;
            font-weight: 600;
            color: #0f172a;
        }
        
        /* Button Styling */
        div.stButton > button {
            border-radius: 0.75rem;
            border: 1px solid #e2e8f0;
            background-color: white;
            color: #0f172a;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        div.stButton > button:hover {
            border-color: #cbd5e1;
            background-color: #f8fafc;
            transform: translateY(-1px);
        }

        </style>
    """, unsafe_allow_html=True)
