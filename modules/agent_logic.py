"""
Agent logic for Gaia Heat Sync.

The AgentSimulator class handles all AI reasoning, chat history management,
and sandbox simulation interactions. It uses a lazy-loaded OpenAI client
and delegates context building to a single private helper to avoid repetition.
"""
import os
import random
import re
import string
import tempfile
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Generator

import streamlit as st
from modules.state_manager import StateManager

try:
    from openai import OpenAI
    from openai.types.chat import ChatCompletionChunk
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
    "ndvi", "albedo", "buildings", "traffic", "population",
]


class AgentSimulator:
    def __init__(self):
        # Initialization handled by StateManager in app.py
        pass

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def add_message(self, role: str, content: str) -> None:
        """Append a message to the persistent chat history."""
        chat_history = StateManager.get("chat_history", [])
        chat_history.append({"role": role, "content": content})
        # StateManager.set("chat_history", chat_history) # Not needed as list is mutable and ref is same

    def get_client(self) -> Optional["OpenAI"]:
        """Lazy-load the OpenAI client."""
        if not OpenAI:
            return None

        api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
             # Check for legacy/alternative location
             if "mapbox" in st.secrets and "OPENAI_API_KEY" in st.secrets["mapbox"]:
                 api_key = st.secrets["mapbox"]["OPENAI_API_KEY"]

        if api_key:
            return OpenAI(api_key=api_key)

        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_context(self) -> Dict[str, Any]:
        """
        Gather the current dashboard context into a plain dict.

        Returns:
            Dict with keys: city, temp, resilience, active_layers (comma-joined str).
        """
        city = StateManager.get("selected_city_name", "Unknown City")
        temp: Any = "Unknown"
        resilience: Any = "Unknown"

        city_data = StateManager.get("data")
        if city_data is not None:
            try:
                temp = city_data.current_temp
                resilience = city_data.resilience_score
            except Exception:
                pass

        active = [k for k in _ALL_LAYERS if StateManager.get(f"toggle_{k}", False)]
        return {
            "city": city,
            "temp": temp,
            "resilience": resilience,
            "active_layers": ", ".join(active) if active else "None",
        }

    def _build_system_prompt(self, ctx: Dict[str, Any]) -> Dict[str, str]:
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
            f"Resilience Score: {ctx['resilience']}/100 | "
            f"Active Map Layers: {ctx['active_layers']}. "
            f"IMPORTANT: If the user asks to see or activate a layer, include the exact tag "
            f"[ACTION: ACTIVATE_{{LAYER_NAME}}] in your response. Available layers are: "
            f"THERMAL, TREES, WATER, PARKS, SHELTERS, FOUNTAINS, GREEN_ROOFS, GARDENS, "
            f"FORESTS, WETLANDS, SENSORS. To deactivate, use [ACTION: DEACTIVATE_{{LAYER_NAME}}]."
        )
        return {"role": "system", "content": content}

    # ------------------------------------------------------------------
    # Simulation scenarios (no LLM — deterministic, fast)
    # ------------------------------------------------------------------

    def simulate_deployment(self) -> None:
        """Scenario: Deploy Nervous System."""
        self.add_message("user", "Scan for Data Desserts")
        StateManager.set("agent_status", "ACTIVE")
        response = (
            "<div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>"
            "**[SENSE]** Scanning for Data Deserts in Census Tract 242...<br>"
            "**[PLAN]** Identified 8 optimal locations for Solar-IoT nodes.<br>"
            "**[ACT]** Generating procurement request for open-standard sensors.<br>"
            "**[ACT]** Protocol: VDP-Signed (Verified Data Provenance)."
            "</div>"
            "Deployment sequence initiated. Activating Sensor Grid overlay."
        )
        self.add_message("assistant", response)
        StateManager.set("agent_status", "IDLE")

    def simulate_intervention(self) -> None:
        """Scenario: Win-Win Intervention."""
        self.add_message("user", "Detect Thermal Risk Areas")
        StateManager.set("agent_status", "REASONING")
        response = (
            "<div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>"
            "**[SENSE]** Surface temp 49°C detected in proximity to schools.<br>"
            "**[REASON]** High cardiovascular risk correlated with heat index.<br>"
            "**[PLAN]** Strategy: 40 Coast Live Oaks + Reflective Albedo Coating.<br>"
            "**[ROI]** Est. -3.2°C cooling | $1.2k annual energy savings."
            "</div>"
            "Risk area detected. Proposing biological intervention. Activating Nature ID overlay."
        )
        self.add_message("assistant", response)
        StateManager.set("agent_status", "IDLE")

    def auto_analyze_region(self) -> None:
        """Scenario: Auto-Analyze and suggest top interventions."""
        self.add_message("user", ":material/bolt: Auto-Analyze Region for Optimal Interventions")
        StateManager.set("agent_status", "REASONING")
        city = StateManager.get("selected_city_name", "This Region")
        response = (
            f"<div style='font-family: monospace; font-size: 0.9em; margin-bottom: 10px;'>"
            f"**[SENSE]** Scanning {city} for extreme thermal anomalies and vulnerable populations.<br>"
            f"**[REASON]** Correlating heat islands with lacking tree canopy and high density.<br>"
            f"**[PLAN]** Generated 3 optimal interventions localized for maximum impact."
            f"</div>"
            f"**Top Suggested Interventions:**\n"
            f"1. **Urban Forest Injection (Zone A):** +500 Trees near Highway Corridor. Est Cooling: -1.2°C.\n"
            f"2. **Albedo Modification (Zone B):** 20,000 sq ft of white roofs in dense commercial center. Est Cooling: -0.8°C.\n"
            f"3. **Emergency Cooling Center (Zone C):** Deploy active hydration/shelter node in highest risk tract.\n\n"
            f"*Activating relevant layers for visual confirmation.*"
        )
        self.add_message("assistant", response)
        StateManager.set("agent_status", "IDLE")

    def simulate_intervention_on_asset(self, obj: dict) -> None:
        """Sandbox Scenario: Propose a cooling intervention on a specific map asset."""
        asset_id = obj.get("asset_id", "Unknown")
        name = obj.get("name", "Urban Asset")
        asset_type = obj.get("type", "Concrete Mass")
        lat = obj.get("lat", 34.05)
        lon = obj.get("lon", -118.24)

        self.add_message("user", f"**[SANDBOX]** Propose a cooling intervention for {name} ({asset_type}).")
        StateManager.set("agent_status", "REASONING")

        # Determine intervention parameters by asset type
        if asset_type == "Concrete Mass":
            intervention_name = "500m² Intensive Green Roof"
            cooling_offset, energy_savings, health_impact, cost = 0.4, 12500, 1, 150000
            color = [163, 230, 53, 255]
        elif asset_type in ("Motorway", "Trunk", "Primary", "Road") or "Transit" in name:
            intervention_name = "Bioswale & Canopy Corridor"
            cooling_offset, energy_savings, health_impact, cost = 0.7, 8400, 3, 300000
            color = [21, 128, 61, 255]
        else:
            intervention_name = "Standard Albedo Enhancement"
            cooling_offset, energy_savings, health_impact, cost = 0.2, 5000, 0, 50000
            color = [56, 189, 248, 255]

        # Update simulation state
        StateManager.set("simulated_cooling", StateManager.get("simulated_cooling", 0.0) + cooling_offset)
        StateManager.set("sandbox_budget", StateManager.get("sandbox_budget", 5_000_000.0) - cost)

        nature_id_hash = "0x" + "".join(random.choices(string.hexdigits[:16], k=12))

        simulations = StateManager.get("simulations", [])
        simulations.append({
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
        # StateManager.set("simulations", simulations) # List is mutable

        ledger = StateManager.get("green_ledger", [])
        ledger.append({
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Nature ID": nature_id_hash,
            "Target Asset": name,
            "Intervention": intervention_name,
            "Cooling Impact (°C)": f"-{cooling_offset:.1f}",
            "Status": "Verified ✅",
        })
        # StateManager.set("green_ledger", ledger)

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
        StateManager.set("agent_status", "IDLE")

    def simulate_verification(self) -> None:
        """Scenario: Verify Green Bond."""
        self.add_message("user", "Verify Green Bond Impact")
        StateManager.set("agent_status", "VERIFYING")
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
        StateManager.set("agent_status", "IDLE")

    # ------------------------------------------------------------------
    # LLM-powered query handling
    # ------------------------------------------------------------------

    def process_custom_query(self, query: str) -> None:
        """Handle arbitrary user input, streaming from OpenAI if available."""
        self.add_message("user", query)
        StateManager.set("agent_status", "REASONING")

        client = self.get_client()
        if client:
            ctx = self._build_context()
            system_prompt = self._build_system_prompt(ctx)
            chat_history = StateManager.get("chat_history", [])
            messages = [system_prompt] + list(chat_history)

            try:
                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=600,
                    stream=True,
                )

                def _generate() -> Generator[str, None, None]:
                    for chunk in stream:
                        delta = chunk.choices[0].delta.content # type: ignore[attr-defined]
                        if delta is not None:
                            yield delta

                assistant_response = st.write_stream(_generate())
                self.add_message("assistant", assistant_response)

                # Parse and apply any map layer actions from the response
                actions = re.findall(r"\[ACTION:\s*(ACTIVATE|DEACTIVATE)_([A-Z_]+)\]", assistant_response)
                for action_type, layer_name in actions:
                    toggle_key = f"toggle_{layer_name.lower()}"
                    if toggle_key in st.session_state:
                        StateManager.set(toggle_key, action_type == "ACTIVATE")

            except Exception as e:
                st.error("*[Connection Error]* Failed to reach Gaia Central Node.")
                self.add_message("assistant", f"**:material/error: [Connection Error]** {e}")
        else:
            time.sleep(1)
            response = f"Simulated response to: '{query}'. (OpenAI API key not configured in secrets.toml)."
            st.markdown(response)
            self.add_message("assistant", response)

        StateManager.set("agent_status", "IDLE")

    # ------------------------------------------------------------------
    # PDF report generation
    # ------------------------------------------------------------------

    def generate_pdf_report(self) -> Optional[bytes]:
        """Generate a markdown briefing via LLM and convert it to PDF bytes."""
        StateManager.set("agent_status", "GENERATING REPORT")
        client = self.get_client()
        if not client or not MarkdownPdf:
            StateManager.set("agent_status", "IDLE")
            return None

        ctx = self._build_context()
        system_prompt = {
            "role": "system",
            "content": (
                f"You are the Gaia Heat Sync Agent. "
                f"CURRENT SYSTEM CONTEXT - Avg Surface Temp: {ctx['temp']}°C | "
                f"Resilience Score: {ctx['resilience']}/100 | "
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

            StateManager.set("agent_status", "IDLE")
            return pdf_bytes

        except Exception as e:
            st.error(f"Failed to generate PDF Report: {e}")
            StateManager.set("agent_status", "IDLE")
            return None
