import random
import streamlit as st
import pandas as pd
import time
from modules.styles import load_css
from modules.data_generator import generate_mock_data
from modules.map_layers import create_map
from modules.agent_logic import AgentSimulator
from modules.models import CityData, LayerToggles, MapConfig

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
_state_defaults = {
    "selected_city_name": "Los Angeles, USA",
    "time_of_day":        "14:00",
    "pending_map_click":  None,
    "last_clicked_asset": None,
    "last_clicked_obj":   None,          # Fix #4: was missing
    "sandbox_mode":       False,
    "simulations":        [],
    "simulated_cooling":  0.0,
    "sandbox_budget":     5_000_000.0,
    "green_ledger":       [],
    "generating_pdf":     False,
}
for key, default in _state_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Layer toggles — all off by default
_ALL_LAYERS = [
    "thermal", "trees", "water", "parks", "shelters", "fountains",
    "green_roofs", "gardens", "forests", "wetlands", "sensors",
    "ndvi", "albedo", "buildings", "traffic", "population",
]
for layer in _ALL_LAYERS:
    if f"toggle_{layer}" not in st.session_state:
        st.session_state[f"toggle_{layer}"] = False


def fetch_data_with_loading(lat, lon, time_of_day, city_name, action_desc) -> CityData:
    progress_bar = st.progress(0, text=f"{action_desc} ({city_name})...")

    def update_progress(msg, pct):
        progress_bar.progress(pct, text=f"{action_desc} ({city_name}) - {msg}")

    data = generate_mock_data(lat, lon, time_of_day, progress_callback=update_progress)
    progress_bar.empty()
    return data


# Load data on first run (or if session data is missing / wrong type)
if "data" not in st.session_state or not isinstance(st.session_state.data, CityData):
    city = CITIES[st.session_state.selected_city_name]
    st.session_state.data = fetch_data_with_loading(
        city["lat"], city["lon"],
        st.session_state.time_of_day,
        st.session_state.selected_city_name,
        "Initializing Gaia Node",
    )

if "agent" not in st.session_state:
    st.session_state.agent = AgentSimulator()

# Unpack data fields by name — no positional indexing
city_data: CityData = st.session_state.data
agent: AgentSimulator = st.session_state.agent

# Display any deferred OSM fetch errors as toasts
if st.session_state.data.fetch_error:
    st.toast(st.session_state.data.fetch_error, icon="🚨")
    # Clear by replacing with a copy that has fetch_error=None
    from dataclasses import replace
    st.session_state.data = replace(st.session_state.data, fetch_error=None)
    city_data = st.session_state.data

# --- MAIN LAYOUT ---
# Theme Toggle at Top Right — pure CSS approach (no config.toml writes)
t1, t2 = st.columns([95, 5])
with t2:
    light_mode = st.session_state.get("light_mode", False)
    theme_icon = ":material/dark_mode:" if light_mode else ":material/light_mode:"
    if st.button("", icon=theme_icon, help="Toggle Theme"):
        st.session_state.light_mode = not light_mode
        st.rerun()

