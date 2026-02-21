import streamlit as st


def load_css(light_mode: bool = False):
    if light_mode:
        bg              = "#f1f5f9"
        bg2             = "#e8eef5"
        bg3             = "#f8fafc"      # near-white: inputs, selectbox
        text            = "#0f172a"
        text_muted      = "#64748b"
        border          = "#94a3b8"
        btn_sec_bg      = "#e2e8f0"
        btn_sec_fg      = "#0f172a"
        scrollbar       = "#94a3b8"
        scrollbar_hover = "#64748b"
        toggle_off      = "#94a3b8"
        toggle_on       = "#2563eb"
        toggle_thumb    = "#ffffff"
        avatar_bg       = "#e2e8f0"
    else:
        bg              = "#0f172a"
        bg2             = "#1e293b"
        bg3             = "#1e293b"
        text            = "#f8fafc"
        text_muted      = "#94a3b8"
        border          = "#334155"
        btn_sec_bg      = "#1e293b"
        btn_sec_fg      = "#f8fafc"
        scrollbar       = "#334155"
        scrollbar_hover = "#475569"
        toggle_off      = "#334155"
        toggle_on       = "#2563eb"
        toggle_thumb    = "#f1f5f9"
        avatar_bg       = "#1e293b"

    st.markdown(f"""
        <style>
        /* ─── Google Fonts ─── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Outfit:wght@300;500;600;700&display=swap');

        /* ─── CSS variables ─── */
        :root {{
            --bg:        {bg};
            --bg2:       {bg2};
            --text:      {text};
            --border:    {border};
        }}

        /* ════════════════════════════════════════
           APP SHELL
        ════════════════════════════════════════ */
        .stApp,
        .stApp > div,
        section[data-testid="stMain"],
        section[data-testid="stMain"] > div,
        div[data-testid="stMainBlockContainer"],
        .block-container {{
            background-color: {bg} !important;
        }}
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div,
        section[data-testid="stSidebar"] > div > div {{
            background-color: {bg2} !important;
        }}

        /* ════════════════════════════════════════
           TYPOGRAPHY
        ════════════════════════════════════════ */
        html, body {{
            font-family: 'Inter', sans-serif;
            color: {text} !important;
        }}
        /* Cast wide net for text colour, but avoid overriding icons */
        p, span:not([class*="icon"]):not([data-testid*="Icon"]),
        label, li, td, th, div[data-testid="stMarkdownContainer"] * {{
            color: {text} !important;
        }}
        h1, h2, h3, h4 {{
            font-family: 'Outfit', sans-serif;
            font-weight: 500;
            color: {text} !important;
        }}
        small, caption,
        p[style*="0.8em"], p[style*="#94a3b8"], p[style*="#888"] {{
            color: {text_muted} !important;
        }}

        /* ════════════════════════════════════════
           CONTAINERS / CARDS
        ════════════════════════════════════════ */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: {bg2} !important;
            border: 1px solid {border} !important;
            border-radius: 8px !important;
        }}
        div[data-testid="stExpander"],
        div[data-testid="stExpander"] > div {{
            background-color: {bg2} !important;
            border: 1px solid {border} !important;
            border-radius: 8px !important;
        }}
        div[data-testid="stExpander"] * {{
            color: {text} !important;
        }}
        /* Info / warning / success boxes */
        div[data-testid="stAlert"] {{
            background-color: {bg2} !important;
            border-color: {border} !important;
        }}
        div[data-testid="stAlert"] * {{
            color: {text} !important;
        }}

        /* ════════════════════════════════════════
           METRICS
        ════════════════════════════════════════ */
        [data-testid="stMetricValue"],
        [data-testid="stMetricLabel"],
        [data-testid="stMetricDelta"] {{
            color: {text} !important;
        }}

        /* ════════════════════════════════════════
           INPUTS & SELECTBOX
        ════════════════════════════════════════ */
        input, textarea {{
            background-color: {bg3} !important;
            color: {text} !important;
            border-color: {border} !important;
        }}
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div {{
            background-color: {bg3} !important;
            color: {text} !important;
            border-color: {border} !important;
        }}
        /* Selectbox control */
        div[data-baseweb="select"] > div:first-child {{
            background-color: {bg3} !important;
            color: {text} !important;
            border-color: {border} !important;
        }}
        /* Dropdown arrow SVG */
        div[data-baseweb="select"] svg {{
            fill: {text} !important;
            color: {text} !important;
        }}
        /* Selected value text */
        div[data-baseweb="select"] [data-testid="stSelectboxValue"],
        div[data-baseweb="select"] div[class*="ValueContainer"] * {{
            color: {text} !important;
        }}
        /* Dropdown list popup */
        div[data-baseweb="popover"] ul,
        div[data-baseweb="popover"] li,
        div[role="listbox"],
        div[role="option"] {{
            background-color: {bg2} !important;
            color: {text} !important;
        }}
        div[role="option"]:hover {{
            background-color: {bg3} !important;
        }}

        /* ════════════════════════════════════════
           BUTTONS
        ════════════════════════════════════════ */
        /* Primary */
        button[kind="primary"],
        div[data-testid="stButton"] > button[kind="primary"] {{
            background-color: #2563eb !important;
            color: #ffffff !important;
            border: none !important;
        }}
        button[kind="primary"]:hover,
        div[data-testid="stButton"] > button[kind="primary"]:hover {{
            background-color: #1d4ed8 !important;
        }}
        /* Secondary / default */
        button[kind="secondary"],
        div[data-testid="stButton"] > button:not([kind="primary"]) {{
            background-color: {btn_sec_bg} !important;
            color: {btn_sec_fg} !important;
            border: 1px solid {border} !important;
        }}
        button[kind="secondary"]:hover,
        div[data-testid="stButton"] > button:not([kind="primary"]):hover {{
            opacity: 0.85;
            color: {btn_sec_fg} !important;
        }}
        /* Button icons/spans inherit correct colour */
        div[data-testid="stButton"] button span,
        div[data-testid="stButton"] button p {{
            color: inherit !important;
        }}

        /* ════════════════════════════════════════
           TOGGLES  (Streamlit uses a hidden <input> +
           adjacent styled <div> as the track)
        ════════════════════════════════════════ */
        /* Toggle label text */
        div[data-testid="stToggle"] p,
        div[data-testid="stToggle"] span {{
            color: {text} !important;
        }}
        /* Track — sibling div immediately after the hidden checkbox input */
        div[data-testid="stToggle"] input[type="checkbox"] + div {{
            background-color: {toggle_off} !important;
            border-radius: 999px !important;
            border: none !important;
        }}
        /* Track when checked */
        div[data-testid="stToggle"] input[type="checkbox"]:checked + div {{
            background-color: {toggle_on} !important;
        }}
        /* Thumb */
        div[data-testid="stToggle"] input[type="checkbox"] + div > div {{
            background-color: {toggle_thumb} !important;
            border-radius: 50% !important;
        }}
        /* Fallback using role selectors */
        div[data-testid="stToggle"] div[role="checkbox"],
        div[data-testid="stToggle"] div[role="switch"] {{
            background-color: {toggle_off} !important;
        }}
        div[data-testid="stToggle"] div[role="checkbox"][aria-checked="true"],
        div[data-testid="stToggle"] div[role="switch"][aria-checked="true"] {{
            background-color: {toggle_on} !important;
        }}
        div[data-testid="stToggle"] div[role="checkbox"] > div,
        div[data-testid="stToggle"] div[role="switch"] > div {{
            background-color: {toggle_thumb} !important;
        }}

        /* ════════════════════════════════════════
           SLIDERS
        ════════════════════════════════════════ */
        div[data-baseweb="slider"] * {{
            color: {text} !important;
        }}

        /* ════════════════════════════════════════
           CHAT
        ════════════════════════════════════════ */
        /* Chat message bubbles */
        div[data-testid="stChatMessage"] {{
            background-color: {bg2} !important;
            border: 1px solid {border} !important;
            border-radius: 8px !important;
        }}
        div[data-testid="stChatMessage"] * {{
            color: {text} !important;
        }}
        /* Avatar circle */
        div[data-testid="stChatMessageAvatarUser"],
        div[data-testid="stChatMessageAvatarAssistant"],
        div[data-testid*="chatAvatar"],
        div[data-testid*="ChatMessageAvatar"] {{
            background-color: {avatar_bg} !important;
            color: {text} !important;
            border: 1px solid {border} !important;
        }}
        /* Avatar icon / SVG fill */
        div[data-testid*="chatAvatar"] span,
        div[data-testid*="chatAvatar"] svg,
        div[data-testid*="ChatMessageAvatar"] span,
        div[data-testid*="ChatMessageAvatar"] svg {{
            color: {text} !important;
            fill: {text} !important;
        }}
        /* Chat input wrapper */
        .stChatFloatingInputContainer {{
            background-color: transparent !important;
        }}
        div[data-testid="stChatInput"] > div {{
            background-color: {bg2} !important;
            border: 1px solid {border} !important;
            border-radius: 8px !important;
        }}
        div[data-testid="stChatInput"] textarea,
        div[data-testid="stChatInput"] textarea::placeholder {{
            background-color: transparent !important;
            color: {text} !important;
        }}
        div[data-testid="stChatInput"] textarea::placeholder {{
            color: {text_muted} !important;
        }}
        /* Submit button inside chat input */
        div[data-testid="stChatInput"] button {{
            color: {text} !important;
        }}
        div[data-testid="stChatInput"] button svg {{
            fill: {text} !important;
        }}

        /* ════════════════════════════════════════
           TABS
        ════════════════════════════════════════ */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {bg2} !important;
        }}
        .stTabs [data-baseweb="tab"] p,
        .stTabs [data-baseweb="tab"] span {{
            color: {text_muted} !important;
        }}
        .stTabs [aria-selected="true"] p,
        .stTabs [aria-selected="true"] span {{
            color: {text} !important;
        }}

        /* ════════════════════════════════════════
           DATAFRAME / TABLE
        ════════════════════════════════════════ */
        div[data-testid="stDataFrame"] * {{
            color: {text} !important;
        }}
        div[data-testid="stDataFrame"] iframe {{
            background-color: {bg2} !important;
        }}

        /* ════════════════════════════════════════
           STATUS INDICATORS
        ════════════════════════════════════════ */
        .status-dot {{
            height: 10px; width: 10px;
            border-radius: 50%; display: inline-block;
            margin-right: 8px;
        }}
        .status-active {{
            background-color: #3b82f6;
            box-shadow: 0 0 8px rgba(59,130,246,0.5);
        }}
        .status-idle {{ background-color: #94a3b8; }}

        /* ════════════════════════════════════════
           CHROME / LAYOUT
        ════════════════════════════════════════ */
        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        .block-container {{
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }}

        /* ─── Custom Scrollbar ─── */
        ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: {scrollbar}; border-radius: 3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: {scrollbar_hover}; }}

        </style>
    """, unsafe_allow_html=True)
