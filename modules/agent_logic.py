import streamlit as st
import time
import random
import re
import os
import hashlib
import tempfile
from datetime import datetime
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from markdown_pdf import Section, MarkdownPdf
except ImportError:
    MarkdownPdf = None

try:
    from modules.database import save_ledger_entry, init_db
except ImportError:
    try:
        from database import save_ledger_entry, init_db
    except ImportError:
        save_ledger_entry = None
        init_db = None

class AgentSimulator:
    def __init__(self):
        if 'chat_history' not in st.session_state:
            # Initial greeting
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Initializing Gaia Node... ready for queries."}
            ]
        if 'agent_status' not in st.session_state:
            st.session_state.agent_status = "IDLE"
        # Ensure DB tables exist on every agent init
        if init_db:
            try:
                init_db()
            except Exception:
                pass

    def get_client(self):
        """Lazy load the OpenAI client to handle hot-reloaded secrets."""
        if not OpenAI:
            return None
        
        # Check root level
        if "OPENAI_API_KEY" in st.secrets:
            return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            
        # Check if accidentally placed under [mapbox]
        if "mapbox" in st.secrets and "OPENAI_API_KEY" in st.secrets["mapbox"]:
            return OpenAI(api_key=st.secrets["mapbox"]["OPENAI_API_KEY"])
            
        return None

    def add_message(self, role, content):
        """Adds a message to the chat history."""
        st.session_state.chat_history.append({"role": role, "content": content})

    def simulate_deployment(self):
        """Scenario: Deploy Nervous System"""
        self.add_message("user", "Scan for Data Desserts")
        st.session_state.agent_status = "ACTIVE"
        
        response = f"""
        <div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>
        **[SENSE]** Scanning for Data Deserts in Census Tract 242...<br>
        **[PLAN]** Identified 8 optimal locations for Solar-IoT nodes.<br>
        **[ACT]** Generating procurement request for open-standard sensors.<br>
        **[ACT]** Protocol: VDP-Signed (Verified Data Provenance).
        </div>
        Deployment sequence initiated. Activating Sensor Grid overlay.
        """
        self.add_message("assistant", response)
        st.session_state.agent_status = "IDLE"

    def simulate_intervention(self):
        """Scenario: Win-Win Intervention"""
        self.add_message("user", "Detect Thermal Risk Areas")
        st.session_state.agent_status = "REASONING"
        
        response = f"""
        <div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>
        **[SENSE]** Surface temp 49°C detected in proximity to schools.<br>
        **[REASON]** High cardiovascular risk correlated with heat index.<br>
        **[PLAN]** Strategy: 40 Coast Live Oaks + Reflective Albedo Coating.<br>
        **[ROI]** Est. -3.2°C cooling | $1.2k annual energy savings.
        </div>
        Risk area detected. Proposing biological intervention. Activating Nature ID overlay.
        """
        self.add_message("assistant", response)
        st.session_state.agent_status = "IDLE"

    def auto_analyze_region(self):
        """Scenario: Auto-Analyze and suggest top interventions."""
        self.add_message("user", ":material/bolt: Auto-Analyze Region for Optimal Interventions")
        st.session_state.agent_status = "REASONING"
        
        city = st.session_state.get('selected_city_name', 'This Region')
        
        response = f"""
        <div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>
        **[SENSE]** Scanning {city} for extreme thermal anomalies and vulnerable populations.<br>
        **[REASON]** Correlating heat islands with lacking tree canopy and high density.<br>
        **[PLAN]** Generated 3 optimal interventions localized for maximum impact.
        </div>
        **Top Suggested Interventions:**
        1. **Urban Forest Injection (Zone A):** +500 Trees near Highway Corridor. Est Cooling: -1.2°C.
        2. **Albedo Modification (Zone B):** 20,000 sq ft of white roofs in dense commercial center. Est Cooling: -0.8°C.
        3. **Emergency Cooling Center (Zone C):** Deploy active hydration/shelter node in highest risk tract.
        
        *Activating relevant layers for visual confirmation.*
        """
        self.add_message("assistant", response)
        st.session_state.agent_status = "IDLE"

    def simulate_intervention_on_asset(self, obj):
        """Sandbox Scenario: Intervene on a specific map asset"""
        asset_id = obj.get('asset_id', 'Unknown')
        name = obj.get('name', 'Urban Asset')
        asset_type = obj.get('type', 'Concrete Mass')
        lat = obj.get('lat', 34.05)
        lon = obj.get('lon', -118.24)
        
        self.add_message("user", f"**[SANDBOX]** Propose a cooling intervention for {name} ({asset_type}).")
        st.session_state.agent_status = "REASONING"
        
        # Calculate impact based on type
        cooling_offset = 0.0
        energy_savings = 0
        health_impact = 0
        cost = 0
        intervention_name = ""
        color = [0, 255, 128, 200]
        
        if asset_type == "Concrete Mass":
            intervention_name = "500m² Intensive Green Roof"
            cooling_offset = 0.4
            energy_savings = 12500
            health_impact = 1
            cost = 150000
            color = [163, 230, 53, 255] # Lime green
        elif asset_type in ["Motorway", "Trunk", "Primary", "Road"] or "Transit" in name:
            intervention_name = "Bioswale & Canopy Corridor"
            cooling_offset = 0.7
            energy_savings = 8400
            health_impact = 3
            cost = 300000
            color = [21, 128, 61, 255] # Forest green
        else:
            intervention_name = "Standard Albedo Enhancement"
            cooling_offset = 0.2
            energy_savings = 5000
            health_impact = 0
            cost = 50000
            color = [56, 189, 248, 255] # Sky blue
            
        # Add to state
        st.session_state.simulated_cooling += cooling_offset
        if 'sandbox_budget' in st.session_state:
            st.session_state.sandbox_budget -= cost
            
        st.session_state.simulations.append({
            'lat': lat,
            'lon': lon,
            'name': intervention_name,
            'target': name,
            'cooling': cooling_offset,
            'color': color,
            'radius': 250,
            'tooltip': f"<b style='font-size: 14px; color: #3b82f6;'>Simulated Intervention</b><br/><span style='color:#94a3b8; font-size:11px;'>Target: {name}</span><br/><br/><b>Installed:</b> {intervention_name}<br/><b>Cooling Effect:</b> -{cooling_offset:.1f}°C<br/><b>Health Impact:</b> {health_impact} ER visits avoided<br/><b>Cost:</b> ${cost:,.0f}"
        })
        
        # --- Deterministic SHA-256 Nature ID Hash ---
        # Tied to the actual data: same intervention on same asset always produces the same hash.
        hash_payload = f"{name}|{intervention_name}|{lat:.4f}|{lon:.4f}|{cooling_offset:.2f}|{cost:.0f}"
        nature_id_hash = "0x" + hashlib.sha256(hash_payload.encode()).hexdigest()[:16]
        
        city = st.session_state.get('selected_city_name', 'Unknown')
        
        # Persist to SQLite (survives page refresh)
        if save_ledger_entry:
            try:
                save_ledger_entry(
                    nature_id_hash=nature_id_hash,
                    city=city,
                    target_asset=name,
                    intervention=intervention_name,
                    cooling_impact=f"-{cooling_offset:.1f}",
                    cost=cost,
                )
            except Exception:
                pass  # Non-fatal: still update session_state below

        if 'green_ledger' not in st.session_state:
            st.session_state.green_ledger = []
            
        st.session_state.green_ledger.append({
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Nature ID": nature_id_hash,
            "City": city,
            "Target Asset": name,
            "Intervention": intervention_name,
            "Cooling Impact (°C)": f"-{cooling_offset:.1f}",
            "Cost ($)": f"${cost:,.0f}",
            "Status": "Verified ✅"
        })
        
        response = f"""
        <div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>
        **[ANALYZE]** Target: {name} (Surface type: {asset_type}) at {lat:.4f}, {lon:.4f}<br>
        **[PROPOSE]** Intervention: {intervention_name} | Cost: ${cost:,.0f}<br>
        **[ROI: GRID]** Est. Annual Savings: ${energy_savings:,}<br>
        **[ROI: HEALTH]** Est. ER Visits Prevented: {health_impact}<br>
        **[ROI: CLIMATE]** Est. Local Cooling: -{cooling_offset:.1f}°C<br>
        **[MINT]** Nature ID Generated: `{nature_id_hash}` (Submitting to Green Ledger)
        </div>
        Intervention simulated and Nature ID minted. The dashboard has been updated to reflect the new state.
        """
        self.add_message("assistant", response)
        st.session_state.agent_status = "IDLE"

    def simulate_verification(self):
        """Scenario: Verify Green Bond"""
        self.add_message("user", "Verify Green Bond Impact")
        st.session_state.agent_status = "VERIFYING"
        
        # Deterministic hash tied to verification event data
        city = st.session_state.get('selected_city_name', 'Unknown')
        verify_payload = f"VERIFY|{city}|Intervention#882|2.1C|2026-baseline"
        hash_val = "0x" + hashlib.sha256(verify_payload.encode()).hexdigest()[:20]
        
        response = """
        <div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>
        **[REFLECT]** Comparing 2025 baseline vs 2026 satellite actuals.<br>
        **[VERIFY]** Intervention #882 reduced peak temp by 2.1°C.<br>
        **[BLOCKCHAIN]** Impact Sealed. Hash: HASH_VALUE_PLACEHOLDER
        </div>
        Verification complete. Impact cryptographically secured to the Green Ledger.
        """.replace("HASH_VALUE_PLACEHOLDER", hash_val)
        self.add_message("assistant", response)
        st.session_state.agent_status = "IDLE"

    def process_custom_query(self, query):
        """Handle arbitrary user input"""
        self.add_message("user", query)
        st.session_state.agent_status = "REASONING"
        
        client = self.get_client()
        if client:
            city = st.session_state.get('selected_city_name', 'Unknown City')
            
            temp = "Unknown"
            resilience = "Unknown"
            if "data" in st.session_state:
                try:
                    # In data_generator: return df_thermal, ..., resilience_score, current_temp, current_aqi
                    temp = st.session_state.data[-2]
                    resilience = st.session_state.data[-3]
                except Exception:
                    pass
                    
            all_layers = ["thermal", "trees", "water", "parks", "shelters", "fountains", "green_roofs", "gardens", "forests", "wetlands", "sensors", "ndvi", "albedo", "buildings", "traffic", "population"]
            active_layers = [k for k in all_layers if st.session_state.get(f"toggle_{k}", False)]
            layers_str = ", ".join(active_layers) if active_layers else "None"
            
            system_prompt_text = (
                "You are the Gaia Heat Sync Agent, a Planetary Intelligence system focused on urban resilience for the CITY_PLACEHOLDER Bio-Region Node. "
                "Tone: technical and concise. "
                "CURRENT CONTEXT: Avg Surface Temp: TEMP_PLACEoC | Resilience Score: RESILIENCE_PLACE/100 | Active Map Layers: LAYERS_PLACE. "
                "MAP LAYER RULES: When a user asks to activate a layer, include the EXACT tag [ACTION: ACTIVATE_{LAYER_NAME}]. "
                "To deactivate, use [ACTION: DEACTIVATE_{LAYER_NAME}]. "
                "FULL LIST of valid layer names (use exact spelling): "
                "THERMAL (surface temperature heatmap), "
                "NDVI (vegetation index/plant health), "
                "ALBEDO (surface reflectance/reflectivity - completely different from thermal), "
                "SENSORS (air quality IoT sensor nodes), "
                "TREES (urban tree canopy), WATER (water bodies), PARKS (public parks), "
                "SHELTERS (cooling shelters), FOUNTAINS (drinking fountains), "
                "GREEN_ROOFS (green roof installations), GARDENS (community gardens), "
                "FORESTS (urban forests), WETLANDS (wetland areas), "
                "BUILDINGS (building mass/footprints), TRAFFIC (traffic arteries), POPULATION (population density). "
                "IMPORTANT: If asked for albedo specifically, always use [ACTION: ACTIVATE_ALBEDO] — never substitute with thermal or any other layer."
            )
            system_prompt = {
                "role": "system",
                "content": system_prompt_text.replace("CITY_PLACEHOLDER", city).replace("TEMP_PLACE", str(temp)).replace("RESILIENCE_PLACE", str(resilience)).replace("LAYERS_PLACE", layers_str)
            }
            
            # Prepare messages
            messages = [system_prompt]
            for msg in st.session_state.chat_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
                
            try:
                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=600,
                    stream=True
                )
                
                def generate():
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            yield chunk.choices[0].delta.content
                            
                assistant_response = st.write_stream(generate())
                self.add_message("assistant", assistant_response)
                
                # Parse Map Actions
                actions = re.findall(r'\[ACTION:\s*(ACTIVATE|DEACTIVATE)_([A-Z_]+)\]', assistant_response)
                for action_type, layer_name in actions:
                    layer_key = layer_name.lower()
                    expected_key = f"toggle_{layer_key}"
                    if expected_key in st.session_state:
                        st.session_state[expected_key] = (action_type == "ACTIVATE")
            except Exception as e:
                st.error(f"*[Connection Error]* Failed to reach Gaia Central Node.")
                self.add_message("assistant", f"**:material/error: [Connection Error]** Failed to reach Gaia Central Node: {str(e)}")
        else:
            time.sleep(1) # Fake processing time
            response = f"Simulated response to: '{query}'. (OpenAI API key not configured in secrets.toml)."
            st.markdown(response)
            self.add_message("assistant", response)
            
        st.session_state.agent_status = "IDLE"

    def generate_pdf_report(self):
        """Generates a markdown report via LLM and converts it to a PDF."""
        st.session_state.agent_status = "GENERATING REPORT"
        client = self.get_client()
        if not client or not MarkdownPdf:
            st.session_state.agent_status = "IDLE"
            return None
            
        city = st.session_state.get('selected_city_name', 'Unknown City')
        
        temp = "Unknown"
        resilience = "Unknown"
        if "data" in st.session_state:
            try:
                temp = st.session_state.data[-2]
                resilience = st.session_state.data[-3]
            except Exception:
                pass
                
        all_layers = ["thermal", "trees", "water", "parks", "shelters", "fountains", "green_roofs", "gardens", "forests", "wetlands", "sensors", "ndvi", "albedo", "buildings", "traffic", "population"]
        active_layers = [k for k in all_layers if st.session_state.get(f"toggle_{k}", False)]
        layers_str = ", ".join(active_layers) if active_layers else "None"
        
        system_prompt_text = "You are the Gaia Heat Sync Agent. CURRENT SYSTEM CONTEXT - Avg Surface Temp: TEMP_PLACE°C | Resilience Score: RESILIENCE_PLACE/100 | Active Map Layers: LAYERS_PLACE."
        system_prompt = {
            "role": "system",
            "content": system_prompt_text.replace("TEMP_PLACE", str(temp)).replace("RESILIENCE_PLACE", str(resilience)).replace("LAYERS_PLACE", layers_str)
        }
        
        # We only need to prompt the LLM to generate the report
        messages = [
            system_prompt,
            {"role": "user", "content": f"Generate a formal bio-regional resilience briefing based on the current dashboard context for the {city} Bio-Region Node. Format as a professional Markdown report. Do not use any map control actions, just return the report text."}
        ]
            
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            markdown_content = response.choices[0].message.content
            
            # Convert to PDF
            pdf = MarkdownPdf(toc_level=0)
            pdf.add_section(Section(markdown_content, toc=False))
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                temp_pdf_path = tmp.name

            pdf.save(temp_pdf_path)
            
            with open(temp_pdf_path, "rb") as f:
                pdf_bytes = f.read()
                
            os.remove(temp_pdf_path)
            st.session_state.agent_status = "IDLE"
            return pdf_bytes
            
        except Exception as e:
            st.error(f"Failed to generate PDF Report: {e}")
            st.session_state.agent_status = "IDLE"
            return None
