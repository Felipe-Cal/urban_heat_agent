import streamlit as st
import time
import random
from datetime import datetime

class AgentSimulator:
    def __init__(self):
        if 'logs' not in st.session_state:
            st.session_state.logs = []
        if 'agent_status' not in st.session_state:
            st.session_state.agent_status = "IDLE"

    def add_log(self, stage, message):
        """Adds a structured log entry."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = {
            "time": timestamp,
            "stage": stage, # SENSE, PLAN, ACT, REASON, REFLECT
            "message": message
        }
        st.session_state.logs.insert(0, entry) # Prepend for latest first

    def simulate_deployment(self):
        """Scenario: Deploy Nervous System"""
        st.session_state.agent_status = "ACTIVE"
        
        # 1. Sense
        self.add_log("SENSE", "Scanning for Data Deserts in Census Tract 242...")
        time.sleep(0.5) 
        
        # 2. Plan
        self.add_log("PLAN", "Identified 8 optimal locations for Solar-IoT nodes.")
        time.sleep(0.5)
        
        # 3. Act
        self.add_log("ACT", "Generating procurement request for open-standard sensors.")
        self.add_log("ACT", "Protocol: VDP-Signed (Verified Data Provenance).")
        
        st.session_state.agent_status = "IDLE"

    def simulate_intervention(self):
        """Scenario: Win-Win Intervention"""
        st.session_state.agent_status = "REASONING"
        
        self.add_log("SENSE", "Surface temp 49°C detected in proximity to schools.")
        time.sleep(0.5)
        
        self.add_log("REASON", "High cardiovascular risk correlated with heat index.")
        time.sleep(0.5)
        
        self.add_log("PLAN", "Strategy: 40 Coast Live Oaks + Reflective Albedo Coating.")
        self.add_log("ROI", "Est. -3.2°C cooling | $1.2k annual energy savings.")
        
        st.session_state.agent_status = "IDLE"

    def simulate_verification(self):
        """Scenario: Verify Green Bond"""
        st.session_state.agent_status = "VERIFYING"
        
        self.add_log("REFLECT", "Comparing 2025 baseline vs 2026 satellite actuals.")
        time.sleep(0.5)
        
        self.add_log("VERIFY", "Intervention #882 reduced peak temp by 2.1°C.")
        self.add_log("BLOCKCHAIN", f"Impact Sealed. Hash: 0x{random.randint(10**10, 10**11)}...31a")
        
        st.session_state.agent_status = "IDLE"
