"""
Agent logic for Gaia Heat Sync.

The AgentSimulator class handles all AI reasoning, chat history management,
and sandbox simulation interactions. It uses a lazy-loaded OpenAI client
and delegates context building to a single private helper to avoid repetition.
"""
import json
import os
import random
import re
import string
import tempfile
import time
from datetime import datetime
from typing import Optional

import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]

try:
    from markdown_pdf import MarkdownPdf, Section
except ImportError:
    MarkdownPdf = None  # type: ignore[assignment,misc]

# All available layer names — single source of truth used across the class
_ALL_LAYERS = [
    "thermal", "trees", "water", "parks", "shelters", "fountains",
    "green_roofs", "gardens", "forests", "wetlands", "sensors",
    "buildings", "traffic",
]


class AgentSimulator:
    def __init__(self):
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Initializing Gaia Node... ready for queries."}
            ]
        if "agent_status" not in st.session_state:
            st.session_state.agent_status = "IDLE"

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def add_message(self, role: str, content: str) -> None:
        """Append a message to the persistent chat history."""
        st.session_state.chat_history.append({"role": role, "content": content})

    def get_client(self) -> Optional["OpenAI"]:
        """Lazy-load the OpenAI client, checking common secret locations."""
        if not OpenAI:
            return None
        if "OPENAI_API_KEY" in st.secrets:
            return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        # Fallback: key accidentally placed under [mapbox]
        if "mapbox" in st.secrets and "OPENAI_API_KEY" in st.secrets["mapbox"]:
            return OpenAI(api_key=st.secrets["mapbox"]["OPENAI_API_KEY"])
        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_context(self) -> dict:
        """
        Gather the current dashboard context into a plain dict.

        Returns:
            Dict with keys: city, temp, aqi, active_layers (comma-joined str).
        """
        city = st.session_state.get("selected_city_name", "Unknown City")
        temp: object = "Unknown"
        aqi: object = "Unknown"

        city_data = st.session_state.get("data")
        if city_data is not None:
            try:
                temp = city_data.current_temp
                aqi = city_data.current_aqi
            except Exception:
                pass

        active = [k for k in _ALL_LAYERS if st.session_state.get(f"toggle_{k}", False)]
        return {
            "city": city,
            "temp": temp,
            "aqi": aqi,
            "active_layers": ", ".join(active) if active else "None",
        }

    def _build_system_prompt(self, ctx: dict) -> dict:
        content = (
            f"You are the Gaia Heat Sync Agent, a highly advanced, bio-minimalist "
            f"Planetary Intelligence system currently focused on urban resilience for the "
            f"{ctx['city']} Bio-Region Node. Your tone is technical, institutional, but "
            f"'living'—think high-trust Digital Public Infrastructure. Focus on urban heat, "
            f"tree canopy, water resources, public parks, and sensor data. Keep responses "
            f"concise and structured. Use formatting like "
            f"<span style='color: #3b82f6; font-weight: 500;'>[SENSE]</span> when describing "
            f"reasoning steps if relevant, but otherwise respond naturally as an AI. "
            f"CURRENT SYSTEM CONTEXT - Avg Surface Temp: {ctx['temp']}°C | "
            f"Air Quality Index (AQI): {ctx['aqi']} | "
            f"Active Map Layers: {ctx['active_layers']}. "
            f"You have access to tools to toggle map layers, switch cities, and query map data. "
            f"Use these tools proactively to answer user queries factually or control the dashboard."
        )
        return {"role": "system", "content": content}

    def _build_tools(self) -> list[dict]:
        """Define OpenAI Function Calling schemas for map actions and data queries."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "toggle_map_layer",
                    "description": "Activate or deactivate a specific map layer.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "layer_name": {"type": "string", "enum": ["thermal", "trees", "water", "parks", "shelters", "fountains", "green_roofs", "gardens", "forests", "wetlands", "sensors", "buildings", "traffic"]},
                            "state": {"type": "boolean", "description": "True to activate, False to deactivate"}
                        },
                        "required": ["layer_name", "state"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "switch_city",
                    "description": "Switch the planetary node to a different city.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city_name": {"type": "string", "enum": [
                                "Barcelona, Spain", "Cairo, Egypt", "London, UK", "Los Angeles, USA",
                                "Madrid, Spain", "Mexico City, Mexico", "Mumbai, India", "New York City, USA",
                                "San Francisco, USA", "São Paulo, Brazil", "Singapore", "Sydney, Australia", "Tokyo, Japan"
                            ]}
                        },
                        "required": ["city_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_urban_assets",
                    "description": "Query the counts of specific urban asset types currently loaded in the map data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "asset_type": {"type": "string", "enum": ["trees", "water", "parks", "shelters", "fountains", "green_roofs", "gardens", "forests", "wetlands", "sensors", "buildings", "traffic"]}
                        },
                        "required": ["asset_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_thermal_anomalies",
                    "description": "Get the coordinates and temperatures of the highest heat points (thermal anomalies) in the current city data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "top_n": {"type": "integer", "description": "Number of top anomalies to return. Default is 5.", "default": 5}
                        }
                    }
                }
            }
        ]

    # ------------------------------------------------------------------
    # Simulation scenarios (no LLM — deterministic, fast)
    # ------------------------------------------------------------------

    def simulate_deployment(self) -> None:
        """Scenario: Deploy Nervous System (Data Deserts)."""
        self.add_message("user", "Map Data Deserts")
        st.session_state.agent_status = "ACTIVE"
        
        # MOCK ANNOTATIONS: Create 5 mock data deserts spread around the city center
        data = st.session_state.get("data")
        lat, lon = 40.7128, -74.0060  # Fallback to NYC
        if data and hasattr(data, "df_buildings") and not data.df_buildings.empty:
            lat = float(data.df_buildings["lat"].mean())
            lon = float(data.df_buildings["lon"].mean())
        
        import random
        st.session_state.map_annotations = [
            {
                "lat": lat + random.uniform(-0.015, 0.015), 
                "lon": lon + random.uniform(-0.015, 0.015), 
                "radius": 150, 
                "color": [59, 130, 246, 200],
                "tooltip": "Optimal Node Location"
            }
            for _ in range(5)
        ]

        response = (
            "<div style='font-family: monospace; font-size: 0.85em; color: #64748b; margin-bottom: 12px; border-left: 2px solid #cbd5e1; padding-left: 8px;'>"
            "<i>Profiling Data Deserts in Census Tract 242</i>"
            "</div>"
            "**Strategic analysis complete.** I have identified 8 optimal locations for Solar-IoT nodes where our infrastructural awareness is weakest.\n\n"
            "**Deployment Sequence Initiated:**\n\n"
            "1. **Procurement:** Generating purchase request for open-standard sensors.\n"
            "2. **Data Protocol:** Locking nodes to VDP-Signed (Verified Data Provenance).\n"
            "3. **Map Overlay:** Activating Sensor Grid visualization on the active viewport."
        )
        self.add_message("assistant", response)
        st.session_state.agent_status = "IDLE"

    def simulate_intervention(self) -> None:
        """Scenario: Win-Win Intervention (Thermal Risk)."""
        self.add_message("user", "Map Thermal Risk Areas")
        st.session_state.agent_status = "REASONING"
        
        # MOCK ANNOTATIONS: Create 3 mock thermal risk areas (larger radius)
        data = st.session_state.get("data")
        lat, lon = 40.7128, -74.0060  # Fallback to NYC
        if data and hasattr(data, "df_buildings") and not data.df_buildings.empty:
            lat = float(data.df_buildings["lat"].mean())
            lon = float(data.df_buildings["lon"].mean())
        
        import random
        st.session_state.map_annotations = [
            {
                "lat": lat + random.uniform(-0.01, 0.01), 
                "lon": lon + random.uniform(-0.01, 0.01), 
                "radius": 250, 
                "color": [239, 68, 68, 200],
                "tooltip": "Thermal Risk Zone"
            }
            for _ in range(3)
        ]

        response = (
            "<div style='font-family: monospace; font-size: 0.85em; color: #64748b; margin-bottom: 12px; border-left: 2px solid #cbd5e1; padding-left: 8px;'>"
            "<i>Profiling Thermal Anomalies | Surface Temp: 49°C</i>"
            "</div>"
            "**Critical risk area detected.** A significant heat anomaly has been located in close proximity to multi-family housing and schools, correlating with a high cardiovascular risk profile.\n\n"
            "**Proposed Biological Intervention:**\n\n"
            "1. **Strategy:** Deploy 40 mature Coast Live Oaks + Reflective Albedo Coating.\n"
            "2. **Est. ROI:** -3.2°C localized cooling offset.\n"
            "3. **Capital Relief:** $1.2k annual energy savings across adjacent structures.\n\n"
            "Activating Nature ID overlay on the high-risk zones."
        )
        self.add_message("assistant", response)
        st.session_state.agent_status = "IDLE"

    def auto_analyze_region(self, data: Optional["CityData"] = None) -> None:
        """Scan current region data and suggest top interventions."""
        # Clear previous annotations on new regional analysis
        st.session_state.map_annotations = []
        
        # Use provided data or fallback to session state
        if data is None:
            data = st.session_state.get("data")
        
        city = st.session_state.get("selected_city_name", "This Region")
        temp = getattr(data, "current_temp", 30.0) if data else 30.0
        resilience = getattr(data, "resilience_score", 50) if data else 50

        self.add_message("user", f"**[EVENT]** Node Connection: {city}")
        st.session_state.agent_status = "REASONING"
        
        if city == "New York City, USA":
            reasoning = (
                "Thermal risk is currently **Minimal** due to low seasonal temperatures. "
                "The NYC Bio-Region node has high sensor density and comprehensive Nature ID coverage, "
                "providing a high-integrity baseline for planning."
            )
            actions = (
                "1. **Planning & Simulation:** Since conditions are stable, we could run **interventions** in the Sandbox "
                "to prepare for upcoming heatwaves.\n"
                "2. **Gap Analysis:** I can scan for **Data Deserts** to see where we can further densify the nervous system.\n"
                "3. **High-Risk Nodes:** Alternatively, we could switch to higher-risk regions like **Cairo, Egypt** or **Mexico City, Mexico** "
                "where thermal stress is currently elevated."
            )
        elif city == "Cairo, Egypt":
            reasoning = (
                "Thermal stress is currently **Elevated**. The Nile basin is experiencing a heat anomaly, "
                "and Nature ID coverage shows significant gaps in dense urban tracts."
            )
            actions = (
                "1. **Emergency Response:** I can scan for **Cooling Centers** and verify their operational capacity.\n"
                "2. **Thermal Risk Mapping:** I can activate the **Thermal Heatmap** to identify the most critical friction points.\n"
                "3. **Simulate Interventions:** We can test the ROI of adding white roofs or urban forests in the hottest zones."
            )
        else:
            reasoning = (
                f"The {city} Node is fully operational. Preliminary ingestion establishes a "
                f"Resilience Score of **{resilience}/100**."
            )
            actions = (
                "1. **Analyze Heat Islands:** I can scan for thermal anomalies and correlate them with canopy gaps.\n"
                "2. **Map Data Desserts:** I can identify areas in this region with insufficient sensor coverage.\n"
                "3. **Launch Sandbox:** We can simulate biological interventions to test ROI for cooling corridors."
            )

        response = (
            f"<div style='font-family: monospace; font-size: 0.85em; color: #64748b; margin-bottom: 12px; border-left: 2px solid #cbd5e1; padding-left: 8px;'>"
            f"<i>Profiling Regional Node: {city} [Surface: {temp:.1f}°C | Resilience: {resilience}/100]</i>"
            f"</div>"
            f"{reasoning}\n\n"
            f"**Suggested Next Steps:**\n\n"
            f"{actions}\n\n"
            f"Please select an option (1-3) or ask a custom question regarding this region."
        )
        
        # No automated toggles here, as per user preference.
        
        self.add_message("assistant", response)
        st.session_state.agent_status = "IDLE"

    def analyze_asset(self, obj: dict) -> None:
        """Contextual reasoning for a specific map asset clicked by the user."""
        # Clear region-wide annotations to focus on the asset
        st.session_state.map_annotations = []
        
        asset_id = obj.get("asset_id", obj.get("id", "Unknown"))
        name = obj.get("name", "Urban Asset")
        asset_type = obj.get("type", "Infrastructure")
        city = st.session_state.get("selected_city_name", "Current City")

        self.add_message("user", f"**[EVENT]** Map intersection: {name} ({asset_type})")
        st.session_state.agent_status = "REASONING"

        # Construct contextual reasoning based on asset type
        if asset_type in ("Tree", "Park", "Forest", "Garden"):
            reasoning = f"The selected terrestrial asset (**{name}**) acts as a primary cooling anchor and localized carbon sink for the {city} Bio-Region."
            actions = (
                f"1. **Verify Vitality:** I can check the vegetative health index and recent satellite delta for this {asset_type}.\n"
                f"2. **Assess Cooling Radius:** We can calculate its estimated localized temperature reduction.\n"
                f"3. **Simulate Expansion:** Enter Sandbox mode to model the ROI of expanding this natural asset."
            )
        elif asset_type in ("Water", "Wetland", "Fountain"):
            reasoning = f"The selected hydrological asset (**{name}**) provides evaporative cooling benefits and blue-green infrastructure value to the {city} node."
            actions = (
                f"1. **Thermal Scan:** Assess the evaporative cooling footprint of this water body on surrounding terrain.\n"
                f"2. **Riparian Buffer Analysis:** Scan for adjacent concrete surfaces that could be converted to absorbing buffers.\n"
                f"3. **Simulate Enhancement:** Enter Sandbox mode to model expanding its wetland periphery."
            )
        elif asset_type in ("Shelter", "Cooling Center"):
            reasoning = f"The selected facility (**{name}**) serves as a critical relief node during acute thermal stress events in {city}."
            actions = (
                f"1. **Check Capacity:** I can query real-time availability and operating status.\n"
                f"2. **Route Analysis:** Identify vulnerable populations within a 15-minute walking radius of this shelter.\n"
                f"3. **Resource Allocation:** Simulate deploying additional emergency supplies to this node."
            )
        else: # Buildings, Roads, Traffic, etc
            reasoning = f"The selected infrastructure (**{name}**) consists predominantly of impervious surfaces and contributes to localized thermal friction (Urban Heat Island effect)."
            actions = (
                f"1. **Thermal Scan:** I can assess the exact surface temperature anomaly of this specific asset.\n"
                f"2. **Simulate Retrofit:** Enter Sandbox mode to model adding a green roof or applying high-albedo (cool) coatings.\n"
                f"3. **Vulnerability Map:** Correlate this asset's heat retention with nearby population density."
            )

        response = (
            f"<div style='font-family: monospace; font-size: 0.85em; color: #64748b; margin-bottom: 12px; border-left: 2px solid #cbd5e1; padding-left: 8px;'>"
            f"<i>Profiling {name} ({asset_type}) at {city} Node [ID: {asset_id}]</i>"
            f"</div>"
            f"{reasoning}\n\n"
            f"**Suggested Next Steps:**\n\n"
            f"{actions}\n\n"
            f"Please select an option (1-3) or ask a custom question regarding this asset."
        )
        
        self.add_message("assistant", response)
        st.session_state.agent_status = "IDLE"

    def simulate_intervention_on_asset(self, obj: dict) -> None:
        """Sandbox Scenario: Propose a cooling intervention on a specific map asset."""
        asset_id = obj.get("asset_id", "Unknown")
        name = obj.get("name", "Urban Asset")
        asset_type = obj.get("type", "Concrete Mass")
        lat = obj.get("lat", 34.05)
        lon = obj.get("lon", -118.24)

        city_data = st.session_state.get("data")
        surface_temp = getattr(city_data, "current_temp", 35.0) if city_data else 35.0

        user_prompt = f"**[SANDBOX]** Propose a cooling intervention for {name} ({asset_type}) at {lat}, {lon}."
        self.add_message("user", user_prompt)
        st.session_state.agent_status = "REASONING"

        client = self.get_client()
        if client:
            system_prompt = {
                "role": "system",
                "content": (
                    f"You are the Gaia Heat Sync Agent planning an intervention for a {asset_type} "
                    f"called '{name}'. The regional average surface temp is {surface_temp:.1f}°C. "
                    f"Return ONLY a strictly formatted JSON object with the following keys: "
                    f"intervention_name (string), cooling_offset (float, positive value representing degrees C reduction), "
                    f"cost (integer in USD), energy_savings (integer in USD), health_impact (integer representing ER visits avoided). "
                    f"Be realistic and specific. For example, a bioswale might reduce temp by 0.7C and cost 300,000 USD."
                )
            }
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[system_prompt, {"role": "user", "content": user_prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                )
                raw_json = response.choices[0].message.content
                result = json.loads(raw_json)
                
                intervention_name = result.get("intervention_name", "Standard Albedo Enhancement")
                cooling_offset = float(result.get("cooling_offset", 0.2))
                cost = int(result.get("cost", 50000))
                energy_savings = int(result.get("energy_savings", 5000))
                health_impact = int(result.get("health_impact", 0))
            except Exception as e:
                intervention_name = "Emergency Albedo Enhancement"
                cooling_offset, cost, energy_savings, health_impact = 0.2, 50000, 5000, 0
        else:
            if asset_type == "Concrete Mass":
                intervention_name = "500m² Intensive Green Roof"
                cooling_offset, energy_savings, health_impact, cost = 0.4, 12500, 1, 150000
            elif asset_type in ("Motorway", "Trunk", "Primary", "Road") or "Transit" in name:
                intervention_name = "Bioswale & Canopy Corridor"
                cooling_offset, energy_savings, health_impact, cost = 0.7, 8400, 3, 300000
            else:
                intervention_name = "Standard Albedo Enhancement"
                cooling_offset, energy_savings, health_impact, cost = 0.2, 5000, 0, 50000

        # Determine color based on type
        inv_lower = intervention_name.lower()
        if "roof" in inv_lower or "green" in inv_lower:
            color = [163, 230, 53, 255]
        elif "bioswale" in inv_lower or "tree" in inv_lower or "canopy" in inv_lower:
            color = [21, 128, 61, 255]
        elif "water" in inv_lower or "wetland" in inv_lower:
            color = [56, 189, 248, 255]
        else:
            color = [56, 189, 248, 255]

        # Update simulation state
        st.session_state.simulated_cooling += cooling_offset
        st.session_state.sandbox_budget = st.session_state.get("sandbox_budget", 5_000_000.0) - cost

        nature_id_hash = "0x" + "".join(random.choices(string.hexdigits[:16], k=12))

        st.session_state.simulations.append({
            "lat": lat, "lon": lon,
            "name": intervention_name,
            "target": name,
            "cooling": cooling_offset,
            "color": color,
            "radius": 250,
            "tooltip": (
                f"<b style='font-size: 14px; color: #3b82f6;'>Simulated Intervention</b>"
                f"<br/><span style='color:#94a3b8; font-size:11px;'>Target: {name}</span>"
                f"<br/><br/><b>Installed:</b> {intervention_name}"
                f"<br/><b>Cooling Effect:</b> -{cooling_offset:.1f}°C"
                f"<br/><b>Health Impact:</b> {health_impact} ER visits avoided"
                f"<br/><b>Cost:</b> ${cost:,.0f}"
            ),
        })

        if "green_ledger" not in st.session_state:
            st.session_state.green_ledger = []
        st.session_state.green_ledger.append({
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Nature ID": nature_id_hash,
            "Target Asset": name,
            "Intervention": intervention_name,
            "Cooling Impact (°C)": f"-{cooling_offset:.1f}",
            "Status": "Verified ✅",
        })

        response = (
            f"<div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>"
            f"**[ANALYZE]** Target: {name} (Surface type: {asset_type}) at {lat:.4f}, {lon:.4f}<br>"
            f"**[PROPOSE]** Intervention: {intervention_name} | Cost: ${cost:,.0f}<br>"
            f"**[ROI: GRID]** Est. Annual Savings: ${energy_savings:,}<br>"
            f"**[ROI: HEALTH]** Est. ER Visits Prevented: {health_impact}<br>"
            f"**[ROI: CLIMATE]** Est. Local Cooling: -{cooling_offset:.1f}°C<br>"
            f"**[MINT]** Nature ID Generated: `{nature_id_hash}` (Submitting to Green Ledger)"
            f"</div>"
            f"Intervention simulated and Nature ID minted. The dashboard has been updated."
        )
        self.add_message("assistant", response)
        st.session_state.agent_status = "IDLE"

    def simulate_verification(self) -> None:
        """Scenario: Verify Green Bond."""
        self.add_message("user", "Verify Green Bond Impact")
        st.session_state.agent_status = "VERIFYING"
        rand_val = random.randint(10_000_000_000, 100_000_000_000)
        hash_val = f"0x{rand_val}...31a"
        response = (
            "<div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>"
            "**[REFLECT]** Comparing 2025 baseline vs 2026 satellite actuals.<br>"
            "**[VERIFY]** Intervention #882 reduced peak temp by 2.1°C.<br>"
            f"**[BLOCKCHAIN]** Impact Sealed. Hash: {hash_val}"
            "</div>"
            "Verification complete. Impact cryptographically secured to the Green Ledger."
        )
        self.add_message("assistant", response)
        st.session_state.agent_status = "IDLE"

    # ------------------------------------------------------------------
    # LLM-powered query handling
    # ------------------------------------------------------------------

    def process_custom_query(self, query: str) -> None:
        """Handle arbitrary user input, using function calling to interact with tools."""
        st.session_state.map_annotations = []
        
        self.add_message("user", query)
        st.session_state.agent_status = "REASONING"

        client = self.get_client()
        if client:
            ctx = self._build_context()
            system_prompt = self._build_system_prompt(ctx)
            messages = [system_prompt] + list(st.session_state.chat_history)

            try:
                # First non-streaming call to get tool_calls
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=600,
                    tools=self._build_tools(),
                    tool_choice="auto",
                )

                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                if tool_calls:
                    messages.append(response_message)
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        try:
                            function_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            function_args = {}
                            
                        if function_name == "toggle_map_layer":
                            layer_name = function_args.get("layer_name")
                            state = function_args.get("state")
                            if layer_name is not None and state is not None:
                                toggle_key = f"toggle_{layer_name.lower()}"
                                if toggle_key in st.session_state:
                                    st.session_state[toggle_key] = state
                                messages.append({
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": function_name,
                                    "content": json.dumps({"status": "success", "message": f"Layer {layer_name} set to {state}"})
                                })
                            else:
                                messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": '{"error": "Missing layer_name or state"}'})
                        
                        elif function_name == "switch_city":
                            city_name = function_args.get("city_name")
                            if city_name:
                                valid_cities = [
                                    "Barcelona, Spain", "Cairo, Egypt", "London, UK", "Los Angeles, USA",
                                    "Madrid, Spain", "Mexico City, Mexico", "Mumbai, India", "New York City, USA",
                                    "San Francisco, USA", "São Paulo, Brazil", "Singapore", "Sydney, Australia", "Tokyo, Japan"
                                ]
                                best_match = city_name
                                for valid in valid_cities:
                                    if city_name.strip().lower() in valid.lower() or valid.lower() in city_name.strip().lower():
                                        best_match = valid
                                        break
                                st.session_state.selected_city_name = best_match
                                st.session_state.need_initial_analysis = True
                                messages.append({
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": function_name,
                                    "content": json.dumps({"status": "success", "message": f"City switched to {best_match}"})
                                })
                            else:
                                messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": '{"error": "Missing city_name"}'})
                        
                        elif function_name == "query_urban_assets":
                            asset_type = function_args.get("asset_type")
                            city_data = st.session_state.get("data")
                            count = 0
                            if city_data and asset_type:
                                df_name = f"df_{asset_type.lower()}"
                                if hasattr(city_data, df_name):
                                    df = getattr(city_data, df_name)
                                    count = len(df)
                            messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps({"status": "success", "count": count, "asset_type": asset_type})
                            })
                            
                        elif function_name == "get_thermal_anomalies":
                            top_n = function_args.get("top_n", 5)
                            city_data = st.session_state.get("data")
                            anomalies = []
                            if city_data and hasattr(city_data, "df_thermal_points") and not city_data.df_thermal_points.empty:
                                df = city_data.df_thermal_points
                                top_df = df.nlargest(top_n, 'temp')
                                anomalies = top_df[['lat', 'lon', 'temp']].to_dict(orient='records')
                            messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps({"status": "success", "anomalies": anomalies})
                            })
                        else:
                            messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps({"error": f"Unknown tool: {function_name}"})
                            })

                    # Second streaming call after tool execution
                    stream = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=600,
                        stream=True,
                    )
                    
                    def _generate_stream():
                        for chunk in stream:
                            delta = chunk.choices[0].delta.content
                            if delta is not None:
                                yield delta
                    assistant_response = st.write_stream(_generate_stream())
                    
                else:
                    # No tool calls, standard streaming simulation
                    content = response.choices[0].message.content or ""
                    def _generate_synthetic():
                        words = content.split(" ")
                        for i, word in enumerate(words):
                            yield word + (" " if i < len(words) - 1 else "")
                            time.sleep(0.01)
                    assistant_response = st.write_stream(_generate_synthetic())

                self.add_message("assistant", assistant_response)

            except Exception as e:
                st.error("*[Connection Error]* Failed to reach Gaia Central Node.")
                self.add_message("assistant", f"**:material/error: [Connection Error]** {e}")
        else:
            time.sleep(1)
            response = f"Simulated response to: '{query}'. (OpenAI API key not configured in secrets.toml)."
            st.markdown(response)
            self.add_message("assistant", response)

        st.session_state.agent_status = "IDLE"

    # ------------------------------------------------------------------
    # PDF report generation
    # ------------------------------------------------------------------

    def generate_pdf_report(self) -> Optional[bytes]:
        """Generate a markdown briefing via LLM and convert it to PDF bytes."""
        st.session_state.agent_status = "GENERATING REPORT"
        client = self.get_client()
        if not client or not MarkdownPdf:
            st.session_state.agent_status = "IDLE"
            return None

        ctx = self._build_context()
        system_prompt = {
            "role": "system",
            "content": (
                f"You are the Gaia Heat Sync Agent. "
                f"CURRENT SYSTEM CONTEXT - Avg Surface Temp: {ctx['temp']}°C | "
                f"Air Quality Index (AQI): {ctx['aqi']} | "
                f"Active Map Layers: {ctx['active_layers']}."
            ),
        }
        messages = [
            system_prompt,
            {
                "role": "user",
                "content": (
                    f"Generate a formal bio-regional resilience briefing based on the current "
                    f"dashboard context for the {ctx['city']} Bio-Region Node. Format as a "
                    f"professional Markdown report. Do not use any map control actions, just "
                    f"return the report text."
                ),
            },
        ]

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=1500,
            )
            markdown_content = response.choices[0].message.content

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
