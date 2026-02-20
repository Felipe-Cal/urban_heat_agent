import streamlit as st
import pandas as pd
import time
from modules.styles import load_css
from modules.data_generator import generate_mock_data
from modules.map_layers import create_map
from modules.agent_logic import AgentSimulator

# 1. Page Config
st.set_page_config(
    page_title="Gaia Heat Sync | Planetary Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed" # Hide sidebar entirely
)

# 2. Load "Electric" Styles
load_css()

# City Data (Bio-Regions)
CITIES = {
    "Los Angeles, USA": {"lat": 34.0522, "lon": -118.2437},
    "New York City, USA": {"lat": 40.7128, "lon": -74.0060},
    "London, UK": {"lat": 51.5074, "lon": -0.1278},
    "Tokyo, Japan": {"lat": 35.6762, "lon": 139.6503},
    "Singapore": {"lat": 1.3521, "lon": 103.8198},
    "São Paulo, Brazil": {"lat": -23.5505, "lon": -46.6333},
    "Mumbai, India": {"lat": 19.0760, "lon": 72.8777},
    "Cairo, Egypt": {"lat": 30.0444, "lon": 31.2357},
    "Mexico City, Mexico": {"lat": 19.4326, "lon": -99.1332},
    "Sydney, Australia": {"lat": -33.8688, "lon": 151.2093}
}

# 3. Initialize Session State
if 'selected_city_name' not in st.session_state:
    st.session_state.selected_city_name = "Los Angeles, USA"

if 'time_of_day' not in st.session_state:
    st.session_state.time_of_day = "14:00"
    
if 'pending_map_click' not in st.session_state:
    st.session_state.pending_map_click = None
    
if 'last_clicked_asset' not in st.session_state:
    st.session_state.last_clicked_asset = None

if 'sandbox_mode' not in st.session_state:
    st.session_state.sandbox_mode = False
if 'simulations' not in st.session_state:
    st.session_state.simulations = []
if 'simulated_cooling' not in st.session_state:
    st.session_state.simulated_cooling = 0.0

def fetch_data_with_loading(lat, lon, time_of_day, city_name, action_desc):
    progress_bar = st.progress(0, text=f"{action_desc} ({city_name})...")
    
    def update_progress(msg, pct):
        progress_bar.progress(pct, text=f"{action_desc} ({city_name}) - {msg}")
        
    data = generate_mock_data(lat, lon, time_of_day, progress_callback=update_progress)
    progress_bar.empty()
    return data

if 'data' not in st.session_state or len(st.session_state.data) != 19:
    city = CITIES[st.session_state.selected_city_name]
    st.session_state.data = fetch_data_with_loading(city['lat'], city['lon'], st.session_state.time_of_day, st.session_state.selected_city_name, "Initializing Gaia Node")
    
if 'agent' not in st.session_state:
    st.session_state.agent = AgentSimulator()

if 'layer_toggles' not in st.session_state:
    st.session_state.layer_toggles = {
        "thermal": True,
        "trees": False,
        "water": False,
        "parks": False,
        "shelters": False,
        "fountains": False,
        "green_roofs": False,
        "gardens": False,
        "forests": False,
        "wetlands": False,
        "sensors": False,
        "ndvi": False,
        "albedo": False,
        "buildings": False,
        "traffic": False,
        "population": False
    }

# Unpack Data
df_thermal, df_trees, df_water, df_parks, df_shelters, df_fountains, df_green_roofs, df_gardens, df_forests, df_wetlands, df_sensors, df_ndvi, df_albedo, df_buildings, df_traffic, df_population, resilience_score, current_temp, current_aqi = st.session_state.data
agent = st.session_state.agent

# --- MAIN LAYOUT ---
# 40% Left (Agent), 60% Right (Map)
col_agent, col_map = st.columns([4, 6], gap="large")

