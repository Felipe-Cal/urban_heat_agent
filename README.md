# Gaia Heat Sync — Planetary Intelligence Dashboard

A high-fidelity Streamlit dashboard for urban heat resilience, built for the Open Earth Foundation. It visualises live thermal, air quality, and nature ID data on an interactive 3D map, and features an AI agent for bio-regional analysis and ROI simulation.

## Features

- **Live Data** — Real temperature & AQI from Open-Meteo; real geographic assets from OpenStreetMap
- **Multi-Layer Map** — 16 toggleable layers (thermal, NDVI, albedo, population, buildings, traffic, nature assets)
- **Gaia Agent** — GPT-4o-mini-powered AI agent for region analysis, interventions, and Q&A
- **ROI Sandbox** — Click-to-simulate cooling interventions with cost/impact estimates
- **Green Ledger** — Simulated Nature ID hashing and verifiable data provenance
- **PDF Briefings** — Auto-generated professional briefing reports

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
