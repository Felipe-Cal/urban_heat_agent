import streamlit as st
import pandas as pd
import time
from modules.styles import load_css
from modules.data_generator import generate_mock_data
from modules.map_layers import create_map
from modules.agent_logic import AgentSimulator

# 1. Page Config
st.set_page_config(
    page_title="Gaia Heat Sync | LA Bio-Region",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Load "Bio-Minimalism" Styles
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

if 'data' not in st.session_state:
    # Generate initial data for default city
    city = CITIES[st.session_state.selected_city_name]
    st.session_state.data = generate_mock_data(city['lat'], city['lon'])
    
if 'agent' not in st.session_state:
    st.session_state.agent = AgentSimulator()

if 'layer_toggles' not in st.session_state:
    st.session_state.layer_toggles = {
        "thermal": True,
        "trees": False,
        "sensors": False
    }

# Unpack Data
df_thermal, df_trees, df_sensors = st.session_state.data
agent = st.session_state.agent

# --- SIDEBAR (THE PROXY) ---
with st.sidebar:
    st.markdown("### 🧬 Gaia Agent (Beta)")
    st.caption(f"{st.session_state.selected_city_name} Node")
    
    # Status Indicator
    status = st.session_state.get('agent_status', 'IDLE')
    if status != "IDLE":
        st.markdown(f'<div class="status-dot status-active"></div> **Status: {status}**', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-dot" style="background-color: #cbd5e1;"></div> Status: Monitoring', unsafe_allow_html=True)
         
    st.divider()

    # City Selector
    st.markdown("**Bio-Region Node**")
    selected_city = st.selectbox(
        "Select City",
        options=list(CITIES.keys()),
        index=list(CITIES.keys()).index(st.session_state.selected_city_name),
        label_visibility="collapsed"
    )

    # Handle City Change
    if selected_city != st.session_state.selected_city_name:
        st.session_state.selected_city_name = selected_city
        coords = CITIES[selected_city]
        st.session_state.data = generate_mock_data(coords['lat'], coords['lon'])
        st.rerun()

    st.divider()

    # Agent Actions (Scenarios)
    st.markdown("**Autonomous Reasoning Scenarios**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Deploy\nNerves"):
            agent.simulate_deployment()
            st.session_state.layer_toggles["sensors"] = True # Auto-enable layer
            st.rerun()
            
    with col2:
        if st.button("Win-Win\nIntervention"):
            agent.simulate_intervention()
            st.session_state.layer_toggles["trees"] = True
            st.rerun()
            
    if st.button("Verify Green Bond Impact", use_container_width=True):
        agent.simulate_verification()
        st.rerun()

    st.divider()
    
    # Layer Controls
    st.markdown("**Biosphere Layers**")
    st.session_state.layer_toggles["thermal"] = st.toggle("Thermal Inversion (Landsat)", value=st.session_state.layer_toggles["thermal"])
    st.session_state.layer_toggles["trees"] = st.toggle("Nature ID Canopy", value=st.session_state.layer_toggles["trees"])
    st.session_state.layer_toggles["sensors"] = st.toggle("Sensor Grid (Violet)", value=st.session_state.layer_toggles["sensors"])

    st.divider()
    
    # Streaming Logs
    st.markdown("**Agent Logic Stream**")
    log_container = st.container(height=300)
    for log in st.session_state.logs:
        log_container.markdown(f"**[{log['stage']}]** {log['message']} <span style='color:#94a3b8; font-size:0.8em;'>{log['time']}</span>", unsafe_allow_html=True)


# --- MAIN AREA (THE BIOSPHERE) ---

# Header
col_head, col_metrics = st.columns([2, 1])
with col_head:
    st.title("Gaia Heat Sync")
    st.markdown("Urbit-Style Resilience Cockpit for City Officers.")

with col_metrics:
    # Live Metrics
    m1, m2 = st.columns(2)
    m1.metric("Avg Surface Temp", "38.2°C", "1.2°C")
    m2.metric("Active Agents", "1,204", "+8")

# Map Visualization
deck_map = create_map(
    df_thermal, 
    df_trees, 
    df_sensors,
    st.session_state.layer_toggles["thermal"],
    st.session_state.layer_toggles["trees"],
    st.session_state.layer_toggles["sensors"],
    center_lat=CITIES[st.session_state.selected_city_name]['lat'],
    center_lon=CITIES[st.session_state.selected_city_name]['lon']
)

st.pydeck_chart(deck_map)

# --- INTERACTIVE COMPONENTS (THE SPINE) ---
# Nature ID Drill Down (Simulated via Expander for now as PyDeck click events in Streamlit are tricky without complex callbacks)
# In a full app, we'd capture pydeck_chart selection. Here we simulate "Latest Asset" inspection.

if st.session_state.layer_toggles["trees"]:
    st.markdown("### 🌳 Selected Nature Asset")
    
    # Mock selecting a random tree for demo purposes if none "clicked"
    # In production: st.session_state.get('selected_tree_id')
    selected_tree = df_trees.iloc[0] 
    
    col_card, col_trust = st.columns([2, 1])
    
    with col_card:
        st.markdown(f"""
        <div class="bio-card">
            <h3>{selected_tree['species']}</h3>
            <p><strong>ID:</strong> {selected_tree['tree_id']}</p>
            <p><strong>Health:</strong> <span style="color: #059669;">{selected_tree['health']}</span></p>
            <p><strong>Owner:</strong> {selected_tree['owner']}</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_trust:
        st.markdown("""
        <div class="bio-card" style="border-left: 4px solid #f59e0b;">
            <div style="font-size: 0.8em; color: #64748b; margin-bottom: 4px;">VERIFIABLE DATA PROVENANCE</div>
            <div style="font-weight: 600;">Status: Verified</div>
            <div style="font-size: 0.8em; font-family: monospace; color: #64748b;">Source: Secure Enclave 002</div>
            <div style="margin-top: 8px;">🛡️ <span style="color: #059669;">Signatures Valid</span></div>
        </div>
        """, unsafe_allow_html=True)

