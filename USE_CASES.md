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

*Add new use cases below as they are validated.*
