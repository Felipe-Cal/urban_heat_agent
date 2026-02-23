# Gaia Heat Sync — Urban Heat Sync Agent Showcase Guide

This document outlines 14 distinct capabilities of the Gaia Heat Sync Agent. It is designed to demonstrate how the platform acts as a continuous learning loop (Senses, Plans, Acts, Reflects) to build urban resilience against lethal heat waves, while simultaneously forcing the creation of Verifiable Nature IDs as its core tech spine. demonstrates, how to test it live, what is still missing, and how hard the missing piece would be to build.

---

## Summary Table

| # | Use Case | Status | Impact | Effort to Complete |
|---|----------|--------|--------|--------------------|
| [UC-01](#uc-01--cooling-asset-inventory--nature-id-registry) | Cooling Asset Inventory / Nature ID Registry | ✅ Live | ⭐⭐⭐⭐⭐ | — |
| [UC-02](#uc-02--real-thermal-surface-temperature-heatmap) | Real Thermal Surface Temperature Heatmap | ✅ Live | ⭐⭐⭐⭐⭐ | — |
| [UC-03](#uc-03--temporal-heat-simulation-diurnal-cycle) | Temporal Heat Simulation (Diurnal Cycle) | ✅ Live | ⭐⭐⭐⭐ | — |
| [UC-04](#uc-04--live-air-quality-sensor-network-openaq) | Live Air Quality Sensor Network (OpenAQ) | ✅ Live | ⭐⭐⭐⭐ | — |
| [UC-05](#uc-05--dynamic-heat-risk-index) | Dynamic Heat Risk Index | ✅ Live | ⭐⭐⭐⭐ | — |
| [UC-06](#uc-06--sandbox--intervention-simulator) | Sandbox — Intervention Simulator | ✅ Live | ⭐⭐⭐⭐⭐ | — |
| [UC-07](#uc-07--green-ledger--verifiable-data-provenance-vdp) | Green Ledger / Verifiable Data Provenance | ⚠️ Partial | ⭐⭐⭐⭐⭐ | 🔨 Medium |
| [UC-08](#uc-08--agentic-digital-twin-asset-profiling) | Agentic Digital Twin Asset Profiling | ✅ Live | ⭐⭐⭐⭐⭐ | — |
| [UC-09](#uc-09--agentic-sense--plan--act--reflect-loop) | Agentic Sense → Plan → Act → Reflect Loop | ⚠️ Partial | ⭐⭐⭐⭐⭐ | 🔨 Medium |
| [UC-10](#uc-10--multi-city-bio-region-comparison) | Multi-City / Bio-Region Comparison | ⚠️ Partial | ⭐⭐⭐⭐ | 🔧 Low |
| [UC-11](#uc-11--ai-generated-briefing-report) | AI-Generated Briefing Report (PDF) | ✅ Live | ⭐⭐⭐⭐ | — |
| [UC-12](#uc-12--data-desert-detection--iot-sensor-gap-mapping) | Data Desert Detection / IoT Sensor Gap Mapping | ⚠️ Partial | ⭐⭐⭐ | 🔧 Low |
| [UC-13](#uc-13--parametric-finance--green-bond-verification) | Parametric Finance / Green Bond Verification | ❌ Simulated | ⭐⭐⭐⭐⭐ | 🏗️ High |
| [UC-14](#uc-14--user-authentication--multi-stakeholder-access) | User Authentication / Multi-Stakeholder Access | ✅ Live | ⭐⭐⭐ | — |

**Legend — Effort:** 🔧 Low (< 1 day) · 🔨 Medium (1–3 days) · 🏗️ High (> 3 days)

---

## UC-01 · Cooling Asset Inventory / Nature ID Registry

**Status:** ✅ Live (as of 2026-02-20)

### What it demonstrates
A city heat officer opens the platform and sees every cooling infrastructure asset in a neighbourhood — every street tree, park, drinking fountain, cooling shelter, green roof, community garden, urban forest, and wetland within a configurable radius. Every asset has a **Nature ID** (e.g. `TREE-12345678`), a decentralised digital identity derived from the OpenStreetMap element ID. This is the foundational primitive of the entire planetary intelligence vision.

### What makes it real
| Data field | Source | Real? |
|---|---|---|
| Asset locations (lat/lon) | OpenStreetMap Overpass API | ✅ Real |
| Asset names, species, type | OSM `name`, `species`, `genus` tags | ✅ Real |
| Opening hours / live open-closed status | OSM `opening_hours` tag | ✅ Real |
| Operator, capacity, A/C, wheelchair, phone | OSM rich tags | ✅ Real (where mapped) |

### What is missing
- Nature IDs are session-only — they are not persisted to the `nature_assets` SQLite table (code exists in `database.py` but the `upsert_nature_asset()` call is never made from the data pipeline).
- No cross-session deduplication: re-loading the same city generates fresh random IDs each time.

### How to test
1. Open the app → select **London, UK** or **Singapore** (best OSM coverage)
2. Enable: `Tree Canopy`, `Cooling Centers`, `Drinking Fountains`, `Public Parks`
3. Click any **amber dot** (Cooling Center) → verify the tooltip shows Open/Closed status, address, operator, and `SHELTER-<id>`
4. Click any **green dot** (Tree) → verify tooltip shows species name and `TREE-<id>`
5. Compare two city views — notice how park density changes resilience score (UC-05)

**Expected result:** Each asset has a structured ID, real operational data, and a "Cooling asset" tag — the raw material for a Nature ID registry.

---

## UC-02 · Real Thermal Surface Temperature Heatmap

**Status:** ✅ Live (as of 2026-02-20)

### What it demonstrates
Stakeholders visualise the Urban Heat Island (UHI) distribution across a city. The heatmap is not synthetic — it fetches a 10×10 grid of real surface/soil temperatures from the Open-Meteo API, then interpolates 2,000 scatter points using Inverse Distance Weighting (IDW) for a smooth, organic look. This proves that remote-sensing paradigms can work from open APIs without proprietary satellite access.

### What makes it real
| Data field | Source | Real? |
|---|---|---|
| Land Surface Temperature (LST) | Open-Meteo `soil_temperature_0cm` (batch API) | ✅ Real |
| Spatial grid (~3 km radius, 10×10 points) | Open-Meteo forecast API, multi-point format | ✅ Real |
| Diurnal modulation | Cosine offset calibrated to local time slider | ✅ Modelled |

### What is missing
- Resolution is 1–11 km per model pixel — cannot resolve street-level variation.
- No true satellite IR (Landsat/Sentinel) integration. That would provide 30 m resolution but requires authenticated access (NASA EarthData, Copernicus).

### How to test
1. Select **Los Angeles, CA** or **Singapore**
2. Enable `Thermal` layer (Map Layers section)
3. Verify an irregular, asymmetric heat distribution (not a perfect circle)
4. Open browser DevTools → Network → filter `open-meteo.com` → confirm the batch request with 100 comma-separated lat/lon pairs

**Expected result:** Realistic thermal overlay with irregular hot/cool patches; DevTools confirms a real API call.

---

## UC-03 · Temporal Heat Simulation (Diurnal Cycle)

**Status:** ✅ Live

### What it demonstrates
Users can drag a time slider to simulate heat intensity at any hour of the day. The system uses a calibrated cosine diurnal model (peak ~14:00, trough ~04:00) to shift the thermal heatmap and `Avg Surface Temp` metric in real time. A blue **NOW** marker on the slider shows the city's actual local time.

### What makes it real
- City UTC offsets are hardcoded per-city.
- The displayed temperature is derived from the Open-Meteo live reading, modulated by the diurnal model.
- The slider auto-initialises to the city's current local time on city change.
- Infrastructure and nature datasets are efficiently reused during temporal shifts, guaranteeing smooth 60fps simulation without hitting external APIs repeatedly.

### What is missing
- The diurnal model uses a simplified cosine; it does not account for cloud cover, humidity, or seasonal variation.
- Thermal grid data is fetched once and shared across all slider positions (day simulation is only an approximation, not a re-fetch at each hour).

### How to test
1. Select any city — note the `Avg Surface Temp` reading and the NOW marker position
2. Drag the slider to **14:00** — verify `Avg Surface Temp` increases vs. 04:00
3. Drag slider to **04:00** — verify temperature drop
4. Switch cities — verify the slider resets to the new city's local time, and NOW marker repositions

**Expected result:** Temperature delta updates live; NOW marker accurate to within 15 min; city switch resets slider.

---

## UC-04 · Live Air Quality Sensor Network (OpenAQ)

**Status:** ✅ Live (requires `OPENAQ_API_KEY` in `secrets.toml` for full data)

### What it demonstrates
Real air quality monitoring stations from the **OpenAQ v3** network are plotted on the map as coloured dots (🟢 Good / 🟡 Moderate / 🔴 Unhealthy). With an API key, each station fetches real PM2.5/Ozone/NO2/PM10 readings and converts them to US AQI using EPA breakpoints. This layer demonstrates **real-time IoT sensor ingestion** — one of the core Sense components.

### What makes it real
| Data | Source | Real? |
|---|---|---|
| Station locations | OpenAQ v3 `/locations` geo-radius query | ✅ Real |
| Active station filter | `datetimeLast` within 60 days | ✅ Real |
| Pollutant readings | OpenAQ `/locations/{id}/latest` | ✅ Real (with API key) |
| US AQI calculation | EPA standard breakpoints | ✅ Real |

### What is missing
- Without an API key, AQI values fall back to Open-Meteo's regional estimate (less granular).
- No historical trend chart — only point-in-time readings.
- No correlation display between AQI hot spots and heat islands on the same view.

### How to test
1. Add `OPENAQ_API_KEY = "your-key"` to `.streamlit/secrets.toml`
2. Select **Los Angeles, CA** or **London, UK**
3. Enable **Air Quality** layer
4. Click on a coloured sensor dot → verify tooltip shows a real `OAQ-<id>`, pollutant type (PM2.5/O3), and AQI value
5. Without API key: verify dots still appear but AQI shows a uniform regional estimate

**Expected result:** Coloured sensor network visible; with API key each dot has a distinct, real AQI reading.

---

## UC-05 · Dynamic Heat Risk Index

**Status:** ✅ Live

### What it demonstrates
A composite **Heat Risk Index (0–100)** is calculated dynamically based on real-time environmental factors (local temperature and OpenAQ air quality), grounded in WHO and US NWS thresholds. It replaces arbitrary static scoring with a live, actionable gauge of immediate biological thermal stress.

### What makes it real
The formula uses real-world thresholds:
- **Thermal Factor (60%):** Curves upward sharply between 25°C and 40°C.
- **Air Quality Factor (40%):** Maps EPA AQI bands (0-300+) to risk penalties.
- **Diurnal Modifier:** Applies a 1.2x stress multiplier during peak afternoon hours (12:00–16:00).
The result categorizes the city's status into 'Low', 'Moderate', 'High', or 'Extreme' risk.

### What is missing
- No historical tracking (score today vs. 1 year ago).
- Does not currently factor in specific humidity/wet-bulb temperature, which is the gold standard for human thermal limit modeling.

### How to test
1. Select **Singapore** or **Cairo** — note the Heat Risk Index and its categorical label.
2. Drag the temporal slider to peak afternoon (14:00) — observe the Heat Risk Index actively increasing due to diurnal multipliers.
3. Enter Sandbox mode → simulate interventions on concrete masses → watch the Index dynamically adjust downward as simulated cooling is applied.

**Expected result:** The Risk Index responds fluidly to temporal changes, live data, and hypothetical sandbox interventions.

---

## UC-06 · Sandbox — Intervention Simulator

**Status:** ✅ Live

### What it demonstrates
The **Sandbox** is the system's "Act" layer. Users click any mapped asset (building, road, park) and the AI proposes a context-aware cooling intervention:
- **Concrete Mass** → 500 m² Intensive Green Roof (−0.4°C, $150k)
- **Road/Transit Artery** → Bioswale & Canopy Corridor (−0.7°C, $300k)
- **Other** → Albedo Enhancement (−0.2°C, $50k)

Each intervention: decrements the $5M sandbox budget, adds a coloured overlay circle on the map, mints a Nature ID hash, and appends a row to the Green Ledger. The `Avg Surface Temp` metric and Resilience Score update live.

### What is missing
- Intervention ROI figures (energy savings, ER visits avoided) are hardcoded, not computed from real local data.
- No "undo last intervention" — only "Clear All."
- No spatial constraint: you can place interventions on top of each other or on water.
- Budget depletion does not prevent further interventions (no guard).

### How to test
1. Click **Launch Sandbox**
2. Enable **Buildings** layer → click a building on the map
3. Verify: chat shows ANALYZE / PROPOSE / ROI block; map shows a coloured radius circle; budget decreases; `Avg Surface Temp` drops
4. Enable **Traffic** layer → click a highway → verify Bioswale intervention proposed
5. Open **Green Ledger** → verify the intervention row was appended with a Nature ID hash
6. Click **Clear Interventions** → verify map resets and budget restores to $5M

**Expected result:** Each click produces a differentiated, contextual intervention proposal and updates all dashboard metrics simultaneously.

---

## UC-07 · Green Ledger / Verifiable Data Provenance (VDP)

**Status:** ⚠️ Partially implemented

### What it demonstrates
The **Green Ledger** is the trust layer of the system. It records every simulated cooling intervention with a timestamp, Nature ID hash, target asset, intervention type, and cooling impact — simulating a cryptographically signed audit trail. This is the prototype of the "blockchain anchor" described in the architecture.

### What makes it real
- The ledger table schema exists in SQLite (`database.py`) with `save_ledger_entry()` / `load_ledger_entries()` fully implemented.
- The Sandbox mints new Nature ID hashes and appends rows to `st.session_state.green_ledger` (visible in the UI table).

### What is missing
| Gap | Details | Effort |
|-----|---------|--------|
| Session persistence | Ledger lives in `session_state` only — cleared on page refresh. `database.py` functions exist but are never called. | 🔧 Low (wire up `save_ledger_entry()` in `agent_logic.py`) |
| Real cryptographic hash | Nature ID is a random hex string, not a deterministic hash of sensor data + timestamp. | 🔨 Medium (SHA-256 over asset payload) |
| Blockchain anchor | Currently just a simulated button — no actual on-chain write (Ethereum/Polygon/Ceramic). | 🏗️ High |
| Auditor Agent | No automatic comparison of claimed cooling vs. measured temperature delta. | 🏗️ High |

### How to test
1. Enter **Sandbox** → add 2–3 interventions
2. Open **Green Ledger** expander → verify table shows Nature IDs, cooling claims, timestamps
3. Click **⚙️ Simulate Legacy Verification** → verify simulated blockchain hash in chat
4. Refresh the page → notice ledger is lost (demonstrates the missing persistence gap)

**Expected result (current):** Ledger populates during session. **Expected result (after fix):** Ledger survives page refresh because rows are written to SQLite.

---

## UC-08 · Agentic Digital Twin Asset Profiling

**Status:** ✅ Live

### What it demonstrates
Clicking any nature or infrastructure asset triggers an immediate contextual analysis by the **Gaia Agent**. Rather than a static data card, the AI evaluates the asset's specific role in the local bio-region (e.g., identifying a tree as a terrestrial cooling anchor vs. a road as an urban heat island friction point) and suggests three precise follow-up actions to simulate.

### What makes it real
- Asset identity, spatial geometry, and classification come directly from real OSM element tags.
- The agent's reasoning is injected with the city's live thermal data and the specific category of the asset clicked (Hydrological, Terrestrial, Infrastructure).

### What is missing
| Gap | Details | Effort |
|-----|---------|--------|
| Multi-asset selection | Currently only analyzes one asset at a time; cannot select an entire block or neighbourhood for aggregate profiling. | 🔨 Medium |
| Algorithmic carbon estimates | Carbon sequestration figures in sandbox simulations are static heuristics, not calculated from actual species DBs like i-Tree. | 🏗️ High |

### How to test
1. Ensure **Tree Canopy** or **Buildings** layer is enabled (Sandbox OFF).
2. Click a specific building or tree on the map.
3. Check the chat panel — verify the Gaia Agent immediately posts a contextual breakdown of that asset type along with 1-3 suggested next simulation steps.
4. Click 'Launch Sandbox' and click the same asset to execute an intervention.

**Expected result:** Every map feature serves as a clickable prompt that anchors the AI's reasoning to a specific spatial coordinate.

---

## UC-09 · Agentic Sense → Plan → Act → Reflect Loop

**Status:** ⚠️ Partially implemented (3 of 4 phases live)

### What it demonstrates
The core Planetary Intelligence loop: the system **Senses** environmental data, **Plans** interventions, **Acts** via the sandbox, and ideally **Reflects** by comparing outcomes. Three pre-built scenarios plus a free-text interface demonstrate agentic reasoning.

### Phases currently live
| Phase | Feature | Implementation |
|-------|---------|----------------|
| **SENSE** | Analyze City Heat Risk | Scans for thermal anomalies, correlates heat islands with canopy gaps |
| **SENSE** | Map Data Deserts | Identifies areas with no sensor coverage |
| **PLAN** | Map Thermal Risk | Proposes multi-species tree planting + albedo coating |
| **ACT** | Sandbox Intervention | Executes proposed intervention on a specific asset |
| **REFLECT** | ❌ Auditor Agent | Not implemented — no automated comparison of pre/post temperatures |

### What is missing
| Gap | Details | Effort |
|-----|---------|--------|
| Reflect / Auditor loop | After simulating an intervention, there is no code path that re-queries the Open-Meteo API, compares the delta, and issues a VDP-signed verdict. | 🏗️ High |
| Persistent memory | Each session starts fresh — the agent has no memory of past interventions or city baselines. | 🏗️ High |

### How to test
1. Select a city. The Agent will immediately perform an automatic **Node Briefing** characterizing the current bio-region.
2. Click **Analyze City Heat Risk** → verify chat shows SENSE / REASON / PLAN block with localized context.
3. Click **Map Data Deserts** → verify PLAN shows IoT node placement.
4. Click into the chat input, type *"Activate the thermal layer"* → verify the layer toggles ON automatically.

**Expected result:** Quick actions produce distinct, structured reasoning chains; map clicks bridge spatial data to AI reasoning.

---

## UC-10 · Multi-City / Bio-Region Comparison

**Status:** ⚠️ Partial (sequential, not simultaneous)

### What it demonstrates
The system supports 13 cities across 4 continents, each with calibrated OSM radii and UTC offsets. Switching cities reloads all real data — demonstrating global scalability of the spine.

### What is missing
| Gap | Details | Effort |
|-----|---------|--------|
| Side-by-side city comparison | Currently only one city view at a time — no split screen or overlay comparison mode. | 🔨 Medium |
| City-scoped Green Ledger | Ledger entries don't currently record which city they belong to (the `city` column exists in `database.py` but is not passed from the sandbox flow). | 🔧 Low |
| Cities in the Global South | Only 2 of 13 cities are in Africa/MENA (Cairo) + Southern Asia (Mumbai). Adding Freetown, Nairobi, Dhaka would align with the stated mission of serving "data deserts." | 🔧 Low |

### How to test
1. Select **Singapore** → note resilience score and visible asset count
2. Select **Cairo, Egypt** → compare (lower tree count, lower resilience score)
3. Select **Tokyo, Japan** → compare density and building layer detail
4. Slide temporal slider for each → verify NOW marker shifts per city timezone

**Expected result:** Each city loads distinct real data; resilience score varies with actual green infrastructure; timezone is accurate per city.

---

## UC-11 · AI-Generated Briefing Report (PDF)

**Status:** ✅ Live (requires `OPENAI_API_KEY`)

### What it demonstrates
With one click, the system generates a **formal bio-regional resilience briefing** using GPT-4o-mini, injecting the current screen context (city, temperature, resilience score, active layers) as the system prompt. The report is rendered to PDF via `markdown-pdf` and offered as a download. This demonstrates the system's ability to produce **decision-ready outputs** for municipal stakeholders.

### What is missing
- Without an OpenAI key, the button does nothing (should at least produce a static template).
- The report does not include map screenshots or the Green Ledger table.
- No custom sections — a heat officer cannot request specific sections (e.g., budget breakdown, neighbourhood-specific analysis).

### How to test
1. Configure `OPENAI_API_KEY` in `.streamlit/secrets.toml`
2. Select **New York City, USA**, enable Thermal + Trees layers
3. Click **📄 Generate Briefing Report**
4. Wait for spinner → click **Download PDF Briefing**
5. Verify PDF contains: city name, temperature reading, resilience score, layer context, recommendations

**Expected result:** A multi-section Markdown-rendered PDF with the city's live dashboard context embedded.

---

## UC-12 · Data Desert Detection / IoT Sensor Gap Mapping

**Status:** ⚠️ Partial (simulated narrative, partial real data)

### What it demonstrates
The system identifies areas where sensor coverage is absent — "data deserts" — which is the first step in deploying a decentralised IoT mesh. The **Scan for Data Deserts** button triggers a narrative showing 8 optimal proposed IoT node locations. The real OpenAQ layer already shows where coverage exists, implicitly revealing where it doesn't.

### What is missing
| Gap | Details | Effort |
|-----|---------|--------|
| Spatial gap algorithm | No code computes actual sensor density vs. population/heat exposure to identify true deserts. | 🔨 Medium (Voronoi gap analysis on OpenAQ stations) |
| Proposed node visualisation | The "8 optimal locations" are mentioned in chat text only — not rendered on the map. | 🔨 Medium |
| Ground sensor data | All sensor data comes from stationary reference stations, not low-cost IoT devices. | 🏗️ High (requires hardware integration) |

### How to test
1. Enable **Air Quality** layer for **Cairo, Egypt** or **Mexico City, Mexico**
2. Observe sparse sensor coverage compared to **London** or **Los Angeles**
3. Click **Scan for Data Deserts** → verify agent describes IoT node deployment plan in the chat

**Expected result:** Sensor gap is visually obvious from the Air Quality layer; agent narrates a deployment strategy.

---

## UC-13 · Parametric Finance / Green Bond Verification

**Status:** ❌ Simulated only

### What it demonstrates
The **⚙️ Simulate Legacy Verification** button in the Green Ledger panel shows the concept: after an intervention claim is made, an Auditor Agent compares the claim against signed sensor data and seals the result to a blockchain with an immutable hash. This would be the mechanism for triggering automated green bond payouts when verified cooling milestones are met.

### What is missing
| Gap | Details | Effort |
|-----|---------|--------|
| Real pre/post temperature comparison | No code fetches temperature before and after a simulated intervention to compute a real delta. | 🔨 Medium |
| Cryptographic hash of real data | Hash is `random.randint` — not derived from actual readings. | 🔨 Medium (SHA-256 over payload) |
| Smart contract / parametric trigger | No integration with any blockchain or insurance protocol. | 🏗️ High |
| Finance module UI | No dedicated screen for funders to view verified impact claims. | 🏗️ High |

### How to test
1. Enter Sandbox → add interventions → open **Green Ledger**
2. Click **⚙️ Simulate Legacy Verification**
3. Verify chat shows: `[REFLECT]` comparison, `[VERIFY]` impact statement, `[BLOCKCHAIN]` fake hash
4. Discuss with stakeholders: "This is what a real VDP-signed payout trigger would look like — the hash would be written on-chain."

**Expected result:** The scenario is clearly labelled as a simulation; the narrative flow demonstrates the full provenance chain for an investor audience.

---

## UC-14 · User Authentication / Multi-Stakeholder Access

**Status:** ✅ Live

### What it demonstrates
The system uses **Supabase** for email/password and Google OAuth authentication — gating the entire dashboard behind a login wall. This demonstrates the multi-stakeholder access model: different users (Heat Officers, Utility Providers, Climate Funders) would eventually see role-specific dashboards.

### What is missing
- All authenticated users see the same dashboard — there are no roles or permission levels.
- Session persistence via cookies (`extra-streamlit-components`) is unreliable in the current implementation.
- No profile page or user-specific saved state (favourite cities, custom ledger views).

### How to test
1. Open app at `localhost:8501` (unauthenticated)
2. Verify the login/signup screen blocks dashboard access
3. Sign up with a test email → verify auto-login after registration
4. Log out → verify session is cleared and dashboard is inaccessible
5. Log back in → verify dashboard loads with previous city data

**Expected result:** Login gates the dashboard; sign-up creates an account and auto-logs in; logout clears session.

---

## Showcase Order Recommendation

For a live demo to investors or city partners, run the use cases in this order:

```text
1. UC-14 → Log in (establish trust & access control)
2. UC-01 → Show Nature ID assets for Singapore or London (anchor in real data)
3. UC-02 → Enable Thermal Heatmap (visual wow moment)
4. UC-03 → Drag time slider to 14:00 → 04:00 (demonstrate smooth diurnal intelligence data reuse)
5. UC-04 → Show Air Quality sensor network (multi-sensor IoT)
6. UC-05 → Highlight the Dynamic Heat Risk Index (WHO/EPA thresholds)
7. UC-09 → Agent gives automatic City Briefing on load. Click "Analyze City Heat Risk".
8. UC-08 → Click a building on the map to trigger an AI Digital Twin Context Profile
9. UC-06 → Launch Sandbox → click that same building → show intervention + ROI
10. UC-07 → Open Green Ledger → show minted Nature IDs → "Simulate Legacy Verification"
11. UC-11 → Click "Generate Briefing" → download PDF (leave stakeholder with a report)
```

---

*Last updated: 2026-02-21 · Embodying Planetary Intelligence.*