# ==========================================
# LEFT COLUMN: THE AGENT (THE PROXY)
# ==========================================
with col_agent:
    st.markdown("### ⚡ Gaia Agent")
    st.caption(f"System Node: {st.session_state.selected_city_name}")
    
    # Status Indicator
    status = st.session_state.get('agent_status', 'IDLE')
    if status != "IDLE":
        st.markdown(f'<div class="status-dot status-active"></div> **Status: {status}**', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-dot" style="background-color: #333;"></div> Status: Listening', unsafe_allow_html=True)
         
    st.divider()

    # Chat History Container (Scrollable)
    chat_container = st.container(height=500, border=False)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"], unsafe_allow_html=True)

    # Agent Action Shortcuts
    st.markdown("<p style='font-size: 0.8em; color: #888;'>SUGGESTED ACTIONS</p>", unsafe_allow_html=True)
    btn1, btn2, btn3 = st.columns(3)
    
    with btn1:
        if st.button("Scan for\nData Desserts", use_container_width=True):
            agent.simulate_deployment()
            st.session_state.layer_toggles["sensors"] = True
            st.rerun()
    with btn2:
        if st.button("Detect Thermal\nRisk Areas", use_container_width=True):
            agent.simulate_intervention()
            st.session_state.layer_toggles["trees"] = True
            st.rerun()
    with btn3:
        if st.session_state.sandbox_mode:
            if st.button("🔴 Exit\nSandbox", use_container_width=True):
                st.session_state.sandbox_mode = False
                st.session_state.simulations = []
                st.session_state.simulated_cooling = 0.0
                st.rerun()
        else:
            if st.button("🌱 Launch\nSandbox", use_container_width=True):
                st.session_state.sandbox_mode = True
                st.rerun()
                
    if st.session_state.sandbox_mode:
        st.info("🌱 **Sandbox Active:** Click on any building or road on the map to simulate a cooling intervention.")
        if len(st.session_state.simulations) > 0:
            if st.button("🗑️ Clear Interventions", use_container_width=True):
                st.session_state.simulations = []
                st.session_state.simulated_cooling = 0.0
                st.rerun()
            
    if st.button("📄 Generate Briefing Report", use_container_width=True, type="primary"):
        st.session_state.generating_pdf = True
        st.rerun()

    if st.session_state.get('generating_pdf', False):
        with st.spinner("Generating Professional PDF Briefing..."):
            pdf_bytes = agent.generate_pdf_report()
            if pdf_bytes:
                st.session_state.pdf_ready = pdf_bytes
            st.session_state.generating_pdf = False
            st.rerun()

    if 'pdf_ready' in st.session_state:
        city_slug = st.session_state.selected_city_name.split(',')[0].replace(' ', '_')
        st.download_button(
            label="⬇️ Download PDF Briefing",
            data=st.session_state.pdf_ready,
            file_name=f"Gaia_Briefing_{city_slug}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )

    # Process Pending Map Clicks
    if st.session_state.pending_map_click:
        prompt = st.session_state.pending_map_click
        obj = st.session_state.last_clicked_obj
        st.session_state.pending_map_click = None
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt, unsafe_allow_html=True)
            with st.chat_message("assistant"):
                if st.session_state.sandbox_mode and obj:
                    agent.simulate_intervention_on_asset(obj)
                else:
                    agent.process_custom_query(prompt)

    # Generic Chat Input
    if prompt := st.chat_input("Ask Gaia to analyze regions, verify data, or propose interventions..."):
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt, unsafe_allow_html=True)
            with st.chat_message("assistant"):
                agent.process_custom_query(prompt)
        st.rerun()