# 40% Left (Agent), 60% Right (Map)
col_agent, col_map = st.columns([4, 6], gap="large")

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
                    st.markdown(msg["content"], unsafe_allow_html=True)

        if prompt := st.chat_input("Ask Gaia to analyze regions, verify data, or propose interventions..."):
            with chat_container:
                with st.chat_message("user", avatar=":material/person:"):
                    st.markdown(prompt, unsafe_allow_html=True)
                with st.chat_message("assistant", avatar=":material/smart_toy:"):
                    agent.process_custom_query(prompt)
            st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    # Agent Action Shortcuts
    st.markdown("<p style='font-size: 0.8em; color: #888;'>SUGGESTED ACTIONS</p>", unsafe_allow_html=True)

    if st.button(":material/public: Auto-Analyze Region", use_container_width=True, type="primary"):
        agent.auto_analyze_region()
        st.rerun()

    btn1, btn2, btn3 = st.columns(3)
    with btn1:
        if st.button(":material/radar: Scan for Data Desserts", use_container_width=True):
            agent.simulate_deployment()
            st.session_state.toggle_sensors = True
            st.rerun()
    with btn2:
        if st.button(":material/thermostat: Detect Thermal Risk Areas", use_container_width=True):
            agent.simulate_intervention()
            st.session_state.toggle_trees = True
            st.rerun()
    with btn3:
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

    if st.session_state.sandbox_mode:
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

    if st.button("📄 Generate Briefing Report", use_container_width=True, type="primary"):
        st.session_state.generating_pdf = True
        st.rerun()

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

    # Process Pending Map Clicks
    if st.session_state.pending_map_click:
        prompt = st.session_state.pending_map_click
        obj = st.session_state.last_clicked_obj
        st.session_state.pending_map_click = None

        with chat_container:
            with st.chat_message("user", avatar=":material/person:"):
                st.markdown(prompt, unsafe_allow_html=True)
            with st.chat_message("assistant", avatar=":material/smart_toy:"):
                if st.session_state.sandbox_mode and obj:
                    agent.simulate_intervention_on_asset(obj)
                elif obj:
                    asset_id = obj.get("asset_id", "Unknown")
                    name = obj.get("name", "Urban Asset")
                    asset_type = obj.get("type", "Unknown Type")
                    nature_id_hash = "0x" + "".join(random.choices("0123456789abcdef", k=8)) + "...1f"
                    age = random.randint(5, 80) if "Tree" in asset_type or "Forest" in asset_type else "N/A"
                    c02 = f"{random.randint(10, 500)} kg/yr" if age != "N/A" else "0 kg/yr"
                    cooling_power = f"-{random.uniform(0.1, 2.5):.1f}°C"
                    twin_response = (
                        f"**Digital Twin Profile Loaded:** `{name}`"
                        f"<div style='background-color: var(--background-color, #1e293b); padding: 10px; "
                        f"border-radius: 5px; border-left: 3px solid #3b82f6; margin-top: 10px; "
                        f"margin-bottom: 10px; font-family: monospace;'>"
                        f"<b>Asset Type:</b> {asset_type}<br/>"
                        f"<b>Nature ID Hash:</b> {nature_id_hash}<br/>"
                        f"<b>Est. Age:</b> {age} years<br/>"
                        f"<b>Carbon Seq:</b> {c02}<br/>"
                        f"<b>Local Cooling:</b> <span style='color:#3b82f6;'>{cooling_power}</span><br/>"
                        f"<b>Status:</b> Verified via Satellite"
                        f"</div>"
                        f"I have pulled the biometric profile from the Green Ledger. "
                        f"This asset actively contributes to the '{st.session_state.selected_city_name}' Resilience Score."
                    )
                    agent.add_message("assistant", twin_response)
                    st.markdown(twin_response, unsafe_allow_html=True)
                else:
                    agent.process_custom_query(prompt)

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
            coords = CITIES[selected_city]
            st.session_state.data = fetch_data_with_loading(
                coords["lat"], coords["lon"],
                st.session_state.time_of_day,
                selected_city,
                "Establishing connection to",
            )
            city_data = st.session_state.data
            st.rerun()

    with ctrl2:
        bonus_score = int(len(st.session_state.simulations) * 1.5)
        st.metric(
            "Resilience Score",
            f"{city_data.resilience_score + bonus_score}/100",
            f"+{bonus_score} pts" if bonus_score > 0 else "",
        )
    with ctrl3:
        cooling = st.session_state.simulated_cooling
        if cooling > 0:
            st.markdown(
                f"**Avg Surface Temp**<br>"
                f"<span style='font-size:1.8em; font-weight:600;'>{city_data.current_temp - cooling:.1f}°C</span><br>"
                f"<span style='color:#10b981; font-weight:500;'>-{cooling:.1f}°C (Simulated)</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"**Avg Surface Temp**<br>"
                f"<span style='font-size:1.8em; font-weight:600;'>{city_data.current_temp:.1f}°C</span><br>"
                f"<div style='height:8px; width:8px; border-radius:50%; background-color:#3b82f6; "
                f"display:inline-block; margin-right:4px;'></div>"
                f"<span style='color:#3b82f6; font-weight:500;'>Live</span>",
                unsafe_allow_html=True,
            )
    with ctrl4:
        st.markdown(
            f"**Air Quality Index**<br>"
            f"<span style='font-size:1.8em; font-weight:600;'>AQI {city_data.current_aqi}</span><br>"
            f"<div style='height:8px; width:8px; border-radius:50%; background-color:#3b82f6; "
            f"display:inline-block; margin-right:4px;'></div>"
            f"<span style='color:#3b82f6; font-weight:500;'>Live</span>",
            unsafe_allow_html=True,
        )

    # Temporal Slider
    current_hour = int(st.session_state.time_of_day.split(":")[0])
    time_val = st.slider("Temporal Heat Simulation", min_value=0, max_value=23, value=current_hour, format="%02d:00")
    if time_val != current_hour:
        st.session_state.time_of_day = f"{time_val:02d}:00"
        coords = CITIES[st.session_state.selected_city_name]
        st.session_state.data = fetch_data_with_loading(
            coords["lat"], coords["lon"],
            st.session_state.time_of_day,
            st.session_state.selected_city_name,
            f"Simulating regional shift to {time_val:02d}:00 for",
        )
        city_data = st.session_state.data
        st.rerun()

    # Map Visualization Placeholder
    map_placeholder = st.container()

    # Layer Toggles
    st.markdown("<p style='font-size: 0.8em; color: #94a3b8; font-weight: 600; margin-bottom: 0; margin-top: 10px;'>SATELLITE INDICES</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.toggle("Thermal Heatmap",   key="toggle_thermal")
    with c2: st.toggle("NDVI (Vegetation)", key="toggle_ndvi")
    with c3: st.toggle("Albedo (Reflectance)", key="toggle_albedo")

    st.markdown("<p style='font-size: 0.8em; color: #94a3b8; font-weight: 600; margin-bottom: 0; margin-top: 10px;'>PHYSICAL SENSORS</p>", unsafe_allow_html=True)
    st.toggle("Air Quality Nodes", key="toggle_sensors")

    st.markdown("<p style='font-size: 0.8em; color: #94a3b8; font-weight: 600; margin-bottom: 0; margin-top: 10px;'>URBAN DRIVERS & VULNERABILITY</p>", unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3)
    with d1: st.toggle("Population Density", key="toggle_population")
    with d2: st.toggle("Building Mass",       key="toggle_buildings")
    with d3: st.toggle("Traffic Arteries",    key="toggle_traffic")

    st.markdown("<p style='font-size: 0.8em; color: #94a3b8; font-weight: 600; margin-bottom: 0; margin-top: 10px;'>NATURE ID ASSETS</p>", unsafe_allow_html=True)
    n1, n2, n3 = st.columns(3)
    with n1:
        st.toggle("Tree Canopy",       key="toggle_trees")
        st.toggle("Urban Forests",     key="toggle_forests")
        st.toggle("Community Gardens", key="toggle_gardens")
    with n2:
        st.toggle("Water Sources",     key="toggle_water")
        st.toggle("Wetlands",          key="toggle_wetlands")
        st.toggle("Drinking Fountains",key="toggle_fountains")
    with n3:
        st.toggle("Public Parks",      key="toggle_parks")
        st.toggle("Green Roofs",       key="toggle_green_roofs")
        st.toggle("Cooling Centers",   key="toggle_shelters")

    with map_placeholder:
        map_config = MapConfig(
            data=city_data,
            toggles=LayerToggles.from_session_state(st.session_state),
            center_lat=CITIES[st.session_state.selected_city_name]["lat"],
            center_lon=CITIES[st.session_state.selected_city_name]["lon"],
            simulations=st.session_state.simulations,
        )
        deck_map = create_map(map_config)
        selection = st.pydeck_chart(deck_map, on_select="rerun", selection_mode="single-object", key="main_map_v2")

        if selection and selection.get("selection") and selection["selection"].get("objects"):
            objects_dict = selection["selection"]["objects"]
            obj = None
            for layer_objects in objects_dict.values():
                if layer_objects:
                    obj = layer_objects[0]
                    break

            if obj:
                asset_id = obj.get("asset_id") or obj.get("sensor_id")
                name = obj.get("name") or "Sensor Node"
                asset_type = obj.get("type") or "System Telemetry"

                if asset_id and st.session_state.last_clicked_asset != asset_id:
                    st.session_state.last_clicked_asset = asset_id
                    st.session_state.last_clicked_obj = obj

                    if st.session_state.sandbox_mode:
                        st.session_state.pending_map_click = (
                            f"**[SANDBOX]** Simulate an intervention for **{name}** (Type: {asset_type})."
                        )
                    else:
                        st.session_state.pending_map_click = (
                            f"**[MAP EVENT]** I just clicked on: **{name}** "
                            f"(ID: `{asset_id}`, Type: `{asset_type}`). Analyze it for me."
                        )
                    st.rerun()
