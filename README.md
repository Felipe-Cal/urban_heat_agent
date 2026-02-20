# Gaia Heat Sync — Urban Heat Sync Agent

> **Role**: City Resilience Cockpit & Planetary Intelligence Proxy  
> **Stack**: Python · Streamlit · PyDeck · Mapbox · OpenStreetMap · Open-Meteo  
> **Status**: Live Prototype · MVP Stage

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/Felipe-Cal/urban_heat_agent)

---

## 🌍 Vision

This prototype is the **"First Domino"** of a multi-stage roadmap toward a self-governing planetary intelligence for urban climate resilience.

| Stage | Year | Scope | Agency |
|-------|------|-------|--------|
| **1. Urban Heat Agent** | 2026 | City-scale | Human-in-the-loop |
| **2. Regional Orchestration** | 2032 | Watershed & grid | Semi-autonomous |
| **3. Gaia Sovereign AI** | 2040 | Planetary | Fully sovereign |

---

## 🛠 Features

- **Biosphere Map**: Thermal heatmap, NDVI, Albedo, Population Density, Building Mass, Traffic Arteries — all from real OSM/satellite data
- **Nature ID Registry**: Digital twins for every urban tree, park, wetland, and green roof — pulled live from OpenStreetMap
- **Gaia Agent**: GPT-4o-mini powered assistant with streaming, map layer control, and Sense-Plan-Act reasoning loop
- **ROI Sandbox**: Click any map asset to simulate cooling interventions with cost/ROI calculations
- **Green Ledger**: Verifiable Data Provenance — every intervention minted with a deterministic cryptographic hash
- **PDF Briefing**: AI-generated policy brief exportable as a professional PDF

---

## 🚀 Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Create `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "sk-..."

[mapbox]
access_token = "pk...."
```

---

## ☁️ Deploying to Streamlit Cloud

1. Push to GitHub (this repo)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → select `Felipe-Cal/urban_heat_agent`, branch `master`, file `app.py`
3. Under **Settings → Secrets**, paste your `secrets.toml` contents
4. Click **Deploy**

> **Note**: OSM data is cached daily to `/tmp/heat_osm_cache/` to prevent cold-start timeouts on Streamlit Cloud's shared infrastructure.

