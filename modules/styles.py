import streamlit as st

# Border colour is intentionally the same in both modes
# (dark slate — always visible regardless of background)
_BORDER = "#334155"


def load_css(light_mode: bool = False):
    if light_mode:
        bg              = "#f1f5f9"
        bg2             = "#d8e3ef"   # clearly darker than bg — makes containers pop
        bg3             = "#f8fafc"      # near-white — inputs & selectbox only
        text            = "#0f172a"
        text_muted      = "#64748b"
        btn_sec_bg      = "#dde4ef"
        btn_sec_fg      = "#0f172a"
        scrollbar       = "#94a3b8"
        scrollbar_hover = "#64748b"
        avatar_bg       = "#dde4ef"
        tooltip_bg      = "#1e293b"
        tooltip_text    = "#f8fafc"
    else:
        bg              = "#0f172a"
        bg2             = "#1e293b"
        bg3             = "#1e293b"
        text            = "#f8fafc"
        text_muted      = "#94a3b8"
        btn_sec_bg      = "#1e293b"
        btn_sec_fg      = "#f8fafc"
        scrollbar       = "#334155"
        scrollbar_hover = "#475569"
        avatar_bg       = "#1e293b"
        tooltip_bg      = "#334155"
        tooltip_text    = "#f8fafc"

    border = _BORDER   # Same in both modes

    st.markdown(f"""
        <style>
        /* ─── Google Fonts ─── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Outfit:wght@300;500;600;700&display=swap');

        /* ─── CSS variables ─── */
        :root {{
            --bg:    {bg};
            --bg2:   {bg2};
            --text:  {text};
            --border:{border};
        }}

        /* ════════════════════════
           APP SHELL
        ════════════════════════ */
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

        /* ════════════════════════
           TYPOGRAPHY
           — `div` inclusion ensures text nodes inside inline HTML inherit colour
        ════════════════════════ */
        html, body {{
            font-family: 'Inter', sans-serif;
            color: {text} !important;
        }}
        div, p, span, label, li, td, th, a, blockquote, pre, code {{
            color: {text};
            font-family: 'Inter', sans-serif;
        }}
        small, caption {{ color: {text_muted} !important; }}
        h1, h2, h3, h4 {{
            font-family: 'Outfit', sans-serif;
            font-weight: 500;
            color: {text} !important;
        }}
        div[data-testid="stMarkdownContainer"],
        div[data-testid="stMarkdownContainer"] * {{
            color: {text} !important;
        }}

        /* ════════════════════════
           CONTAINERS / CARDS
        ════════════════════════ */
        /* Outer container (st.container(border=True)) — the big box around
           chat messages + chat input. Needs a clearly visible border in
           light mode, so we use both border AND outline as a fallback. */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: {bg2} !important;
            border: 2px solid {border} !important;
            outline: 2px solid {border} !important;
            outline-offset: -2px;
            border-radius: 8px !important;
        }}
        div[data-testid="stExpander"],
        div[data-testid="stExpander"] > div {{
            background-color: {bg2} !important;
            border: 1px solid {border} !important;
            border-radius: 8px !important;
        }}
        div[data-testid="stExpander"] * {{ color: {text} !important; }}
        div[data-testid="stAlert"] {{
            background-color: {bg2} !important;
            border-color: {border} !important;
        }}
        div[data-testid="stAlert"] * {{ color: {text} !important; }}

        /* ════════════════════════
           METRICS
        ════════════════════════ */
        [data-testid="stMetricValue"],
        [data-testid="stMetricLabel"],
        [data-testid="stMetricDelta"] {{ color: {text} !important; }}

        /* ════════════════════════
           INPUTS & SELECTBOX
           CRITICAL: exclude checkbox/radio — styling those hides toggle tracks!
        ════════════════════════ */
        input:not([type="checkbox"]):not([type="radio"]),
        textarea {{
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
        /* Selectbox */
        div[data-baseweb="select"] > div:first-child {{
            background-color: {bg3} !important;
            color: {text} !important;
            border-color: {border} !important;
        }}
        div[data-baseweb="select"] svg {{ fill: {text} !important; }}
        div[data-baseweb="select"] [data-testid="stSelectboxValue"],
        div[data-baseweb="select"] div[class*="ValueContainer"] * {{
            color: {text} !important;
        }}
        /* Dropdown list */
        div[data-baseweb="popover"] ul,
        div[data-baseweb="popover"] li,
        div[role="listbox"],
        div[role="option"] {{
            background-color: {bg2} !important;
            color: {text} !important;
        }}
        div[role="option"]:hover {{ background-color: {bg3} !important; }}

        /* ════════════════════════
           BUTTONS
        ════════════════════════ */
        button[kind="primary"],
        div[data-testid="stButton"] > button[kind="primary"] {{
            background-color: #2563eb !important;
            color: #ffffff !important;
            border: none !important;
        }}
        button[kind="primary"]:hover {{ background-color: #1d4ed8 !important; }}
        button[kind="primary"] *,
        div[data-testid="stButton"] > button[kind="primary"] * {{
            color: #ffffff !important;
            fill: #ffffff !important;
        }}
        button[kind="secondary"],
        div[data-testid="stButton"] > button:not([kind="primary"]) {{
            background-color: {btn_sec_bg} !important;
            color: {btn_sec_fg} !important;
            border: 1px solid {border} !important;
        }}
        button[kind="secondary"] *,
        div[data-testid="stButton"] > button:not([kind="primary"]) * {{
            color: {btn_sec_fg} !important;
        }}

        /* ════════════════════════
           TOGGLES
           The hidden <input type="checkbox"> must have NO background styling
           (see INPUTS section above — we exclude [type="checkbox"]).
           Streamlit's baseweb toggle applies dynamically coloured divs:
             • ON  → primary colour (blue) via baseweb, works automatically
             • OFF → secondaryBackground colour, may be invisible on light bg
           We override with role-based selectors (most reliable without class names).
        ════════════════════════ */
        div[data-testid="stToggle"] p,
        div[data-testid="stToggle"] span {{ color: {text} !important; }}

        /* role=switch / role=checkbox — baseweb toggle track */
        div[data-testid="stToggle"] [role="switch"],
        div[data-testid="stToggle"] [role="checkbox"] {{
            background-color: {_BORDER} !important; /* visible gray in both modes */
            border-radius: 999px !important;
        }}
        div[data-testid="stToggle"] [role="switch"][aria-checked="true"],
        div[data-testid="stToggle"] [role="checkbox"][aria-checked="true"] {{
            background-color: #2563eb !important;
        }}
        /* Thumb */
        div[data-testid="stToggle"] [role="switch"] > div,
        div[data-testid="stToggle"] [role="checkbox"] > div {{
            background-color: #ffffff !important;
            border-radius: 50% !important;
        }}
        /* Disabled track */
        div[data-testid="stToggle"] [role="switch"][aria-disabled="true"],
        div[data-testid="stToggle"] [role="checkbox"][aria-disabled="true"] {{
            background-color: {border} !important;
            opacity: 0.55;
        }}
        /* Disabled thumb */
        div[data-testid="stToggle"] [role="switch"][aria-disabled="true"] > div,
        div[data-testid="stToggle"] [role="checkbox"][aria-disabled="true"] > div {{
            background-color: #cbd5e1 !important;
        }}

        /* ════════════════════════
           SLIDERS
        ════════════════════════ */
        div[data-baseweb="slider"] * {{ color: {text} !important; }}

        /* ════════════════════════
           CHAT
        ════════════════════════ */
        div[data-testid="stChatMessage"] {{
            background-color: {bg2} !important;
            border: 1.5px solid {border} !important;
            border-radius: 8px !important;
        }}
        div[data-testid="stChatMessage"] * {{ color: {text} !important; }}
        div[data-testid*="chatAvatar"],
        div[data-testid*="ChatMessageAvatar"] {{
            background-color: {avatar_bg} !important;
            border: 1px solid {border} !important;
            border-radius: 50% !important;
        }}
        div[data-testid*="chatAvatar"] span,
        div[data-testid*="chatAvatar"] svg,
        div[data-testid*="ChatMessageAvatar"] span,
        div[data-testid*="ChatMessageAvatar"] svg {{
            color: {text} !important;
            fill: {text} !important;
        }}
        /* Chat input */
        .stChatFloatingInputContainer {{ background-color: transparent !important; }}
        div[data-testid="stChatInput"] > div {{
            background-color: {bg2} !important;
            border: 1.5px solid {border} !important;
            border-radius: 8px !important;
        }}
        div[data-testid="stChatInput"] div[data-baseweb="textarea"],
        div[data-testid="stChatInput"] div[data-baseweb="textarea"] > div,
        div[data-testid="stChatInput"] textarea {{
            background-color: {bg2} !important;
            color: {text} !important;
            border: none !important;
        }}
        div[data-testid="stChatInput"] textarea::placeholder {{
            color: {text_muted} !important;
        }}
        div[data-testid="stChatInput"] button {{ color: {text} !important; }}
        div[data-testid="stChatInput"] button svg {{ fill: {text} !important; }}

        /* ════════════════════════
           TOOLTIPS (button hover info popups)
        ════════════════════════ */
        [data-baseweb="tooltip"],
        div[data-baseweb="tooltip"],
        div[data-baseweb="tooltip"] > div {{
            background-color: {tooltip_bg} !important;
            color: {tooltip_text} !important;
            border: 1px solid {border} !important;
            border-radius: 6px !important;
        }}
        [data-baseweb="tooltip"] *,
        div[data-baseweb="tooltip"] * {{ color: {tooltip_text} !important; }}

        /* ════════════════════════
           TABS
        ════════════════════════ */
        .stTabs [data-baseweb="tab-list"] {{ background-color: {bg2} !important; }}
        .stTabs [data-baseweb="tab"] p,
        .stTabs [data-baseweb="tab"] span {{ color: {text_muted} !important; }}
        .stTabs [aria-selected="true"] p,
        .stTabs [aria-selected="true"] span {{ color: {text} !important; }}

        /* ════════════════════════
           DATAFRAME
        ════════════════════════ */
        div[data-testid="stDataFrame"] * {{ color: {text} !important; }}

        /* ════════════════════════
           STATUS DOTS
        ════════════════════════ */
        .status-dot {{
            height:10px; width:10px;
            border-radius:50%; display:inline-block; margin-right:8px;
        }}
        .status-active {{
            background-color:#3b82f6;
            box-shadow:0 0 8px rgba(59,130,246,0.5);
        }}
        .status-idle {{ background-color:#94a3b8; }}

        /* ════════════════════════
           CHROME / LAYOUT
        ════════════════════════ */
        #MainMenu {{visibility:hidden;}}
        header {{visibility:hidden;}}
        .block-container {{
            padding-top:1rem !important;
            padding-bottom:1rem !important;
        }}
        ::-webkit-scrollbar {{ width:6px; height:6px; }}
        ::-webkit-scrollbar-track {{ background:transparent; }}
        ::-webkit-scrollbar-thumb {{ background:{scrollbar}; border-radius:3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background:{scrollbar_hover}; }}

        </style>
    """, unsafe_allow_html=True)
