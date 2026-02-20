"""
Data generation module for Gaia Heat Sync.

Fetches real temperature/AQI from Open-Meteo and real geographic assets from
OpenStreetMap (Overpass API), then synthesises supplementary mock data for
layers not available via OSM.

Returns a CityData dataclass instead of a positional tuple.
"""
import json
import os
import random
import re
import string
from datetime import date, datetime, time as dtime
from typing import Callable, Optional, List, Dict, Any

import numpy as np
import pandas as pd
import requests
import streamlit as st

from modules.models import CityData


# ---------------------------------------------------------------------------
# Caching Decorators (using Streamlit's native caching)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def _fetch_current_weather(lat: float, lon: float) -> tuple[float, int]:
    """Fetch current temperature and AQI from Open-Meteo."""
    current_temp: float = 30.0  # Fallback
    current_aqi: int = 45       # Fallback

    try:
        meteo_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&current=temperature_2m"
        )
        meteo_resp = requests.get(meteo_url, timeout=5)
        if meteo_resp.status_code == 200:
            current_temp = float(
                meteo_resp.json().get("current", {}).get("temperature_2m", 30.0)
            )

        aqi_url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality"
            f"?latitude={lat}&longitude={lon}&current=us_aqi"
        )
        aqi_resp = requests.get(aqi_url, timeout=5)
        if aqi_resp.status_code == 200:
            current_aqi = int(
                aqi_resp.json().get("current", {}).get("us_aqi", 45)
            )
    except Exception as e:
        print(f"Error fetching Open-Meteo APIs: {e}")

    return current_temp, current_aqi

@st.cache_data(ttl=86400) # Cache for 24 hours
def _fetch_thermal_raw_grid(lats_str: str, lons_str: str) -> Optional[List[Optional[float]]]:
    """Fetch raw thermal grid data from Open-Meteo."""
    try:
        thermal_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lats_str}&longitude={lons_str}"
            f"&current=soil_temperature_0cm&temperature_unit=celsius"
        )
        thermal_resp = requests.get(thermal_url, timeout=10)
        if thermal_resp.status_code == 200:
            results = thermal_resp.json()
            raw_temps = []
            if isinstance(results, list):
                for res in results:
                    t = res.get("current", {}).get("soil_temperature_0cm")
                    raw_temps.append(t)
            elif isinstance(results, dict):
                 # Handle single point case if API returns dict instead of list
                 t = results.get("current", {}).get("soil_temperature_0cm")
                 raw_temps.append(t)
            return raw_temps
        else:
            return None
    except Exception as e:
        print(f"Error fetching real thermal grid: {e}")
        return None

@st.cache_data(ttl=86400) # Cache for 24 hours
def _fetch_osm_infrastructure(lat: float, lon: float, radius: int) -> dict:
    """Fetch infrastructure data from Overpass API."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      node["natural"="tree"](around:{radius},{lat},{lon});
      nwr["natural"="water"](around:{radius},{lat},{lon});
      nwr["leisure"="park"](around:{radius},{lat},{lon});
      nwr["amenity"~"shelter|community_centre"](around:{radius},{lat},{lon});
      node["amenity"="drinking_water"](around:{radius},{lat},{lon});
      nwr["green_roof"="yes"](around:{radius},{lat},{lon});
      nwr["roof:material"="grass"](around:{radius},{lat},{lon});
      nwr["landuse"="allotments"](around:{radius},{lat},{lon});
      nwr["leisure"="garden"](around:{radius},{lat},{lon});
      nwr["landuse"="forest"](around:{radius},{lat},{lon});
      nwr["natural"="wood"](around:{radius},{lat},{lon});
      nwr["natural"="wetland"](around:{radius},{lat},{lon});
      way["building"](around:{radius // 2},{lat},{lon});
      way["highway"~"motorway|trunk|primary"](around:{radius},{lat},{lon});
    );
    out geom;
    """
    try:
        response = requests.get(overpass_url, params={"data": query}, timeout=25)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 504:
            return {"error": "Gateway Timeout", "elements": []}
        elif response.status_code == 429:
            return {"error": "Rate Limit", "elements": []}
        else:
             return {"error": f"HTTP {response.status_code}", "elements": []}
    except requests.exceptions.Timeout:
        return {"error": "Timeout", "elements": []}
    except Exception as e:
        return {"error": str(e), "elements": []}

