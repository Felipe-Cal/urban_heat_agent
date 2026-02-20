import streamlit as st
from modules.styles import load_css
from modules.data_generator import generate_mock_data
from modules.agent_logic import AgentSimulator
from modules.models import CityData
from modules.state_manager import StateManager
import modules.ui as ui
from dataclasses import replace

# 1. Page Config
st.set_page_config(
    page_title="Gaia Heat Sync | Planetary Intelligence",
    page_icon=":material/bolt:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Load Styles
load_css()

# City Data (Bio-Regions)
CITIES = {
    "Los Angeles, USA":    {"lat": 34.0522,  "lon": -118.2437},
    "New York City, USA":  {"lat": 40.7128,  "lon": -74.0060},
    "London, UK":          {"lat": 51.5074,  "lon": -0.1278},
    "Tokyo, Japan":        {"lat": 35.6762,  "lon": 139.6503},
    "Singapore":           {"lat": 1.3521,   "lon": 103.8198},
    "São Paulo, Brazil":   {"lat": -23.5505, "lon": -46.6333},
    "Mumbai, India":       {"lat": 19.0760,  "lon": 72.8777},
    "Cairo, Egypt":        {"lat": 30.0444,  "lon": 31.2357},
    "Mexico City, Mexico": {"lat": 19.4326,  "lon": -99.1332},
    "Sydney, Australia":   {"lat": -33.8688, "lon": 151.2093},
}

# 3. Initialize Session State
StateManager.initialize()

def fetch_data_with_loading(lat, lon, time_of_day, city_name, action_desc) -> CityData:
    progress_bar = st.progress(0, text=f"{action_desc} ({city_name})...")

    def update_progress(msg, pct):
        progress_bar.progress(pct, text=f"{action_desc} ({city_name}) - {msg}")

    data = generate_mock_data(lat, lon, time_of_day, progress_callback=update_progress)
    progress_bar.empty()
    StateManager.set("data", data)
    return data

# Load data on first run (or if session data is missing / wrong type)
city_data = StateManager.get("data")
if not isinstance(city_data, CityData):
    selected_city_name = StateManager.get("selected_city_name")
    city = CITIES[selected_city_name]
    city_data = fetch_data_with_loading(
        city["lat"], city["lon"],
        StateManager.get("time_of_day"),
        selected_city_name,
        "Initializing Gaia Node",
    )

agent = StateManager.get("agent")
if not agent:
    agent = AgentSimulator()
    StateManager.set("agent", agent)

# Display any deferred OSM fetch errors as toasts
if city_data.fetch_error:
    st.toast(city_data.fetch_error, icon="🚨")
    # Clear by replacing with a copy that has fetch_error=None
    new_data = replace(city_data, fetch_error=None)
    StateManager.set("data", new_data)
    city_data = new_data

# --- MAIN LAYOUT ---
ui.render_header()

# 40% Left (Agent), 60% Right (Map)
col_agent, col_map = st.columns([4, 6], gap="large")

with col_agent:
    ui.render_agent_interface(agent)

with col_map:
    ui.render_dashboard_column(city_data, CITIES, fetch_data_with_loading)
