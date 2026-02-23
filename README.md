# Gaia Heat Sync — Urban Heat Sync Agent

An intelligent, agent-driven spatial application for urban heat resilience, built for the Open Earth Foundation. It acts as a "Trojan Horse" to force the creation of Nature IDs for trees and water resources, scaling seamlessly from a single street to managing city-wide grids to solve lethal heat waves.

Unlike a static dashboard, Gaia Heat Sync is a living Digital Twin with two-way AI agent interaction: the map informs the Agent, and the Agent controls the map. The system actively senses heat, plans cooling, acts via infrastructure interventions, and reflects on outcomes—directly protecting vulnerable populations in "data deserts".

## Features

- **Two-Way Agentic Interaction**
  - **Map-to-Agent:** Clicking on specific map assets (e.g., buildings, trees, cooling centers) sends rich spatial context to the Gaia Agent to analyze localized risk and propose exact, contextual interventions.
  - **Agent-to-Map:** Users can naturally converse with the agent, which actively manipulates the digital twin—toggling layers, switching cities, identifying thermal anomalies, and deploying simulated infrastructure networks.
- **Continuous Learning Loop** — Senses real-time heat and AQI (Open-Meteo), plans cooling strategies based on asset data (OpenStreetMap), acts in a Sandbox environment, and reflects on outcomes.
- **Dynamic Digital Twin** — 13 toggleable mapping layers dynamically updated by user clicks or AI generation.
- **ROI Sandbox & Parametric Finance** — Simulates specific cooling interventions with realistic cost and impact estimates (e.g., °C cooling offset, ER visits avoided).
- **Green Ledger (Tech Spine)** — Mints verifiable "Nature IDs" onto a Verifiable Data Provenance ledger for trees, water, and cooling assets.
- **PDF Briefings** — Auto-generated, professional regional briefing reports.

## Use Case Showcase

The system demonstrates 14 key capabilities ranging from real-time environmental sensing to simulated parametric finance. For a detailed guide on how to test each feature, including known limitations and "what makes it real," please refer to the [Use Case Showcase Guide](USE_CASES.md).

## Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd heat

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure secrets (see below)

# 5. Run
streamlit run app.py
```

## Secrets Configuration

Create `.streamlit/secrets.toml` (this file is git-ignored):

```toml
OPENAI_API_KEY = "sk-..."

[mapbox]
access_token = "pk...."
```

- **OpenAI key** is required for the Gaia Agent and PDF report generation. Without it, the agent falls back to a simulated response.
- **Mapbox token** is required for the satellite/street base map. Without it, the app falls back to a free CartoDB base map.
- **OPENAQ_API_KEY** (optional): when set, Air Quality nodes show real per-sensor AQI from OpenAQ latest measurements instead of city-level value.

## Project Structure

```
heat/
├── app.py                  # Main Streamlit entry point
├── modules/
│   ├── __init__.py
│   ├── models.py           # CityData, LayerToggles, MapConfig dataclasses
│   ├── data_generator.py   # Fetches + synthesises all city data
│   ├── map_layers.py       # PyDeck layer composition
│   ├── agent_logic.py      # AgentSimulator (OpenAI + simulation scenarios)
│   └── styles.py           # CSS injection
├── tests/
│   ├── __init__.py
│   ├── test_data_generator.py
│   ├── test_agent_logic.py
│   └── test_map_layers.py
├── .streamlit/
│   ├── config.toml         # Theme and server config
│   └── secrets.toml        # API keys (git-ignored)
└── requirements.txt        # Pinned dependencies
```

## Running Tests

```bash
# From the project root
python -m pytest tests/ -v
```

Tests mock all HTTP calls (Open-Meteo, Overpass API, OpenAI) so they run offline and fast.