@st.cache_data(ttl=3600)
def _fetch_openaq_sensors_cached(center_lat: float, center_lon: float, radius_m: int = 25_000, limit: int = 25) -> list:
    """Fetch OpenAQ sensors (cached wrapper)."""
    try:
        resp = requests.get(
            "https://api.openaq.org/v3/locations",
            params={
                "coordinates": f"{center_lat},{center_lon}",
                "radius": radius_m,
                "limit": limit,
            },
            headers={"accept": "application/json"},
            timeout=8,
        )
        if resp.status_code == 200:
             return resp.json().get("results", [])
    except Exception:
        pass
    return []


def generate_mock_data(
    center_lat: float = 34.0522,
    center_lon: float = -118.2437,
    time_of_day: str = "14:00",
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> CityData:
    """
    Generate all map/dashboard data for a city snapshot.

    Args:
        center_lat: Latitude of the city centre.
        center_lon: Longitude of the city centre.
        time_of_day: Time string in "HH:MM" format.
        progress_callback: Optional callable(message, percent) for progress UI.

    Returns:
        CityData dataclass with all DataFrames and scalar metrics.
    """

    def _progress(msg: str, pct: int) -> None:
        if progress_callback:
            progress_callback(msg, pct)

    _progress("Initializing orbital thermal imaging...", 10)

    # -------------------------------------------------------------------------
    # 1. Live temperature + AQI from Open-Meteo
    # -------------------------------------------------------------------------
    current_temp, current_aqi = _fetch_current_weather(center_lat, center_lon)
    fetch_error: Optional[str] = None

    # Diurnal temperature variation (min at ~4am, max at ~3pm; ~10°C swing)
    try:
        hour = int(time_of_day.split(":")[0])
    except (ValueError, IndexError):
        hour = 14

    temp_variation = -5.0 * np.cos((hour - 4) * np.pi / 11.0)
    current_temp += temp_variation

    if hour in [7, 8, 9, 16, 17, 18]:
        current_aqi += random.randint(10, 20)
    elif hour < 6 or hour > 20:
        current_aqi = max(0, current_aqi - random.randint(5, 15))

    # -------------------------------------------------------------------------
    # 2. Real thermal surface temperature (Open-Meteo LST grid)
    # -------------------------------------------------------------------------
    _progress("Acquiring Land Surface Temperature (LST) data...", 20)
    thermal_data = []
    
    # 10x10 grid (~3km radius total)
    steps = 10
    lat_step = 0.006  # ~670m
    lon_step = 0.006
    
    start_lat = center_lat - (lat_step * steps / 2)
    start_lon = center_lon - (lon_step * steps / 2)
    
    lats = []
    lons = []
    for i in range(steps):
        for j in range(steps):
            lats.append(round(start_lat + i * lat_step, 6))
            lons.append(round(start_lon + j * lon_step, 6))
            
    # Open-Meteo multi-point format: latitude=a,b,c&longitude=x,y,z
    lats_str = ",".join(map(str, lats))
    lons_str = ",".join(map(str, lons))
    
    max_theoretical_temp = 50.0

    raw_temps_grid = _fetch_thermal_raw_grid(lats_str, lons_str)

    if raw_temps_grid and len(raw_temps_grid) == len(lats):
        _progress("Processing thermal grid...", 25)

        # Substitute None values with current_temp
        raw_temps = []
        for t in raw_temps_grid:
            if t is None:
                raw_temps.append(current_temp)
            else:
                raw_temps.append(t)

        # Interpolate the rigid 10x10 grid onto a 1500-point random scatter 
        # using Inverse Distance Weighting (IDW) to create a smooth, organic heatmap
        grid_pts = np.column_stack((lats, lons))
        temps_arr = np.array(raw_temps)
        
        num_interp_points = 1500
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        rand_lats = np.random.uniform(min_lat, max_lat, num_interp_points)
        rand_lons = np.random.uniform(min_lon, max_lon, num_interp_points)
        rand_pts = np.column_stack((rand_lats, rand_lons))
        
        # Broadcasting to find distances (1500 x 100)
        rand_pts_exp = rand_pts[:, np.newaxis, :]
        grid_pts_exp = grid_pts[np.newaxis, :, :]
        
        dist_sq = np.sum((rand_pts_exp - grid_pts_exp) ** 2, axis=2)
        dist_sq[dist_sq == 0] = 1e-10  # prevent div by zero
        weights = 1.0 / dist_sq
        
        interp_temps = np.sum(weights * temps_arr, axis=1) / np.sum(weights, axis=1)
        
        for r_lon, r_lat, t in zip(rand_lons, rand_lats, interp_temps):
            # Add micro-variation to break contour banding
            t += random.uniform(-0.3, 0.3)
            weight = max(0.1, t / max_theoretical_temp)
            thermal_data.append([r_lon, r_lat, weight])
    else:
        # Fallback to sparse synthetic grid
        print("Falling back to synthetic thermal grid.")
        for _ in range(300):
                lat = center_lat + np.random.normal(0, 0.02)
                lon = center_lon + np.random.normal(0, 0.02)
                distance = np.sqrt((lat - center_lat) ** 2 + (lon - center_lon) ** 2)
                uhi_effect = max(0.0, 8 - distance * 200)
                temp = current_temp + random.uniform(0, uhi_effect)
                weight = max(0.1, temp / max_theoretical_temp)
                thermal_data.append([lon, lat, weight])

    df_thermal = pd.DataFrame(thermal_data, columns=["lon", "lat", "weight"])

    # -------------------------------------------------------------------------
    # 2b. Synthetic population density
    # -------------------------------------------------------------------------
    population_data = []
    for _ in range(300):
        p_lat = center_lat + np.random.normal(0, 0.025)
        p_lon = center_lon + np.random.normal(0, 0.025)
        distance = np.sqrt((p_lat - center_lat) ** 2 + (p_lon - center_lon) ** 2)
        weight = max(10, 100 - distance * 3500) + random.randint(0, 20)
        population_data.append({"lat": p_lat, "lon": p_lon, "weight": weight})

    # -------------------------------------------------------------------------
    # 3. OpenStreetMap — real nature + infrastructure assets
    # -------------------------------------------------------------------------
    tree_data: list = []
    water_data: list = []
    park_data: list = []
    shelter_data: list = []
    fountain_data: list = []
    green_roof_data: list = []
    garden_data: list = []
    forest_data: list = []
    wetland_data: list = []
    building_data: list = []
    traffic_data: list = []

    # Initialise raw element lists (used later for resilience score)
    trees, water, parks, shelters, fountains = [], [], [], [], []
    green_roofs, gardens, forests, wetlands = [], [], [], []

    _progress("Fetching OpenStreetMap infrastructure...", 30)

    radius_meters = 1500
    osm_resp = _fetch_osm_infrastructure(center_lat, center_lon, radius_meters)

    if "error" in osm_resp:
        fetch_error = f"\u26a0\ufe0f OpenStreetMap Error: {osm_resp['error']}. Map loaded without Nature ID assets."
        osm_elements = []
    else:
        osm_elements = osm_resp.get("elements", [])
        _progress("Processing geospatial elements...", 50)

    def get_coords(el: dict):
        """Extract a representative (lat, lon) from any OSM element type."""
        if "lat" in el and "lon" in el:
            return el["lat"], el["lon"]
        if el.get("type") == "way" and el.get("geometry"):
            mid = len(el["geometry"]) // 2
            return el["geometry"][mid]["lat"], el["geometry"][mid]["lon"]
        if el.get("type") == "relation":
            for member in el.get("members", []):
                if member.get("geometry"):
                    mid = len(member["geometry"]) // 2
                    return member["geometry"][mid]["lat"], member["geometry"][mid]["lon"]
        if "center" in el:
            return el["center"]["lat"], el["center"]["lon"]
        return None, None

    trees = [e for e in osm_elements if e.get("tags", {}).get("natural") == "tree"]
    water = [e for e in osm_elements if e.get("tags", {}).get("natural") == "water"]
    parks = [e for e in osm_elements if e.get("tags", {}).get("leisure") == "park"]
    shelters = [
        e for e in osm_elements
        if e.get("tags", {}).get("amenity") in ("shelter", "community_centre")
    ]
    fountains = [e for e in osm_elements if e.get("tags", {}).get("amenity") == "drinking_water"]
    green_roofs = [
        e for e in osm_elements
        if e.get("tags", {}).get("green_roof") == "yes"
        or e.get("tags", {}).get("roof:material") == "grass"
    ]
    gardens = [
        e for e in osm_elements
        if e.get("tags", {}).get("landuse") == "allotments"
        or e.get("tags", {}).get("leisure") == "garden"
    ]
    forests = [
        e for e in osm_elements
        if e.get("tags", {}).get("landuse") == "forest"
        or e.get("tags", {}).get("natural") == "wood"
    ]
    wetlands = [e for e in osm_elements if e.get("tags", {}).get("natural") == "wetland"]
    raw_buildings = [e for e in osm_elements if "building" in e.get("tags", {})]
    raw_traffic = [e for e in osm_elements if "highway" in e.get("tags", {})]

    # Buildings (PolygonLayer)
    for b_el in raw_buildings[:500]:
        if b_el.get("type") == "way" and b_el.get("geometry"):
            polygon = [[pt["lon"], pt["lat"]] for pt in b_el["geometry"]]
            levels = int(b_el.get("tags", {}).get("building:levels", random.randint(1, 8)))
            height = levels * 3.5
            lat, lon = get_coords(b_el)
            building_data.append({
                "polygon": polygon,
                "height": height,
                "lon": lon,
                "lat": lat,
                "asset_id": f"BLDG-{b_el['id']}",
                "name": b_el.get("tags", {}).get("name", "Urban Structure"),
                "type": "Concrete Mass",
                "tooltip": _building_tooltip(b_el["id"], height),
            })

    # Population density: replace synthetic Gaussian with real OSM building centroids.
    # More floors -> more occupants -> higher density weight.
    if building_data:
        population_data = [
            {
                "lat": b["lat"],
                "lon": b["lon"],
                "weight": max(10, b.get("height", 7.0) / 3.5 * 15),
            }
            for b in building_data
            if b.get("lat") and b.get("lon")
        ]

    # Traffic (PathLayer)
    for t_el in raw_traffic[:200]:
        if t_el.get("type") == "way" and t_el.get("geometry"):
            path = [[pt["lon"], pt["lat"]] for pt in t_el["geometry"]]
            lat, lon = get_coords(t_el)
            hw_type = t_el.get("tags", {}).get("highway", "road")
            traffic_data.append({
                "path": path,
                "lon": lon,
                "lat": lat,
                "asset_id": f"TRAFFIC-{t_el['id']}",
                "name": t_el.get("tags", {}).get("name", "Transit Artery"),
                "type": hw_type.capitalize(),
                "tooltip": _traffic_tooltip(t_el["id"], hw_type),
            })

    def process_assets(elements, data_list, asset_prefix, default_name, asset_type, color, limit=500):
        for element in elements[:limit]:
            lat, lon = get_coords(element)
            if lat is None or lon is None:
                continue
            tags = element.get("tags", {})
            name = tags.get("name", default_name)
            impact_html = _impact_html(asset_prefix)
            data_list.append({
                "lon": lon,
                "lat": lat,
                "asset_id": f"{asset_prefix}-{element['id']}",
                "name": name,
                "type": asset_type,
                "health": "Verified",
                "owner": "Public/Private",
                "color": color,
                "tooltip": _asset_tooltip(name, asset_prefix, element["id"], asset_type, impact_html),
            })

    # Trees — special handling for species
    for element in trees[:1000]:
        lat, lon = get_coords(element)
        if lat is None or lon is None:
            continue
        tags = element.get("tags", {})
        species = tags.get("species") or tags.get("genus") or "Real Tree"
        temp_offset = round(random.uniform(0.1, 1.2), 1)
        impact_html = f"<div style='color: #10b981; font-weight: bold; margin-top: 6px;'>\U0001f321\ufe0f Cooling Impact: -{temp_offset}\u00b0C</div>"
        tree_data.append({
            "lon": lon, "lat": lat,
            "asset_id": f"TREE-{element['id']}",
            "name": species,
            "type": "Tree Canopy",
            "health": "Verified",
            "owner": "Public",
            "color": [5, 150, 105, 200],
            "tooltip": _asset_tooltip(species, "TREE", element["id"], "Tree Canopy", impact_html),
        })

    process_assets(water, water_data, "WATER", "Water Body", "Water Resource", [14, 165, 233, 200], 500)
    process_assets(parks, park_data, "PARK", "Public Park", "Urban Park", [132, 204, 22, 200], 500)
    process_assets(green_roofs, green_roof_data, "ROOF", "Green Roof", "Eco Infrastructure", [163, 230, 53, 200], 200)
    process_assets(gardens, garden_data, "GARDEN", "Community Garden", "Bio-Asset", [77, 124, 15, 200], 300)
    process_assets(forests, forest_data, "FOREST", "Urban Forest", "Woodland", [21, 128, 61, 200], 200)
    process_assets(wetlands, wetland_data, "WETLAND", "Wetland", "Natural Marsh", [12, 74, 110, 200], 100)

    # Shelters — rich tag extraction (opening hours, capacity, AC, address)
    for element in shelters[:200]:
        lat, lon = get_coords(element)
        if lat is None or lon is None:
            continue
        tags = element.get("tags", {})
        name = tags.get("name", "Cooling Center")
        shelter_data.append({
            "lon": lon, "lat": lat,
            "asset_id": f"SHELTER-{element['id']}",
            "name": name,
            "type": "Emergency Shelter",
            "health": "Verified",
            "owner": tags.get("operator", "Public"),
            "color": [245, 158, 11, 200],
            "tooltip": _shelter_tooltip(name, element["id"], tags),
        })

    # Fountains — rich tag extraction (operator, fee, wheelchair)
    for element in fountains[:200]:
        lat, lon = get_coords(element)
        if lat is None or lon is None:
            continue
        tags = element.get("tags", {})
        name = tags.get("name", "Drinking Fountain")
        fountain_data.append({
            "lon": lon, "lat": lat,
            "asset_id": f"FOUNTAIN-{element['id']}",
            "name": name,
            "type": "Hydration Access",
            "health": "Verified",
            "owner": tags.get("operator", "Public"),
            "color": [56, 189, 248, 200],
            "tooltip": _fountain_tooltip(name, element["id"], tags),
        })

    # -------------------------------------------------------------------------
    # 4. Air quality sensor nodes  (real locations from OpenAQ v3)
    # -------------------------------------------------------------------------
    _progress("Connecting to OpenAQ sensor network...", 75)

    openaq_results = _fetch_openaq_sensors_cached(center_lat, center_lon, radius_meters)
    sensor_data = []

    if openaq_results:
        for loc in openaq_results:
            coords = loc.get("coordinates", {})
            lat = coords.get("latitude")
            lon = coords.get("longitude")
            if lat is None or lon is None:
                continue
            sensor_id = f"OAQ-{loc.get('id', _make_sensor_id())}"
            local_aqi = max(0, current_aqi + random.randint(-15, 25))
            if local_aqi < 50:
                color = [16, 185, 129, 200]
            elif local_aqi < 100:
                color = [245, 158, 11, 200]
            else:
                color = [239, 68, 68, 200]
            sensor_data.append({
                "lon": lon, "lat": lat,
                "sensor_id": sensor_id,
                "aqi": local_aqi,
                "color": color,
                "tooltip": _sensor_tooltip(sensor_id, local_aqi, lat, lon),
            })

    if not sensor_data:
        # Fallback: synthetic locations when OpenAQ is unavailable
        for _ in range(25):
            lat = center_lat + np.random.normal(0, 0.03)
            lon = center_lon + np.random.normal(0, 0.03)
            sensor_id = _make_sensor_id()
            local_aqi = max(0, current_aqi + random.randint(-15, 25))
            if local_aqi < 50:
                color = [16, 185, 129, 200]   # Emerald
            elif local_aqi < 100:
                color = [245, 158, 11, 200]   # Amber
            else:
                color = [239, 68, 68, 200]    # Red
            sensor_data.append({
                "lon": lon, "lat": lat,
                "sensor_id": sensor_id,
                "aqi": local_aqi,
                "color": color,
                "tooltip": _sensor_tooltip(sensor_id, local_aqi, lat, lon),
            })

    # -------------------------------------------------------------------------
    # 5. Satellite indices (synthetic)
    # -------------------------------------------------------------------------
    _progress("Generating bio-regional data structures...", 90)

    ndvi_data = []
    for _ in range(400):
        lat = center_lat + np.random.normal(0, 0.02)
        lon = center_lon + np.random.normal(0, 0.02)
        distance = np.sqrt((lat - center_lat) ** 2 + (lon - center_lon) ** 2)
        ndvi_val = min(1.0, 0.2 + distance * 10 + random.uniform(0, 0.2))
        ndvi_data.append([lon, lat, ndvi_val])

    albedo_data = []
    for _ in range(400):
        lat = center_lat + np.random.normal(0, 0.02)
        lon = center_lon + np.random.normal(0, 0.02)
        distance = np.sqrt((lat - center_lat) ** 2 + (lon - center_lon) ** 2)
        albedo_val = max(0.1, 0.8 - distance * 15 + random.uniform(-0.1, 0.1))
        albedo_data.append([lon, lat, albedo_val])

    # -------------------------------------------------------------------------
    # 6. Climate resilience score
    # -------------------------------------------------------------------------
    score_trees = min(len(trees) * 0.1, 25)
    score_parks = min(len(parks) * 1.0, 15)
    score_forests = min(len(forests) * 2.0, 15)
    score_water = min(len(water) * 1.5, 10)
    score_wetlands = min(len(wetlands) * 3.0, 5)
    score_gardens = min(len(gardens) * 1.0, 10)
    score_green_roofs = min(len(green_roofs) * 2.0, 5)
    score_shelters = min(len(shelters) * 2.0, 10)
    score_fountains = min(len(fountains) * 1.0, 5)
    resilience_score = int(
        score_trees + score_parks + score_forests + score_water
        + score_wetlands + score_gardens + score_green_roofs
        + score_shelters + score_fountains
    )
    if resilience_score == 0:
        resilience_score = random.randint(45, 65)

    _progress("Complete.", 100)

    return CityData(
        df_thermal=pd.DataFrame(thermal_data, columns=["lon", "lat", "weight"]),
        df_trees=pd.DataFrame(tree_data),
        df_water=pd.DataFrame(water_data),
        df_parks=pd.DataFrame(park_data),
        df_shelters=pd.DataFrame(shelter_data),
        df_fountains=pd.DataFrame(fountain_data),
        df_green_roofs=pd.DataFrame(green_roof_data),
        df_gardens=pd.DataFrame(garden_data),
        df_forests=pd.DataFrame(forest_data),
        df_wetlands=pd.DataFrame(wetland_data),
        df_sensors=pd.DataFrame(sensor_data),
        df_ndvi=pd.DataFrame(ndvi_data, columns=["lon", "lat", "weight"]),
        df_albedo=pd.DataFrame(albedo_data, columns=["lon", "lat", "weight"]),
        df_buildings=pd.DataFrame(building_data),
        df_traffic=pd.DataFrame(traffic_data),
        df_population=pd.DataFrame(population_data),
        resilience_score=resilience_score,
        current_temp=current_temp,
        current_aqi=current_aqi,
        fetch_error=fetch_error,
    )


# ---------------------------------------------------------------------------
# Private tooltip / ID helpers  (keeps long HTML strings out of business logic)
# ---------------------------------------------------------------------------

def _make_sensor_id() -> str:
    """Generate a random AQ sensor ID without needing the Faker library."""
    digits = "".join(random.choices(string.digits, k=2))
    letters = "".join(random.choices(string.ascii_uppercase, k=2))
    return f"AQ-{digits}{letters}"


def _impact_html(asset_prefix: str) -> str:
    if asset_prefix in ("TREE", "PARK", "WATER", "FOREST", "ROOF", "GARDEN", "WETLAND"):
        temp_offset = round(random.uniform(0.5, 2.5), 1)
        return f"<div style='color: #10b981; font-weight: bold; margin-top: 6px;'>🌡️ Cooling Impact: -{temp_offset}°C</div>"
    if asset_prefix in ("SHELTER", "FOUNTAIN"):
        return "<div style='color: #38bdf8; font-weight: bold; margin-top: 6px;'>💧 Emergency Relief Active</div>"
    return ""


def _asset_tooltip(name: str, prefix: str, element_id, asset_type: str, impact_html: str) -> str:
    return (
        f"<b style='font-size: 14px; color: #00e5ff;'>{name}</b>"
        f"<br/><span style='color:#94a3b8; font-size:11px; font-family: monospace;'>"
        f"ID: {prefix}-{element_id}</span><br/><br/>"
        f"<b>Type:</b> {asset_type}<br/><b>Source:</b> OpenStreetMap{impact_html}"
    )


def _building_tooltip(element_id, height: float) -> str:
    return (
        f"<b style='font-size: 14px; color: #ff0055;'>Building Mass</b>"
        f"<br/><span style='color:#94a3b8; font-size:11px; font-family: monospace;'>"
        f"ID: BLDG-{element_id}</span><br/><br/>"
        f"<b>Est. Height:</b> {height:.1f}m<br/><b>Heat Retention:</b> High"
    )


def _traffic_tooltip(element_id, hw_type: str) -> str:
    return (
        f"<b style='font-size: 14px; color: #f59e0b;'>Transit Artery</b>"
        f"<br/><span style='color:#94a3b8; font-size:11px; font-family: monospace;'>"
        f"ID: TRAFFIC-{element_id}</span><br/><br/>"
        f"<b>Type:</b> {hw_type.capitalize()}<br/><b>Emissions:</b> Active"
    )


def _sensor_tooltip(sensor_id: str, aqi: int, lat: float, lon: float) -> str:
    return (
        f"<b style='font-size: 14px; color: #00e5ff;'>Air Quality Node</b>"
        f"<br/><span style='color:#94a3b8; font-size:11px; font-family: monospace;'>"
        f"ID: {sensor_id}</span><br/><br/>"
        f"<b>US AQI:</b> <span style='font-size: 14px; font-weight:bold;'>{aqi}</span>"
        f"<br/><span style='color:#94a3b8; font-size:11px;'>Lat: {lat:.4f} | Lon: {lon:.4f}</span>"
    )