# ==========================================
# RIGHT COLUMN: THE BIOSPHERE (MAP & DATA)
# ==========================================
with col_map:
    # Header Control Bar
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 1, 1, 1])
    
    with ctrl1:
        # City Selector
        selected_city = st.selectbox(
            "📍 Active Bio-Region",
            options=list(CITIES.keys()),
            index=list(CITIES.keys()).index(st.session_state.selected_city_name),
            label_visibility="collapsed"
        )
        if selected_city != st.session_state.selected_city_name:
            st.session_state.selected_city_name = selected_city
            coords = CITIES[selected_city]
            st.session_state.data = fetch_data_with_loading(coords['lat'], coords['lon'], st.session_state.time_of_day, selected_city, "Establishing connection to")
            st.rerun()
            
    with ctrl2:
        bonus_score = int(len(st.session_state.simulations) * 1.5)
        st.metric("Resilience Score", f"{resilience_score + bonus_score}/100", f"+{bonus_score} pts" if bonus_score > 0 else "")
    with ctrl3:
        cooling = st.session_state.simulated_cooling
        delta = f"-{cooling:.1f}°C" if cooling > 0 else "Live"
        delta_color = "normal" if cooling > 0 else "off"
        st.metric("Avg Surface Temp", f"{current_temp - cooling:.1f}°C", delta, delta_color=delta_color)
    with ctrl4:
        st.metric("Air Quality Index", f"AQI {current_aqi}", "Live")
        
    # --- TEMPORAL SLIDER ---
    current_hour = int(st.session_state.time_of_day.split(":")[0])
    time_val = st.slider("Temporal Heat Simulation", min_value=0, max_value=23, value=current_hour, format="%02d:00")
    if time_val != current_hour:
        st.session_state.time_of_day = f"{time_val:02d}:00"
        coords = CITIES[st.session_state.selected_city_name]
        st.session_state.data = fetch_data_with_loading(coords['lat'], coords['lon'], st.session_state.time_of_day, st.session_state.selected_city_name, f"Simulating regional shift to {time_val:02d}:00 for")
        st.rerun()

    # Map Visualization
    deck_map = create_map(
        df_thermal, 
        df_trees,
        df_water,
        df_parks,
        df_shelters,
        df_fountains,
        df_green_roofs,
        df_gardens,
        df_forests,
        df_wetlands,
        df_sensors,
        df_ndvi,
        df_albedo,
        df_buildings,
        df_traffic,
        df_population,
        st.session_state.layer_toggles["thermal"],
        st.session_state.layer_toggles["trees"],
        st.session_state.layer_toggles["water"],
        st.session_state.layer_toggles["parks"],
        st.session_state.layer_toggles["shelters"],
        st.session_state.layer_toggles["fountains"],
        st.session_state.layer_toggles["green_roofs"],
        st.session_state.layer_toggles["gardens"],
        st.session_state.layer_toggles["forests"],
        st.session_state.layer_toggles["wetlands"],
        st.session_state.layer_toggles["sensors"],
        st.session_state.layer_toggles["ndvi"],
        st.session_state.layer_toggles["albedo"],
        st.session_state.layer_toggles["buildings"],
        st.session_state.layer_toggles["traffic"],
        st.session_state.layer_toggles["population"],
        center_lat=CITIES[st.session_state.selected_city_name]['lat'],
        center_lon=CITIES[st.session_state.selected_city_name]['lon']
    )

    selection = st.pydeck_chart(deck_map, on_select="rerun", selection_mode="single-object", key="main_map")
    
    if selection and selection.get("selection") and selection["selection"].get("objects"):
        objects_dict = selection["selection"]["objects"]
        obj = None
        for layer_objects in objects_dict.values():
            if layer_objects:
                obj = layer_objects[0]
                break
                
        if obj:
            asset_id = obj.get('asset_id') or obj.get('sensor_id')
            name = obj.get('name') or "Sensor Node"
            asset_type = obj.get('type') or "System Telemetry"
            
            if asset_id and st.session_state.last_clicked_asset != asset_id:
                st.session_state.last_clicked_asset = asset_id
                st.session_state.last_clicked_obj = obj
                
                if st.session_state.sandbox_mode:
                    st.session_state.pending_map_click = f"**[SANDBOX]** Simulate an intervention for **{name}** (Type: {asset_type})."
                else:
                    st.session_state.pending_map_click = f"**[MAP EVENT]** I just clicked on: **{name}** (ID: `{asset_id}`, Type: `{asset_type}`). Analyze it for me."
                st.rerun()

    # --- LAYER TOGGLES ---
    st.markdown("<p style='font-size: 0.8em; color: #10b981; margin-bottom: 0; margin-top: 10px;'>SATELLITE INDICES</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.layer_toggles["thermal"] = st.toggle("Thermal Heatmap", value=st.session_state.layer_toggles["thermal"])
    with c2:
        st.session_state.layer_toggles["ndvi"] = st.toggle("NDVI (Vegetation)", value=st.session_state.layer_toggles["ndvi"])
    with c3:
        st.session_state.layer_toggles["albedo"] = st.toggle("Albedo (Reflectance)", value=st.session_state.layer_toggles["albedo"])
        
    st.markdown("<p style='font-size: 0.8em; color: #10b981; margin-bottom: 0; margin-top: 10px;'>PHYSICAL SENSORS</p>", unsafe_allow_html=True)
    st.session_state.layer_toggles["sensors"] = st.toggle("Air Quality Nodes", value=st.session_state.layer_toggles["sensors"])
    
    st.markdown("<p style='font-size: 0.8em; color: #ff0055; margin-bottom: 0; margin-top: 10px;'>URBAN DRIVERS & VULNERABILITY</p>", unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3)
    with d1:
        st.session_state.layer_toggles["population"] = st.toggle("Population Density", value=st.session_state.layer_toggles["population"])
    with d2:
        st.session_state.layer_toggles["buildings"] = st.toggle("Building Mass", value=st.session_state.layer_toggles["buildings"])
    with d3:
        st.session_state.layer_toggles["traffic"] = st.toggle("Traffic Arteries", value=st.session_state.layer_toggles["traffic"])
        
    st.markdown("<p style='font-size: 0.8em; color: #10b981; margin-bottom: 0; margin-top: 10px;'>NATURE ID ASSETS</p>", unsafe_allow_html=True)
    n1, n2, n3 = st.columns(3)
    with n1:
        st.session_state.layer_toggles["trees"] = st.toggle("Tree Canopy", value=st.session_state.layer_toggles["trees"])
        st.session_state.layer_toggles["forests"] = st.toggle("Urban Forests", value=st.session_state.layer_toggles["forests"])
        st.session_state.layer_toggles["gardens"] = st.toggle("Community Gardens", value=st.session_state.layer_toggles["gardens"])
    with n2:
        st.session_state.layer_toggles["water"] = st.toggle("Water Sources", value=st.session_state.layer_toggles["water"])
        st.session_state.layer_toggles["wetlands"] = st.toggle("Wetlands", value=st.session_state.layer_toggles["wetlands"])
        st.session_state.layer_toggles["fountains"] = st.toggle("Drinking Fountains", value=st.session_state.layer_toggles["fountains"])
    with n3:
        st.session_state.layer_toggles["parks"] = st.toggle("Public Parks", value=st.session_state.layer_toggles["parks"])
        st.session_state.layer_toggles["green_roofs"] = st.toggle("Green Roofs", value=st.session_state.layer_toggles["green_roofs"])
        st.session_state.layer_toggles["shelters"] = st.toggle("Cooling Centers", value=st.session_state.layer_toggles["shelters"])


