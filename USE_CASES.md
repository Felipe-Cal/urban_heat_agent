# Gaia Heat Sync — Real Use Cases

This document tracks validated use cases for the platform. Each entry includes a description, what real data backs it, and a test protocol any user can follow to verify it works.

---

## UC-01 · Cooling Asset Inventory for a Heat Officer

**Status:** ✅ Live (as of 2026-02-20)

### What it does
A city heat officer or emergency planner opens the platform before or during a heatwave to see exactly what cooling infrastructure exists in a neighbourhood — every tree, park, drinking fountain, cooling shelter, green roof, community garden, and wetland within a 1.5 km radius of the city centre.

All locations come from **OpenStreetMap**, a continuously updated open geodatabase. Where OSM data is well-maintained (e.g. Los Angeles, London, Singapore), the inventory is highly accurate and includes operational details.

### What makes it real
| Data field | Source | Real? |
|---|---|---|
| Asset locations (lat/lon) | OpenStreetMap Overpass API | ✅ Real |
| Asset names | OSM `name` tag | ✅ Real |
| Opening hours | OSM `opening_hours` tag | ✅ Real |
| Live open/closed status | Parsed from `opening_hours` vs. current time | ✅ Real |
| Operator name | OSM `operator` tag | ✅ Real (where mapped) |
| Capacity | OSM `capacity` tag | ✅ Real (where mapped) |
| Air conditioning | OSM `air_conditioning` tag | ✅ Real (where mapped) |
| Street address | OSM `addr:street` + `addr:housenumber` | ✅ Real (where mapped) |
| Wheelchair access | OSM `wheelchair` tag | ✅ Real (where mapped) |
| Contact phone | OSM `phone` / `contact:phone` | ✅ Real (where mapped) |

### Limitations
- OSM tag coverage varies by city. LA and Singapore are well-mapped; Cairo and Mumbai have sparser operational data.
- The **cooling impact °C** shown in tooltips is a modelled estimate (not a measured sensor reading).
- Opening hours are parsed from the OSM string format — complex schedules (e.g. seasonal variations) may show "Check Hours" instead of a live status.

### How to test

1. Open the app at the Streamlit Cloud URL (or `localhost:8501`)
2. Select a city from the dropdown — try **London, UK** or **Singapore** for best OSM coverage
3. In the **NATURE ID ASSETS** section (right panel), activate:
   - `🌳 Tree Canopy`
   - `🏛️ Cooling Centers`
   - `💧 Drinking Fountains`
   - `🌳 Public Parks`
4. Click on any amber dot (Cooling Center) on the map
5. Verify the tooltip shows:
   - A 🟢 **Open Now** / 🔴 **Closed** badge based on real opening hours
   - At minimum: Name, Asset ID, Type
   - Where OSM data is available: Address, Operator, Capacity, AC status, Wheelchair access
6. Click on a blue dot (Drinking Fountain)
7. Verify the tooltip shows whether access is free, wheelchair-accessible, and whether it is seasonal

**Expected result:** Each clicked asset shows a structured tooltip with real operational data sourced directly from OpenStreetMap, not generated content.

---

## UC-02 · Real Thermal Surface Temperature Heatmap

**Status:** ✅ Live (as of 2026-02-20)

### What it does
A city stakeholder explores the temperature distribution across a neighbourhood to identify Urban Heat Islands (UHIs) and correlate them with the lack of green infrastructure or presence of heavy built environment. The thermal layer displays an interpolated heatmap of real surface temperatures.

### What makes it real
| Data field | Source | Real? |
|---|---|---|
| Land Surface Temperature (LST) | Open-Meteo `soil_temperature_0cm` API | ✅ Real |
| Spatial Sampling | ~3 km grid around city centre | ✅ Real |

*Note: The platform previously used synthetic Gaussian blobs centred on the city, but now fetches real model-derived skin/surface temperature data matching remote sensing paradigms like MODIS L1B/L2.*

### Limitations
- The Open-Meteo spatial resolution is typically between 1 km and 11 km depending on the underlying weather model (e.g., HRRR, ICON D2), meaning micro-urban variations (e.g., one street vs the next) might be smoothed out compared to direct satellite imagery.
- During high API load or network timeouts, the layer falls back to a sparse synthetic grid to ensure continuous visual presence.

### How to test

1. Open the app at the Streamlit Cloud URL (or `localhost:8501`)
2. Select an urban focus area (like **Los Angeles, CA** or **Singapore**)
3. In the **SATELLITE INDICES** section (left panel), activate:
   - `🌡️ Thermal Heatmap`
4. Verify the heatmap is displayed. It should follow an irregular, natural spatial pattern (hot spots and cool spots corresponding to local weather models), not a perfectly symmetric circle.
5. In your browser's Developer Tools (Network tab), filter requests by `open-meteo.com` and reload the page. Verify a batch request containing `current=soil_temperature_0cm` and a long string of comma-separated latitudes/longitudes is made.

**Expected result:** The map displays a realistic thermal overlay sourced via a batch API call, rather than a uniformly decaying synthetic circle.

---

*Add new use cases below as they are validated.*
