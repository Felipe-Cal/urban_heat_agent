import streamlit as st
import time
import random
import re
import os
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

class AgentSimulator:
    def __init__(self):
        if 'chat_history' not in st.session_state:
            # Initial greeting
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Initializing Gaia Node... ready for queries."}
            ]
        if 'agent_status' not in st.session_state:
            st.session_state.agent_status = "IDLE"

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
        
        response = """
        <div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>
        <span style='color: #00e5ff;'>[SENSE]</span> Scanning for Data Deserts in Census Tract 242...<br>
        <span style='color: #00e5ff;'>[PLAN]</span> Identified 8 optimal locations for Solar-IoT nodes.<br>
        <span style='color: #00e5ff;'>[ACT]</span> Generating procurement request for open-standard sensors.<br>
        <span style='color: #00e5ff;'>[ACT]</span> Protocol: VDP-Signed (Verified Data Provenance).
        </div>
        Deployment sequence initiated. Activating Sensor Grid overlay.
        """
        self.add_message("assistant", response)
        st.session_state.agent_status = "IDLE"

    def simulate_intervention(self):
        """Scenario: Win-Win Intervention"""
        self.add_message("user", "Detect Thermal Risk Areas")
        st.session_state.agent_status = "REASONING"
        
        response = """
        <div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>
        <span style='color: #f59e0b;'>[SENSE]</span> Surface temp 49°C detected in proximity to schools.<br>
        <span style='color: #f59e0b;'>[REASON]</span> High cardiovascular risk correlated with heat index.<br>
        <span style='color: #00e5ff;'>[PLAN]</span> Strategy: 40 Coast Live Oaks + Reflective Albedo Coating.<br>
        <span style='color: #00e5ff;'>[ROI]</span> Est. -3.2°C cooling | $1.2k annual energy savings.
        </div>
        Risk area detected. Proposing biological intervention. Activating Nature ID overlay.
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
        intervention_name = ""
        color = [0, 255, 128, 200]
        
        if asset_type == "Concrete Mass":
            intervention_name = "500m² Intensive Green Roof"
            cooling_offset = 0.4
            energy_savings = 12500
            color = [163, 230, 53, 255] # Lime green
        elif asset_type in ["Motorway", "Trunk", "Primary", "Road"] or "Transit" in name:
            intervention_name = "Bioswale & Canopy Corridor"
            cooling_offset = 0.7
            energy_savings = 8400
            color = [21, 128, 61, 255] # Forest green
        else:
            intervention_name = "Standard Albedo Enhancement"
            cooling_offset = 0.2
            energy_savings = 5000
            color = [56, 189, 248, 255] # Sky blue
            
        # Add to state
        st.session_state.simulated_cooling += cooling_offset
        st.session_state.simulations.append({
            'lat': lat,
            'lon': lon,
            'name': intervention_name,
            'target': name,
            'cooling': cooling_offset,
            'color': color,
            'radius': 250,
            'tooltip': f"<b style='font-size: 14px; color: #10b981;'>Simulated Intervention</b><br/><span style='color:#94a3b8; font-size:11px;'>Target: {name}</span><br/><br/><b>Installed:</b> {intervention_name}<br/><b>Cooling Effect:</b> -{cooling_offset:.1f}°C"
        })
        
        response = f"""
        <div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>
        <span style='color: #00e5ff;'>[ANALYZE]</span> Target: {name} (Surface type: {asset_type}) at {lat:.4f}, {lon:.4f}<br>
        <span style='color: #00e5ff;'>[PROPOSE]</span> Intervention: {intervention_name}<br>
        <span style='color: #10b981;'>[ROI MATH]</span> Est. Local Cooling: -{cooling_offset:.1f}°C<br>
        <span style='color: #10b981;'>[ROI MATH]</span> Est. Annual Savings: ${energy_savings:,}
        </div>
        Intervention simulated. The dashboard metrics and map have been updated to reflect the new state.
        """
        self.add_message("assistant", response)
        st.session_state.agent_status = "IDLE"

    def simulate_verification(self):
        """Scenario: Verify Green Bond"""
        self.add_message("user", "Verify Green Bond Impact")
        st.session_state.agent_status = "VERIFYING"
        
        rand_val = random.randint(10000000000, 100000000000)
        hash_val = "0x" + str(rand_val) + "...31a"
        response = """
        <div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>
        <span style='color: #00e5ff;'>[REFLECT]</span> Comparing 2025 baseline vs 2026 satellite actuals.<br>
        <span style='color: #10b981;'>[VERIFY]</span> Intervention #882 reduced peak temp by 2.1°C.<br>
        <span style='color: #10b981;'>[BLOCKCHAIN]</span> Impact Sealed. Hash: HASH_VALUE_PLACEHOLDER
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
                    temp = st.session_state.data[-1]
                    resilience = st.session_state.data[-2]
                except Exception:
                    pass
                    
            active_layers = [k for k, v in st.session_state.get("layer_toggles", {}).items() if v]
            layers_str = ", ".join(active_layers) if active_layers else "None"
            
            system_prompt_text = "You are the Gaia Heat Sync Agent, a highly advanced, bio-minimalist Planetary Intelligence system currently focused on urban resilience for the CITY_PLACEHOLDER Bio-Region Node. Your tone is technical, institutional, but 'living'—think high-trust Digital Public Infrastructure. Focus on urban heat, tree canopy, water resources, public parks, and sensor data. Keep responses concise and structured. Use formatting like <span style='color: #00e5ff;'>[SENSE]</span> when describing reasoning steps if relevant, but otherwise respond naturally as an AI. CURRENT SYSTEM CONTEXT - Avg Surface Temp: TEMP_PLACE°C | Resilience Score: RESILIENCE_PLACE/100 | Active Map Layers: LAYERS_PLACE. IMPORTANT: If the user asks to see or activate a layer, include the exact tag [ACTION: ACTIVATE_{LAYER_NAME}] in your response. Available layers are: THERMAL, TREES, WATER, PARKS, SHELTERS, FOUNTAINS, GREEN_ROOFS, GARDENS, FORESTS, WETLANDS, SENSORS. To deactivate, use [ACTION: DEACTIVATE_{LAYER_NAME}]."
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
                    if layer_key in st.session_state.get("layer_toggles", {}):
                        st.session_state.layer_toggles[layer_key] = (action_type == "ACTIVATE")
            except Exception as e:
                st.error(f"*[Connection Error]* Failed to reach Gaia Central Node.")
                self.add_message("assistant", f"*[Connection Error]* Failed to reach Gaia Central Node: {str(e)}")
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
                
        active_layers = [k for k, v in st.session_state.get("layer_toggles", {}).items() if v]
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
