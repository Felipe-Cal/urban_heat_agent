import random
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, time as dtime, timedelta
import streamlit as st
import pandas as pd
import numpy as np
import time
import os
from supabase import create_client, Client
from modules.styles import load_css
from modules.data_generator import generate_mock_data
from modules.map_layers import create_map
from modules.agent_logic import AgentSimulator
from modules.models import CityData, LayerToggles, MapConfig, BBox
import sys
try:
    import extra_streamlit_components as stx
except ImportError:
    st.warning("⚠️ Module 'extra_streamlit_components' not found. Session recovery will be disabled.")
    class DummyStx:
        def CookieManager(self): return None
    stx = DummyStx()

# 1. Page Config - MUST BE FIRST
st.set_page_config(
    page_title="Gaia Heat Sync | Planetary Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Supabase Auth Connection
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        if not url or not key:
            st.warning("⚠️ SUPABASE_URL or SUPABASE_KEY missing in secrets. Restricted mode active.")
            return None
        return create_client(url, key)
    except Exception as e:
        st.error(f"Supabase init error: {e}")
        return None

supabase = init_supabase()

# 3. Cookie Manager & Session Recovery
def get_cookie_manager():
    try:
        return stx.CookieManager()
    except Exception as e:
        st.warning(f"Cookie manager failed: {e}")
        return None

cookie_manager = get_cookie_manager()

def restore_session():
    if not supabase or not cookie_manager:
        return

    if st.session_state.get("user_session"):
        return

    # extra-streamlit-components requires a small delay or multiple runs to get cookies
    try:
        access_token = cookie_manager.get("sb-access-token") if cookie_manager else None
        refresh_token = cookie_manager.get("sb-refresh-token") if cookie_manager else None

        if access_token and refresh_token:
            response = supabase.auth.set_session(access_token, refresh_token)
            if response.user:
                st.session_state["user_session"] = response.user
                st.rerun()
    except Exception as e:
        # Token might be invalid or expired, just clear them
        print(f"Session restoration failed: {e}")
        try:
            if cookie_manager:
                cookie_manager.delete("sb-access-token")
                cookie_manager.delete("sb-refresh-token")
        except:
            pass

restore_session()

# (load_css is called after session state is initialized so it can read light_mode)

# City Data (Bio-Regions) with UTC Offsets
CITIES = {
    # radius: OSM fetch radius in metres — larger for sprawling cities
    "Barcelona, Spain":    {"lat": 41.3851,  "lon": 2.1734,    "offset": 1,    "radius": 2500},
    "Cairo, Egypt":        {"lat": 30.0444,  "lon": 31.2357,   "offset": 2,    "radius": 3500},
    "London, UK":          {"lat": 51.5074,  "lon": -0.1278,   "offset": 0,    "radius": 3000},
    "Los Angeles, USA":    {"lat": 34.0522,  "lon": -118.2437, "offset": -8,   "radius": 6000},
    "Madrid, Spain":       {"lat": 40.4168,  "lon": -3.7038,   "offset": 1,    "radius": 3000},
    "Mexico City, Mexico": {"lat": 19.4326,  "lon": -99.1332,  "offset": -6,   "radius": 4000},
    "Mumbai, India":       {"lat": 19.0760,  "lon": 72.8777,   "offset": 5.5,  "radius": 3000},
    "New York City, USA":  {"lat": 40.7128,  "lon": -74.0060,  "offset": -5,   "radius": 3500},
    "San Francisco, USA":  {"lat": 37.7749,  "lon": -122.4194, "offset": -8,   "radius": 2500},
    "São Paulo, Brazil":   {"lat": -23.5505, "lon": -46.6333,  "offset": -3,   "radius": 5000},
    "Singapore":           {"lat": 1.3521,   "lon": 103.8198,  "offset": 8,    "radius": 2000},
    "Sydney, Australia":   {"lat": -33.8688, "lon": 151.2093,  "offset": 11,   "radius": 3500},
    "Tokyo, Japan":        {"lat": 35.6762,  "lon": 139.6503,  "offset": 9,    "radius": 3000},
}

def get_city_local_time(city_name):
    from datetime import datetime, timedelta, timezone, time as dtime
    offset = CITIES[city_name].get("offset", 0)
    # Get current UTC time (modern way to avoid deprecation)
    utc_now = datetime.now(timezone.utc)
    # Apply offset
    city_now = utc_now + timedelta(hours=offset)
    return city_now.time().replace(second=0, microsecond=0)

# 4. Initialize Session State
_state_defaults = {
    "user_session":       None,

    "selected_city_name": "New York City, USA",
    "time_of_day":        get_city_local_time("New York City, USA"),
    "pending_map_click":  None,
    "pending_quick_action": None,
    "last_clicked_asset": None,
    "last_clicked_obj":   None,
    "sandbox_mode":       False,
    "simulations":        [],
    "simulated_cooling":  0.0,
    "sandbox_budget":     5_000_000.0,
    "green_ledger":       [],
    "generating_pdf":     False,
    "map_viewport":       None,
    "map_bbox":           None,
    "light_mode":         False,
    "need_initial_analysis": True,
    "last_fetched_city":  None,
    "map_annotations":    [],
}
for key, default in _state_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# 3. Load Styles (here, after session state, so light_mode is available)
load_css(light_mode=st.session_state.light_mode)

# 5. Authentication UI Handlers

def handle_login(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user and response.session:
            st.session_state["user_session"] = response.user
            if cookie_manager:
                cookie_manager.set("sb-access-token", response.session.access_token, key="set_access_token")
                cookie_manager.set("sb-refresh-token", response.session.refresh_token, key="set_refresh_token")
            st.success("Login successful!")
            st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

def handle_signup(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            # Try to auto-login immediately (works if email confirmation is disabled)
            try:
                login_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if login_response.session:
                    st.session_state["user_session"] = login_response.user
                    if cookie_manager:
                        cookie_manager.set("sb-access-token", login_response.session.access_token, key="signup_access_token")
                        cookie_manager.set("sb-refresh-token", login_response.session.refresh_token, key="signup_refresh_token")
                    st.success("Account created successfully! Logging you in...")
                    time.sleep(1)
                    st.rerun()
                    return
            except Exception:
                pass
            
            st.success("Sign up successful! Please switch to the Login tab or check your email.")
        else:
            st.warning("Check your email for a confirmation link.")
    except Exception as e:
        st.error(f"Sign up failed: {e}")

def handle_logout():
    try:
        supabase.auth.sign_out()
    except Exception as e:
        pass # Ignore remote signout failures
    if cookie_manager:
        cookie_manager.delete("sb-access-token")
        cookie_manager.delete("sb-refresh-token")
    st.session_state.clear()
    st.rerun()

def handle_google_login():
    try:
        response = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": "http://localhost:8501"
            }
        })
        if response.url:
            st.session_state["waiting_for_oauth"] = True
            st.markdown(f'<meta http-equiv="refresh" content="0;url={response.url}">', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Google login failed: {e}")

# We depend entirely on st.session_state["user_session"] which is unique per browser session.

# 6. Main App Check: Show Login Page if not authenticated
if not st.session_state.get("user_session"):
    st.markdown("<h1 style='text-align: center;'>🌍 Gaia Heat Sync</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Planetary Intelligence Platform</h3>", unsafe_allow_html=True)
    st.write("---")
    
    if not supabase:
        st.info("💡 Application is running in local mode (Supabase disconnected). Please log in with any credentials if simulated.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login to your account")
            with st.form("login_form"):
                log_email = st.text_input("Email", key="log_email", placeholder="name@company.com", autocomplete="email")
                log_password = st.text_input("Password", type="password", key="log_password", placeholder="••••••••", autocomplete="current-password")
                submit_login = st.form_submit_button("Login", type="primary", use_container_width=True)
                
                if submit_login:
                    if log_email and log_password:
                        handle_login(log_email, log_password)
                    else:
                        st.warning("Please provide both email and password.")
            
            st.markdown("---")
            if st.button("Continue with Google 🚀", use_container_width=True):
                handle_google_login()
                        
        with tab2:
            st.subheader("Create a new account")
            with st.form("signup_form"):
                sign_email = st.text_input("Email", key="sign_email", placeholder="name@company.com", autocomplete="email")
                sign_password = st.text_input("Password", type="password", key="sign_password", placeholder="••••••••", help="Minimum 6 characters", autocomplete="new-password")
                sign_password_confirm = st.text_input("Confirm Password", type="password", key="sign_password_confirm", placeholder="••••••••", help="Must match above", autocomplete="new-password")
                submit_signup = st.form_submit_button("Sign Up", type="primary", use_container_width=True)
                
                if submit_signup:
                    if sign_email and sign_password:
                        if sign_password == sign_password_confirm:
                            if len(sign_password) >= 6:
                                handle_signup(sign_email, sign_password)
                            else:
                                st.warning("Password must be at least 6 characters long.")
                        else:
                            st.warning("Passwords do not match.")
                    else:
                        st.warning("Please provide both email and password.")

    st.stop() # Stops execution here so the main app doesn't render

# 7. Authenticated App Flow below this line
with st.sidebar:
    st.markdown("### Profile")
    st.write(f"Logged in as: `{st.session_state['user_session'].email}`")
    if st.button("Log Out"):
        handle_logout()

# Process Pending Map Clicks and Actions BEFORE UI rendering
# This ensures that updating toggle states (like toggle_sensors) happens before
# Streamlit binds them to the frontend widgets.
if st.session_state.pending_map_click:
    prompt = st.session_state.pending_map_click
    obj = st.session_state.last_clicked_obj
    st.session_state.pending_map_click = None

    # st.rerun() removed to avoid resetting layer toggles
    pass

if st.session_state.get("pending_quick_action"):
    action = st.session_state.pending_quick_action
    st.session_state.pending_quick_action = None
    
    if action == "data_deserts":
        st.session_state.agent.simulate_deployment()
        st.session_state.toggle_sensors = True
    elif action == "thermal_risk":
        st.session_state.agent.simulate_intervention()
        st.session_state.toggle_trees = True
    elif action == "auto_analyze":
        st.session_state.agent.auto_analyze_region()
        
    # st.rerun() removed to avoid resetting layer toggles
    pass


# Layer toggles — all off by default on first page load.
# activate_data_layers() will turn on non-thermal layers once data is ready.
_ALL_LAYERS = [
    "thermal", "trees", "water", "parks", "shelters", "fountains",
    "green_roofs", "gardens", "forests", "wetlands", "sensors",
    "buildings", "traffic",
]
for layer in _ALL_LAYERS:
    if f"toggle_{layer}" not in st.session_state:
        st.session_state[f"toggle_{layer}"] = False

# Map from toggle name → CityData attribute
_LAYER_DATA_FIELD = {
    "trees": "df_trees",    "water": "df_water",   "parks": "df_parks",
    "shelters": "df_shelters", "fountains": "df_fountains",
    "green_roofs": "df_green_roofs", "gardens": "df_gardens",
    "forests": "df_forests", "wetlands": "df_wetlands",
    "sensors": "df_sensors", "buildings": "df_buildings", "traffic": "df_traffic",
}


def activate_data_layers(data: CityData) -> None:
    """Enable all layers with data, leave thermal OFF (too noisy by default)."""
    for layer, field in _LAYER_DATA_FIELD.items():
        st.session_state[f"toggle_{layer}"] = not getattr(data, field).empty
    st.session_state["toggle_thermal"] = False


def fetch_data_with_loading(lat, lon, time_of_day, city_name, action_desc, radius_meters: int = 2500, existing_data: Optional[CityData] = None) -> CityData:
    progress_bar = st.progress(0, text=f"{action_desc} ({city_name})...")

    def update_progress(msg, pct):
        progress_bar.progress(pct, text=f"{action_desc} ({city_name}) - {msg}")

    data = generate_mock_data(
        lat, lon, time_of_day,
        progress_callback=update_progress,
        openaq_api_key=st.secrets.get("OPENAQ_API_KEY"),
        radius_meters=radius_meters,
        existing_data=existing_data,
    )
    progress_bar.empty()
    return data


# Load data on first run or if city changed
if "data" not in st.session_state or st.session_state.get("last_fetched_city") != st.session_state.selected_city_name:
    if st.session_state.selected_city_name not in CITIES:
        st.session_state.selected_city_name = "New York City, USA"
    city = CITIES[st.session_state.selected_city_name]
    st.session_state.data = fetch_data_with_loading(
        city["lat"], city["lon"],
        st.session_state.time_of_day,
        st.session_state.selected_city_name,
        "Initializing Gaia Node",
        radius_meters=city.get("radius", 2500),
    )
    st.session_state.last_fetched_city = st.session_state.selected_city_name
    activate_data_layers(st.session_state.data)

if "agent" not in st.session_state:
    st.session_state.agent = AgentSimulator()

# Trigger Initial Analysis if needed
if st.session_state.get("need_initial_analysis"):
    st.session_state.agent.auto_analyze_region(st.session_state.data)
    st.session_state.need_initial_analysis = False

# Unpack data fields by name — no positional indexing
city_data: CityData = st.session_state.data
agent: AgentSimulator = st.session_state.agent

# Data Sanity Check
if city_data.df_buildings.empty and city_data.df_trees.empty:
    st.toast("⚠️ No map data (buildings/nature) returned from OSM for this area.", icon="ℹ️")
if city_data.df_thermal.empty:
    st.toast("⚠️ No thermal grid generated. Check city coordinates.", icon="🌡️")

# Display any deferred OSM fetch errors as toasts
if st.session_state.data.fetch_error:
    st.toast(st.session_state.data.fetch_error, icon="🚨")
    # Clear by replacing with a copy that has fetch_error=None
    from dataclasses import replace
    st.session_state.data = replace(st.session_state.data, fetch_error=None)
    city_data = st.session_state.data

# --- MAIN LAYOUT ---
# Theme Toggle at Top Right — pure CSS approach (no config.toml writes)
# Note: no explicit st.rerun() needed — the button click already triggers a
# Streamlit rerun, and load_css() will re-inject the correct theme CSS.
t1, t2 = st.columns([95, 5])
with t2:
    light_mode = st.session_state.get("light_mode", False)
    theme_icon = ":material/dark_mode:" if light_mode else ":material/light_mode:"
    if st.button("", icon=theme_icon, help="Toggle Theme"):
        st.session_state.light_mode = not light_mode

# 40% Left (Agent), 60% Right (Map)
col_agent, col_map = st.columns([4, 6], gap="large")

# Re-instantiate the agent on every run so it picks up code changes during dev
# (We pass chat history separately if needed, but AgentSimulator handles it internally)
from modules.agent_logic import AgentSimulator



# ==========================================
# LEFT COLUMN: THE AGENT (THE PROXY)
# ==========================================
with col_agent:
    st.markdown("### :material/public: Gaia Agent")

    # Status Indicator — always blue when data is loaded/connected
    st.markdown(
        f'<div style="height: 10px; width: 10px; border-radius: 50%; display: inline-block; '
        f'background-color: #3b82f6; box-shadow: 0 0 6px rgba(59,130,246,0.6); margin-right: 8px;">'
        f'</div> System Node: {st.session_state.selected_city_name}',
        unsafe_allow_html=True,
    )

    st.markdown("<br/>", unsafe_allow_html=True)

    # Unified chat + input container
    with st.container(border=True):
        chat_container = st.container(height=450, border=False)
        
        with chat_container:
            for msg in st.session_state.chat_history:
                avatar = ":material/person:" if msg["role"] == "user" else ":material/smart_toy:"
                with st.chat_message(msg["role"], avatar=avatar):
                    if msg["role"] == "user":
                        st.markdown(msg['content'] + "<span class='user-msg-marker'></span>", unsafe_allow_html=True)
                    else:
                        st.markdown(msg["content"], unsafe_allow_html=True)

        if prompt := st.chat_input("Ask Gaia to analyze regions, verify data, or propose interventions..."):
            with chat_container:
                with st.chat_message("user", avatar=":material/person:"):
                    st.markdown(prompt + "<span class='user-msg-marker'></span>", unsafe_allow_html=True)
                with st.chat_message("assistant", avatar=":material/smart_toy:"):
                    agent.process_custom_query(prompt)
            st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    # Quick Actions
    st.markdown("<p style='font-size: 0.8em; color: #888; font-weight: 600;'>QUICK ACTIONS</p>", unsafe_allow_html=True)

    # Preferred Action (Primary/Blue)
    if st.button(":material/public: Analyze City Heat Risk", use_container_width=True, type="primary"):
        st.session_state.pending_quick_action = "auto_analyze"
        st.rerun()

    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        if st.button(":material/radar: Map Data Deserts", use_container_width=True):
            st.session_state.pending_quick_action = "data_deserts"
            st.rerun()
            
        if st.session_state.sandbox_mode:
            if st.button(":material/cancel: Exit Sandbox", use_container_width=True):
                st.session_state.sandbox_mode = False
                st.session_state.simulations = []
                st.session_state.green_ledger = []
                st.session_state.simulated_cooling = 0.0
                st.session_state.sandbox_budget = 5_000_000.0
                st.rerun()
        else:
            if st.button(":material/nature: Launch Sandbox", use_container_width=True):
                st.session_state.sandbox_mode = True
                st.rerun()

    with btn_col2:
        if st.button(":material/thermostat: Map Thermal Risk", use_container_width=True):
            st.session_state.pending_quick_action = "thermal_risk"
            st.rerun()
            
        if st.button(":material/summarize: Generate Briefing", use_container_width=True):
            st.session_state.generating_pdf = True
            st.rerun()

    # Optional Sandbox Active Info
    if st.session_state.sandbox_mode:
        st.markdown("<br/>", unsafe_allow_html=True)
        st.info(
            f"**Sandbox Active:** Click map to simulate interventions. "
            f"| **Budget Remaining:** **${st.session_state.sandbox_budget:,.0f}**",
            icon=":material/info:",
        )
        if st.session_state.simulations:
            if st.button("🗑️ Clear Interventions", use_container_width=True):
                st.session_state.simulations = []
                st.session_state.green_ledger = []
                st.session_state.simulated_cooling = 0.0
                st.session_state.sandbox_budget = 5_000_000.0
                st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    # Supporting Data Structures (Ledger)
    with st.expander(
        "🔗 Green Ledger (Verifiable Data Provenance)",
        expanded=bool(st.session_state.green_ledger),
    ):
        if not st.session_state.green_ledger:
            st.caption("No cooling claims registered yet. Mint Nature IDs in the Sandbox to build the ledger.")
            if st.button("⚙️ Simulate Legacy Verification", use_container_width=True):
                agent.simulate_verification()
                st.rerun()
        else:
            ledger_df = pd.DataFrame(st.session_state.green_ledger)
            st.dataframe(ledger_df, use_container_width=True, hide_index=True)

    if st.session_state.generating_pdf:
        with st.spinner("Generating Professional PDF Briefing..."):
            pdf_bytes = agent.generate_pdf_report()
            if pdf_bytes:
                st.session_state.pdf_ready = pdf_bytes
            st.session_state.generating_pdf = False
            st.rerun()

    if "pdf_ready" in st.session_state:
        city_slug = st.session_state.selected_city_name.split(",")[0].replace(" ", "_")
        st.download_button(
            label=":material/download: Download PDF Briefing",
            data=st.session_state.pdf_ready,
            file_name=f"Gaia_Briefing_{city_slug}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )


# ==========================================
# RIGHT COLUMN: THE BIOSPHERE (MAP & DATA)
# ==========================================
with col_map:
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 1, 1, 1])

    with ctrl1:
        selected_city = st.selectbox(
            ":material/location_on: Active Bio-Region",
            options=list(CITIES.keys()),
            index=list(CITIES.keys()).index(st.session_state.selected_city_name),
            label_visibility="collapsed",
        )
        if selected_city != st.session_state.selected_city_name:
            st.session_state.selected_city_name = selected_city
            # Reset slider to the new city's current local time
            st.session_state.time_of_day = get_city_local_time(selected_city)
            coords = CITIES[selected_city]
            st.session_state.data = fetch_data_with_loading(
                coords["lat"], coords["lon"],
                st.session_state.time_of_day,
                selected_city,
                "Establishing connection to",
                radius_meters=coords.get("radius", 2500),
            )
            activate_data_layers(st.session_state.data)
            city_data = st.session_state.data
            st.session_state.need_initial_analysis = True
            st.rerun()

    # ── Shared temporal calculations (used by Heat Risk + Avg Temp) ──────────
    from datetime import datetime, time as dtime
    t_now = get_city_local_time(st.session_state.selected_city_name)
    frac_now = t_now.hour + (t_now.minute / 60.0)
    t_sim = st.session_state.time_of_day
    frac_sim = t_sim.hour + (t_sim.minute / 60.0)

    def get_var(h): return -5.0 * np.cos((h - 4) * np.pi / 11.0)
    sim_delta = get_var(frac_sim) - get_var(frac_now)

    cooling = st.session_state.simulated_cooling
    display_temp = city_data.current_temp + sim_delta - cooling
    is_simulated = cooling > 0 or abs(sim_delta) > 0.1

    # ── Heat Risk Index ───────────────────────────────────────────────────────
    def compute_heat_risk(temp_c: float, aqi: int) -> tuple[int, str, str]:
        """
        Returns (score 0-100, label, hex_color).

        Temperature thresholds follow WHO / US NWS heat-stress science:
          < 27°C  → minimal risk baseline
          27-32°C → caution zone
          32-38°C → moderate heat stress
          38-42°C → high heat stress
          > 42°C  → extreme / danger

        AQI multiplier (US EPA bands):
          0-50   Good            → ×1.0
          51-100 Moderate        → ×1.10
          101-150 USG            → ×1.20
          151-200 Unhealthy      → ×1.35
          > 200  Very Unhealthy+ → ×1.50
        """
        # --- temperature component (0-100) ---
        breakpoints = [
            (27.0,  0.0),
            (32.0, 25.0),
            (38.0, 60.0),
            (42.0, 85.0),
        ]
        if temp_c <= breakpoints[0][0]:
            temp_score = 0.0
        elif temp_c >= breakpoints[-1][0]:
            temp_score = 100.0
        else:
            for i in range(len(breakpoints) - 1):
                t_lo, s_lo = breakpoints[i]
                t_hi, s_hi = breakpoints[i + 1]
                if t_lo <= temp_c < t_hi:
                    temp_score = s_lo + (s_hi - s_lo) * (temp_c - t_lo) / (t_hi - t_lo)
                    break
            else:
                temp_score = 100.0

        # --- AQI multiplier ---
        if aqi <= 50:
            aqi_mult = 1.00
        elif aqi <= 100:
            aqi_mult = 1.10
        elif aqi <= 150:
            aqi_mult = 1.20
        elif aqi <= 200:
            aqi_mult = 1.35
        else:
            aqi_mult = 1.50

        score = int(min(100, temp_score * aqi_mult))

        # --- label + colour ---
        if score <= 25:
            return score, "Low", "#10b981"       # green
        elif score <= 50:
            return score, "Moderate", "#f59e0b"  # amber
        elif score <= 75:
            return score, "High", "#f97316"      # orange
        else:
            return score, "Extreme", "#ef4444"   # red

    heat_risk_score, heat_risk_label, heat_risk_color = compute_heat_risk(
        display_temp, city_data.current_aqi
    )
    hr_status_color = "#10b981" if is_simulated else "#3b82f6"
    hr_status_label = "Simulated" if is_simulated else "Live"

    with ctrl2:
        st.markdown(
            f"**Heat Risk Index**<br>"
            f"<span style='font-size:1.8em; font-weight:600; color:{heat_risk_color};'>"
            f"{heat_risk_score}/100</span>"
            f"<span style='font-size:0.85em; font-weight:600; color:{heat_risk_color}; margin-left:6px;'>"
            f"{heat_risk_label}</span><br>"
            f"<div style='display: flex; align-items: center; gap: 6px; margin-top: 4px;'>"
            f"<div style='height:8px; width:8px; border-radius:50%; background-color:{hr_status_color}; "
            f"box-shadow: 0 0 6px {hr_status_color}80;'></div>"
            f"<span style='color:{hr_status_color}; font-weight:500;'>{hr_status_label}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with ctrl3:
        status_color = "#10b981" if is_simulated else "#3b82f6"
        status_label = f"{sim_delta - cooling:+.1f}°C (Simulated)" if is_simulated else "Live"

        st.markdown(
            f"**Avg Surface Temp**<br>"
            f"<span style='font-size:1.8em; font-weight:600;'>{display_temp:.1f}°C</span><br>"
            f"<div style='display: flex; align-items: center; gap: 6px; margin-top: 4px;'>"
            f"<div style='height:8px; width:8px; border-radius:50%; background-color:{status_color}; "
            f"box-shadow: 0 0 6px {status_color}80;'></div>"
            f"<span style='color:{status_color}; font-weight:500;'>{status_label}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with ctrl4:
        st.markdown(
            f"**Air Quality Index**<br>"
            f"<span style='font-size:1.8em; font-weight:600;'>{city_data.current_aqi}</span><br>"
            f"<div style='display: flex; align-items: center; gap: 6px; margin-top: 4px;'>"
            f"<div style='height:8px; width:8px; border-radius:50%; background-color:#3b82f6; "
            f"box-shadow: 0 0 6px rgba(59,130,246,0.5);'></div>"
            f"<span style='color:#3b82f6; font-weight:500;'>Live</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Temporal Slider (Precision Sync + NOW Marker)
    from datetime import time as dtime, datetime, timedelta
    current_time = st.session_state.time_of_day
    t_now = get_city_local_time(st.session_state.selected_city_name)
    
    # Inject CSS for the "NOW" marker on the slider track
    now_pct = (t_now.hour * 60 + t_now.minute) / 1440 * 100
    st.markdown(f"""
        <style>
        /* Slider Track Marker for 'NOW' */
        div[data-baseweb="slider"] > div:first-child::after {{
            content: "NOW";
            position: absolute;
            left: {now_pct}%;
            top: -20px;
            font-size: 9px;
            font-weight: 700;
            color: #3b82f6;
            transform: translateX(-50%);
            white-space: nowrap;
        }}
        div[data-baseweb="slider"] > div:first-child::before {{
            content: "";
            position: absolute;
            left: {now_pct}%;
            top: 0;
            bottom: 0;
            width: 2px;
            background-color: #3b82f6;
            z-index: 10;
            box-shadow: 0 0 4px #3b82f6;
        }}
        </style>
    """, unsafe_allow_html=True)

    # Use a slider with 15-minute increments
    t_val = st.slider(
        "Temporal Heat Simulation",
        min_value=dtime(0, 0),
        max_value=dtime(23, 45),
        value=current_time,
        step=timedelta(minutes=15),
        format="HH:mm"
    )
    
    if t_val != current_time:
        st.session_state.time_of_day = t_val
        coords = CITIES[st.session_state.selected_city_name]
        st.session_state.data = fetch_data_with_loading(
            coords["lat"], coords["lon"],
            st.session_state.time_of_day.strftime("%H:%M"),
            st.session_state.selected_city_name,
            f"Simulating regional shift to {t_val.strftime('%H:%M')} for",
            radius_meters=coords.get("radius", 2500),
            existing_data=st.session_state.data,
        )
        city_data = st.session_state.data
        st.rerun()

    # Map Visualization Placeholder
    map_placeholder = st.container()

    d = city_data
    def _layer_toggle(label: str, key: str, has_data: bool) -> None:
        st.toggle(
            label + (" (no data)" if not has_data else ""),
            key=key,
            disabled=not has_data,
        )

    # (Pending logic moved higher up the script to avoid UI mutation lock)

    st.markdown("<p style='font-size: 0.8em; color: #94a3b8; font-weight: 600; margin-bottom: 0; margin-top: 10px;'>MAP LAYERS</p>", unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    with r1:
        _layer_toggle("Thermal", "toggle_thermal", not d.df_thermal.empty)
    with r2:
        _layer_toggle("Air Quality", "toggle_sensors", not d.df_sensors.empty)
    with r3:
        _layer_toggle("Buildings", "toggle_buildings", not d.df_buildings.empty)
        _layer_toggle("Traffic", "toggle_traffic", not d.df_traffic.empty)

    st.markdown("<p style='font-size: 0.8em; color: #94a3b8; font-weight: 600; margin-bottom: 0; margin-top: 10px;'>NATURE & ASSETS</p>", unsafe_allow_html=True)
    n1, n2, n3 = st.columns(3)
    with n1:
        _layer_toggle("Tree Canopy",       "toggle_trees",      not d.df_trees.empty)
        _layer_toggle("Urban Forests",     "toggle_forests",    not d.df_forests.empty)
        _layer_toggle("Community Gardens", "toggle_gardens",    not d.df_gardens.empty)
    with n2:
        _layer_toggle("Water Sources",     "toggle_water",      not d.df_water.empty)
        _layer_toggle("Wetlands",          "toggle_wetlands",   not d.df_wetlands.empty)
        _layer_toggle("Drinking Fountains","toggle_fountains",  not d.df_fountains.empty)
    with n3:
        _layer_toggle("Public Parks",      "toggle_parks",      not d.df_parks.empty)
        _layer_toggle("Green Roofs",       "toggle_green_roofs",not d.df_green_roofs.empty)
        _layer_toggle("Cooling Centers",   "toggle_shelters",   not d.df_shelters.empty)

    with map_placeholder:
        map_config = MapConfig(
            data=city_data,
            toggles=LayerToggles.from_session_state(st.session_state),
            center_lat=CITIES[st.session_state.selected_city_name]["lat"],
            center_lon=CITIES[st.session_state.selected_city_name]["lon"],
            simulations=st.session_state.simulations,
            annotations=st.session_state.map_annotations,
        )
        deck_map = create_map(map_config)
        selection = st.pydeck_chart(
            deck_map,
            on_select="rerun",
            selection_mode="single-object",
            key="main_map",
        )

        # Parse the pydeck selection if valid objects are found
        if hasattr(selection, "selection") and selection.selection.get("objects"):
            objects = selection.selection["objects"]
            for layer_id, objs in objects.items():
                if objs and isinstance(objs, list):
                    obj = objs[0]
                    # Ensure we don't infinitely process the same click
                    asset_id = obj.get("asset_id", obj.get("id", "Unknown"))
                    if st.session_state.get("last_clicked_obj_id") != asset_id:
                        obj_name = obj.get("name", "Urban Asset")
                        st.session_state.pending_map_click = f"Selected {obj_name} ({asset_id})"
                        st.session_state.last_clicked_obj = obj
                        st.session_state.last_clicked_obj_id = asset_id
                        st.rerun()
