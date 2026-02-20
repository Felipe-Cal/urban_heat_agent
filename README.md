# Gaia Heat Sync — Planetary Intelligence Dashboard

**Gaia Heat Sync** is a high-fidelity **Streamlit** dashboard designed for urban heat resilience. It acts as a bio-regional "nervous system" for cities, visualizing live thermal data, air quality, and nature-based assets on an interactive 3D map.

Powered by an AI agent (**Gaia Agent**) and real-time data integrations (Open-Meteo, OpenStreetMap, OpenAQ), it allows urban planners and citizens to simulate cooling interventions, verify green claims, and generate professional briefing reports.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.54.0-FF4B4B.svg)

---

## 🌍 Key Features

### 1. **Live Bio-Regional Data**
- **Thermal Imaging**: Real-time land surface temperature approximations based on Open-Meteo forecast data.
- **Air Quality**: Live AQI readings from OpenAQ sensors (or synthetic fallbacks if API limits are hit).
- **Urban Assets**: Fetches real geographic data for trees, parks, water bodies, and buildings via the **Overpass API (OpenStreetMap)**.
- **Multi-Layer Map**: 16 toggleable layers including NDVI (Vegetation), Albedo (Reflectance), Population Density, and Traffic Arteries.

### 2. **Gaia Agent (AI Assistant)**
- **Context-Aware**: The agent "sees" the map state (active layers, selected city, resilience score).
- **Intervention Planning**: Ask Gaia to "Scan for Data Deserts" or "Detect Thermal Risk Areas" to automatically analyze the region.
- **Digital Twins**: Click on any map asset (e.g., a specific tree or building) to pull up its "Digital Twin" profile, including estimated carbon sequestration and cooling impact.
- **PDF Reports**: Generates professional Markdown/PDF briefing reports summarizing the city's current resilience status.

### 3. **ROI Sandbox & Green Ledger**
- **Simulation Mode**: Propose interventions (e.g., "Plant 500 Oaks", "Install Green Roof") and see instant ROI calculations for cooling, energy savings, and health impact.
- **Green Ledger**: A verifiable SQLite-based ledger that tracks all simulated interventions. "Mint" a Nature ID for every action, simulating a blockchain-based verification system for green bonds.

---

## 🏗️ Architecture

The project is built on a modular Python architecture:

- **Frontend**: [Streamlit](https://streamlit.io/) for the reactive UI.
- **Mapping**: [PyDeck](https://pydeck.gl/) for high-performance 3D WebGL visualizations.
- **AI/LLM**: [OpenAI GPT-4o-mini](https://openai.com/) for the Gaia Agent's reasoning and report generation.
- **Data Fetching**: Custom `data_generator` module that parallelizes requests to:
  - **Open-Meteo**: Weather & Air Quality.
  - **Overpass API**: OpenStreetMap vector data.
  - **OpenAQ**: Air quality sensor locations.
- **Persistence**: SQLite (via `modules/database.py`) for the Green Ledger.

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11 or higher
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/gaia-heat-sync.git
cd gaia-heat-sync
```

### 2. Create a Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Secrets
Create a `.streamlit/secrets.toml` file in the project root. This file is git-ignored to protect your API keys.

```toml
# .streamlit/secrets.toml

OPENAI_API_KEY = "sk-..."

[mapbox]
# Optional: Required for the satellite/street base map style.
# If omitted, the app falls back to a free CartoDB base map.
access_token = "pk...."
```

### 5. Run the Application
```bash
streamlit run app.py
```
The dashboard should open automatically in your browser at `http://localhost:8501`.

---

## 📖 Usage Guide

### Navigating the Dashboard
- **Left Panel (Gaia Agent)**: Chat with the AI, trigger auto-analyses, and manage the Sandbox.
- **Right Panel (Map & Data)**: Select the active Bio-Region (City), toggle map layers, and view live metrics (Resilience Score, Temp, AQI).
- **Time Slider**: Adjust the time of day to simulate diurnal temperature variations.

### Interactive Sandbox
1. Click **"Launch Sandbox"** in the left panel.
2. Click anywhere on the map (or on a specific asset) to propose an intervention.
3. The Agent will simulate the cost and impact (e.g., "-0.4°C Cooling").
4. The intervention is recorded in the **Green Ledger** (expandable section below the Agent controls).

### Generating Reports
1. Ensure you have populated the map or run some simulations.
2. Click **"Generate Briefing Report"**.
3. Gaia will write a summary and offer a PDF download.

---

## 📂 Project Structure

```
heat/
├── app.py                  # Main Streamlit application entry point
├── modules/
│   ├── __init__.py
│   ├── agent_logic.py      # Gaia Agent (OpenAI interaction, simulation scenarios)
│   ├── data_generator.py   # Data fetching (Open-Meteo, OSM, OpenAQ) & synthesis
│   ├── database.py         # SQLite storage for Green Ledger
│   ├── map_layers.py       # PyDeck layer composition & rendering
│   ├── models.py           # Dataclasses (CityData, LayerToggles, MapConfig)
│   └── styles.py           # CSS injection for custom UI theming
├── tests/
│   ├── __init__.py
│   ├── test_agent_logic.py
│   ├── test_data_generator.py
│   └── test_map_layers.py
├── .streamlit/
│   ├── config.toml         # Streamlit theme configuration
│   └── secrets.toml        # API keys (user-created, git-ignored)
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## ✅ Running Tests

The project includes a `pytest` suite that mocks external API calls, allowing for fast, offline testing.

```bash
# Run all tests
python -m pytest tests/ -v
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Open Earth Foundation** for the inspiration on planetary intelligence.
- **Open-Meteo** for their excellent free weather APIs.
- **OpenStreetMap** contributors for the global geospatial data.
- **OpenAQ** for open air quality data.
