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
from typing import Callable, Optional

import numpy as np
import pandas as pd
import requests

from modules.models import CityData, BBox

# Configuration
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
# OSM daily file-cache  (prevents cold-start timeouts on Streamlit Cloud)
# ---------------------------------------------------------------------------
_OSM_CACHE_DIR = os.path.join(os.environ.get("TMPDIR", "/tmp"), "heat_osm_cache")


def _cache_key(lat: float, lon: float) -> str:
    return f"{lat:.4f}_{lon:.4f}_{date.today().isoformat()}"


def _load_osm_cache(key: str) -> Optional[dict]:
    path = os.path.join(_OSM_CACHE_DIR, f"{key}.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _save_osm_cache(key: str, data: dict) -> None:
    os.makedirs(_OSM_CACHE_DIR, exist_ok=True)
    path = os.path.join(_OSM_CACHE_DIR, f"{key}.json")
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except Exception:
        pass



def _calculate_aqi(value: float, parameter: str) -> Optional[int]:
    """
    Convert raw pollutant values to US AQI based on EPA breakpoints.
    Supports PM2.5, Ozone (ppm), NO2 (ppb), and PM10.
    """
    parameter = parameter.lower().replace(".", "")
    if parameter == "pm25":
        # PM2.5 (µg/m³)
        bp = [(0, 0, 12, 50), (12.1, 51, 35.4, 100), (35.5, 101, 55.4, 150),
              (55.5, 151, 150.4, 200), (150.5, 201, 250.4, 300), (250.5, 301, 500.4, 500)]
    elif parameter == "o3":
        # Ozone (ppm)
        bp = [(0, 0, 0.054, 50), (0.055, 51, 0.070, 100), (0.071, 101, 0.085, 150),
              (0.086, 151, 0.105, 200), (0.106, 201, 0.200, 300)]
    elif parameter == "no2":
        # NO2 (ppb)
        bp = [(0, 0, 53, 50), (54, 51, 100, 100), (101, 101, 360, 150),
              (361, 151, 649, 200)]
    elif parameter == "pm10":
        # PM10 (µg/m³)
        bp = [(0, 0, 54, 50), (55, 51, 154, 100), (155, 101, 254, 150),
              (255, 151, 354, 200), (355, 201, 424, 300)]
    else:
        return None

    for blo, ilo, bhi, ihi in bp:
        if blo <= value <= bhi:
            return int(round((ihi - ilo) / (bhi - blo) * (value - blo) + ilo))
    
    if bp and value > bp[-1][2]:
        return bp[-1][3]
    return int(round(value)) if value >= 0 else 0


def generate_mock_data(
    center_lat: float = 34.0522,
    center_lon: float = -118.2437,
    time_of_day: str = "14:00",
    progress_callback: Optional[Callable[[str, int], None]] = None,
    openaq_api_key: Optional[str] = None,
    bbox: Optional[BBox] = None,
    radius_meters: int = 2000,
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
    current_temp: float = 30.0  # Fallback
    current_aqi: int = 45       # Fallback
    fetch_error: Optional[str] = None

    try:
        meteo_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={center_lat}&longitude={center_lon}&current=temperature_2m"
        )
        meteo_resp = requests.get(meteo_url, timeout=5)
        if meteo_resp.status_code == 200:
            current_temp = float(
                meteo_resp.json().get("current", {}).get("temperature_2m", 30.0)
            )

        aqi_url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality"
            f"?latitude={center_lat}&longitude={center_lon}&current=us_aqi"
        )
        aqi_resp = requests.get(aqi_url, timeout=5)
        if aqi_resp.status_code == 200:
            current_aqi = int(
                aqi_resp.json().get("current", {}).get("us_aqi", 45)
            )
    except Exception as e:
        print(f"Error fetching Open-Meteo APIs: {e}")

    # Calculate Diurnal temporal shift based on the UI slider
    if hasattr(time_of_day, "hour"):
        hour = time_of_day.hour
        minute = time_of_day.minute
    else:
        try:
            h_str, m_str = time_of_day.split(":")
            hour = int(h_str)
            minute = int(m_str)
        except (ValueError, IndexError):
            hour, minute = 14, 0

    # Precise fractional hour
    fractional_hour = hour + (minute / 60.0)
    temp_variation = -5.0 * np.cos((fractional_hour - 4) * np.pi / 11.0)
    
    # We will compute the final `current_temp` directly from the thermal grid 
    # if it loads successfully, ensuring the UI perfectly matches the true Local Surface Temp.

    # -------------------------------------------------------------------------
    # 2. Real thermal surface temperature (Open-Meteo LST grid)
    # -------------------------------------------------------------------------
    _progress("Acquiring Land Surface Temperature (LST) data...", 20)
    thermal_data = []
    thermal_points_data = []
    
    # 10x10 grid (~3km radius total)
    steps = 10
    if bbox:
        start_lat, start_lon = bbox.min_lat, bbox.min_lon
        lat_step = (bbox.max_lat - bbox.min_lat) / steps
        lon_step = (bbox.max_lon - bbox.min_lon) / steps
    else:
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
    
    thermal_cache_key = f"thermal_{_cache_key(center_lat, center_lon)}"
    if bbox:
        thermal_cache_key += f"_{bbox.min_lat:.4f}_{bbox.min_lon:.4f}_{bbox.max_lat:.4f}_{bbox.max_lon:.4f}"
    cached_thermal = _load_osm_cache(thermal_cache_key)
    
    max_theoretical_temp = 50.0

    if cached_thermal and len(cached_thermal) == len(lats):
        _progress("Loaded thermal grid from cache...", 25)
        raw_temps = [pt["temp"] for pt in cached_thermal]
    else:
        try:
            thermal_url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lats_str}&longitude={lons_str}"
                f"&current=soil_temperature_0cm&temperature_unit=celsius"
            )
            thermal_resp = requests.get(thermal_url, timeout=10)
            if thermal_resp.status_code == 200:
                results = thermal_resp.json()
                cache_payload = []
                raw_temps = []
                for i, res in enumerate(results):
                    t = res.get("current", {}).get("soil_temperature_0cm") 
                    if t is None:
                        t = current_temp
                    cache_payload.append({"temp": t})
                    raw_temps.append(t)
                _save_osm_cache(thermal_cache_key, cache_payload)
            else:
                raise Exception(f"Thermal API returned {thermal_resp.status_code}")
                
        except Exception as e:
            print(f"Error fetching real thermal grid: {e}. Falling back to synthetic.")
            raw_temps = None

    if raw_temps:
        # Interpolate the rigid 10x10 grid onto a 1500-point random scatter 
        # using Inverse Distance Weighting (IDW) to create a smooth, organic heatmap
        grid_pts = np.column_stack((lats, lons))
        temps_arr = np.array(raw_temps)
        
        num_interp_points = 2000
        
        # Gaussian distribution creates a natural fade at the edges instead of a hard square
        rand_lats = np.random.normal(center_lat, 0.03, num_interp_points)
        rand_lons = np.random.normal(center_lon, 0.03, num_interp_points)
        rand_pts = np.column_stack((rand_lats, rand_lons))
        
        # Broadcasting to find distances (2000 x 100)
        rand_pts_exp = rand_pts[:, np.newaxis, :]
        grid_pts_exp = grid_pts[np.newaxis, :, :]
        
        dist_sq = np.sum((rand_pts_exp - grid_pts_exp) ** 2, axis=2)
        dist_sq[dist_sq == 0] = 1e-10  # prevent div by zero
        weights = 1.0 / dist_sq
        
        interp_temps = np.sum(weights * temps_arr, axis=1) / np.sum(weights, axis=1)

        t_lo, t_hi = -10.0, 45.0
        for r_lon, r_lat, t in zip(rand_lons, rand_lats, interp_temps):
            t += temp_variation
            frac = np.clip((t - t_lo) / (t_hi - t_lo), 0.0, 1.0)
            norm_t = 0.05 + 0.45 * frac
            thermal_data.append([r_lon, r_lat, norm_t])
            
        for lon, lat, t in zip(lons, lats, raw_temps):
            t += temp_variation
            thermal_points_data.append({
                "lon": lon, "lat": lat, "temp": t,
                "tooltip": _thermal_point_tooltip(lat, lon, t)
            })
    df_thermal = pd.DataFrame(thermal_data, columns=["lon", "lat", "weight"])
    df_thermal_points = pd.DataFrame(thermal_points_data)

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
    try:
        if bbox:
            area_filter = f"({bbox.to_overpass_str()})"
            building_radius = "" # use full bbox
        else:
            area_filter = f"(around:{radius_meters},{center_lat},{center_lon})"
            building_radius = f"(around:{radius_meters // 2},{center_lat},{center_lon})"

        query = f"""
        [out:json][timeout:90];
        (
          node["natural"="tree"]{area_filter};
          nwr["natural"="water"]{area_filter};
          nwr["leisure"="park"]{area_filter};
          nwr["amenity"~"shelter|community_centre"]{area_filter};
          node["amenity"="drinking_water"]{area_filter};
          nwr["green_roof"="yes"]{area_filter};
          nwr["roof:material"="grass"]{area_filter};
          nwr["landuse"="allotments"]{area_filter};
          nwr["leisure"="garden"]{area_filter};
          nwr["landuse"="forest"]{area_filter};
          nwr["natural"="wood"]{area_filter};
          nwr["natural"="wetland"]{area_filter};
          way["building"]{building_radius if not bbox else area_filter};
          way["highway"~"motorway|trunk|primary"]{area_filter};
        );
        out geom;
        """
        # --- Cache: skip expensive Overpass call if we have today's data ---
        osm_cache_key = _cache_key(center_lat, center_lon)
        if bbox:
            osm_cache_key += f"_{bbox.min_lat:.4f}_{bbox.min_lon:.4f}_{bbox.max_lat:.4f}_{bbox.max_lon:.4f}"
        osm_data = _load_osm_cache(osm_cache_key)

        if osm_data is None:
            endpoints = [
                OVERPASS_URL,
                "https://lz4.overpass-api.de/api/interpreter",
                "https://z.overpass-api.de/api/interpreter",
                "https://overpass.kumi.systems/api/interpreter"
            ]
            response = None
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, params={"data": query}, timeout=90)
                    if response.status_code == 200:
                        break
                    else:
                        print(f"Warning: Overpass endpoint {endpoint} returned {response.status_code}")
                except Exception as e:
                    print(f"Warning: Exception contacting {endpoint}: {e}")
            
            if response and response.status_code == 200:
                osm_data = response.json()
                _save_osm_cache(osm_cache_key, osm_data)
            else:
                last_status = response.status_code if response else "Unknown"
                print(f"Error: All Overpass endpoints failed. Last status: {last_status}")
                if response and response.status_code == 504:
                    fetch_error = "\u23f3 OpenStreetMap Gateway Timeout (504). The query was too large."
                elif response and response.status_code == 429:
                    fetch_error = "\u26a0\ufe0f OpenStreetMap rate-limited (429). Map loaded without Nature ID assets."
                else:
                    fetch_error = f"\u26a0\ufe0f OpenStreetMap Error {last_status}."
                osm_data = {"elements": []}
        else:
            _progress("Loaded from local cache...", 50)

        # --- Process elements regardless of whether data came from cache or API ---
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

        _progress("Processing geospatial elements...", 50)

        elements = osm_data.get("elements", [])
        trees = [e for e in elements if e.get("tags", {}).get("natural") == "tree"]
        water = [e for e in elements if e.get("tags", {}).get("natural") == "water"]
        parks = [e for e in elements if e.get("tags", {}).get("leisure") == "park"]
        shelters = [
            e for e in elements
            if e.get("tags", {}).get("amenity") in ("shelter", "community_centre")
        ]
        fountains = [e for e in elements if e.get("tags", {}).get("amenity") == "drinking_water"]
        green_roofs = [
            e for e in elements
            if e.get("tags", {}).get("green_roof") == "yes"
            or e.get("tags", {}).get("roof:material") == "grass"
        ]
        gardens = [
            e for e in elements
            if e.get("tags", {}).get("landuse") == "allotments"
            or e.get("tags", {}).get("leisure") == "garden"
        ]
        forests = [
            e for e in elements
            if e.get("tags", {}).get("landuse") == "forest"
            or e.get("tags", {}).get("natural") == "wood"
        ]
        wetlands = [e for e in elements if e.get("tags", {}).get("natural") == "wetland"]
        raw_buildings = [e for e in elements if "building" in e.get("tags", {})]
        raw_traffic = [e for e in elements if "highway" in e.get("tags", {})]

        # Buildings (PolygonLayer)
        for b_el in raw_buildings[:500]:
            if b_el.get("type") == "way" and b_el.get("geometry"):
                polygon = [[pt["lon"], pt["lat"]] for pt in b_el["geometry"]]
                levels = max(1, int(b_el.get("tags", {}).get("building:levels", 1)))
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
            impact_html = "<div style='color: #10b981; font-weight: bold; margin-top: 6px;'>Cooling asset</div>"
            tree_data.append({
                "lon": lon, "lat": lat,
                "asset_id": f"TREE-{element['id']}",
                "name": species,
                "type": "Tree Canopy",
                "health": "Verified",
                "owner": "Public",
                "color": "rgba(5, 150, 105, 0.8)",
                "tooltip": _asset_tooltip(species, "TREE", element["id"], "Tree Canopy", impact_html),
            })

        process_assets(water, water_data, "WATER", "Water Body", "Water Resource", "rgba(14, 165, 233, 0.8)", 500)
        process_assets(parks, park_data, "PARK", "Public Park", "Urban Park", "rgba(132, 204, 22, 0.8)", 500)
        process_assets(green_roofs, green_roof_data, "ROOF", "Green Roof", "Eco Infrastructure", "rgba(163, 230, 53, 0.8)", 200)
        process_assets(gardens, garden_data, "GARDEN", "Community Garden", "Bio-Asset", "rgba(77, 124, 15, 0.8)", 300)
        process_assets(forests, forest_data, "FOREST", "Urban Forest", "Woodland", "rgba(21, 128, 61, 0.8)", 200)
        process_assets(wetlands, wetland_data, "WETLAND", "Wetland", "Natural Marsh", "rgba(12, 74, 110, 0.8)", 100)

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
                "color": "rgba(245, 158, 11, 0.8)",
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
                "color": "rgba(56, 189, 248, 0.8)",
                "tooltip": _fountain_tooltip(name, element["id"], tags),
            })


    except requests.exceptions.Timeout:
        print("Error: Overpass API request timed out after 90 seconds.")
        fetch_error = "⏳ OpenStreetMap API response timed out. Map rendered using fallback data."
    except Exception as e:
        print(f"Error fetching OSM data: {e}")
        fetch_error = "🛑 Network Error fetching OpenStreetMap data. Check your connection."

    # -------------------------------------------------------------------------
    # 4. Air quality sensor nodes  (real locations from OpenAQ v3)
    # -------------------------------------------------------------------------
    _progress("Connecting to OpenAQ sensor network...", 75)
    sensor_data, oaq_error = _fetch_openaq_sensors(center_lat, center_lon, current_aqi, openaq_api_key=openaq_api_key)
    if oaq_error:
        fetch_error = f"{fetch_error}\n{oaq_error}" if fetch_error else oaq_error

    _progress("Generating bio-regional data structures...", 90)

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
    _progress("Complete.", 100)

    return CityData(
        df_thermal=pd.DataFrame(thermal_data, columns=["lon", "lat", "weight"]),
        df_thermal_points=pd.DataFrame(thermal_points_data),
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
        df_buildings=pd.DataFrame(building_data),
        df_traffic=pd.DataFrame(traffic_data),
        resilience_score=resilience_score,
        current_temp=current_temp,
        current_aqi=current_aqi,
        fetch_error=fetch_error,
    )


# ---------------------------------------------------------------------------
# Private tooltip / ID helpers  (keeps long HTML strings out of business logic)
# ---------------------------------------------------------------------------

def _fetch_openaq_sensors(
    center_lat: float,
    center_lon: float,
    base_aqi: int,
    radius_m: int = 25_000,
    limit: int = 50,
    openaq_api_key: Optional[str] = None,
) -> tuple[list, Optional[str]]:
    """
    Fetch real sensor stations from OpenAQ v3. 
    Filters for stations updated in the last 60 days to ensure active data.
    """
    error_msg = None
    try:
        headers = {"accept": "application/json"}
        if openaq_api_key:
            headers["X-API-Key"] = openaq_api_key
        
        resp = requests.get(
            "https://api.openaq.org/v3/locations",
            params={
                "coordinates": f"{center_lat},{center_lon}",
                "radius": radius_m,
                "limit": limit,
            },
            headers=headers,
            timeout=8,
        )
        
        if resp.status_code == 401:
            return [], "🔑 OpenAQ: Invalid API Key. Check secrets.toml."
        if resp.status_code == 429:
            return [], "🚦 OpenAQ: Rate limited. Please try again later."
        if resp.status_code != 200:
            print(f"OpenAQ returned status {resp.status_code}")
            return [], f"🌐 OpenAQ API Error ({resp.status_code})."

        sensor_data = []
        results = resp.json().get("results", [])
        
        # Filter for active stations (last updated within 60 days)
        now = datetime.utcnow()
        active_results = []
        for loc in results:
            dt_last = (loc.get("datetimeLast") or {}).get("utc")
            if not dt_last:
                continue
            try:
                # Remove Z and parse
                ts = datetime.fromisoformat(dt_last.replace("Z", "+00:00"))
                delta = now - ts.replace(tzinfo=None)
                if delta.days < 60:
                    active_results.append(loc)
            except Exception:
                pass
        
        # Fallback to all results if no active found in radius
        if not active_results:
            active_results = results[:10]

        for loc in active_results[:25]:
            coords = loc.get("coordinates", {})
            lat, lon = coords.get("latitude"), coords.get("longitude")
            if lat is None or lon is None:
                continue
            
            loc_id = loc.get("id")
            sensor_id = f"OAQ-{loc_id}"
            local_aqi = base_aqi
            pollutant = "Synthesized"

            if openaq_api_key and loc_id is not None:
                try:
                    latest_resp = requests.get(
                        f"https://api.openaq.org/v3/locations/{loc_id}/latest",
                        headers=headers,
                        timeout=5,
                    )
                    if latest_resp.status_code == 200:
                        l_results = latest_resp.json().get("results", [])
                        
                        # Map sensorsId to parameter info from the location object
                        sensor_map = {s.get("id"): (s.get("parameter") or {}).get("name") for s in loc.get("sensors", []) if s.get("id")}
                        
                        # Collect results by parameter name
                        results_by_param = {}
                        for r in l_results:
                            s_id = r.get("sensorsId")
                            p_name = sensor_map.get(s_id)
                            if p_name:
                                results_by_param[p_name] = r
                        
                        # Prioritize pollutants: pm25 > pm2.5 > o3 > no2 > pm10
                        target_param = None
                        for p in ["pm25", "pm2.5", "o3", "no2", "pm10"]:
                            if p in results_by_param:
                                target_param = p
                                break
                        
                        if target_param:
                            target = results_by_param[target_param]
                            v = target.get("value")
                            if v is not None:
                                calculated = _calculate_aqi(float(v), target_param)
                                if calculated is not None:
                                    local_aqi = calculated
                                    pollutant = target_param.upper()
                except Exception:
                    pass

            color = "rgba(16, 185, 129, 0.8)" if local_aqi < 50 else \
                    "rgba(245, 158, 11, 0.8)" if local_aqi < 100 else "rgba(239, 68, 68, 0.8)"
            
            sensor_data.append({
                "lon": lon, "lat": lat,
                "sensor_id": sensor_id,
                "aqi": local_aqi,
                "pollutant": pollutant,
                "color": color,
                "tooltip": _sensor_tooltip(sensor_id, local_aqi, lat, lon, pollutant),
            })
        return sensor_data, None
    except Exception as e:
        print(f"OpenAQ fetch failed: {e}")
        return [], "📡 OpenAQ fetch failed (check connection)."


def _make_sensor_id() -> str:
    """Generate a random AQ sensor ID without needing the Faker library."""
    digits = "".join(random.choices(string.digits, k=2))
    letters = "".join(random.choices(string.ascii_uppercase, k=2))
    return f"AQ-{digits}{letters}"


def _impact_html(asset_prefix: str) -> str:
    if asset_prefix in ("TREE", "PARK", "WATER", "FOREST", "ROOF", "GARDEN", "WETLAND"):
        return "<div style='color: #10b981; font-weight: bold; margin-top: 6px;'>Cooling asset</div>"
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


def _opening_hours_status(oh: str) -> str:
    if not oh:
        return "Check Hours"
    oh_lower = oh.lower().replace(" ", "")
    if "24/7" in oh_lower or "24:00" in oh_lower or "00:00-24:00" in oh_lower:
        return "Open Now"
    return "Check Hours"


def _shelter_tooltip(name: str, element_id, tags: dict) -> str:
    oh = tags.get("opening_hours", "")
    status = _opening_hours_status(oh)
    status_color = "#10b981" if status == "Open Now" else "#94a3b8"
    parts = [
        f"<b style='font-size: 14px; color: #00e5ff;'>{name}</b>",
        f"<br/><span style='color:#94a3b8; font-size:11px; font-family: monospace;'>ID: SHELTER-{element_id}</span>",
        f"<br/><br/><b>Type:</b> Emergency Shelter",
        f"<br/><span style='color:{status_color}; font-weight:600;'>{'🟢' if status == 'Open Now' else '🔴'} {status}</span>",
    ]
    if oh and status == "Check Hours":
        parts.append(f"<br/><b>Hours:</b> {oh}")
    addr = tags.get("addr:street", "")
    if tags.get("addr:housenumber"):
        addr = f"{tags.get('addr:housenumber')} {addr}".strip()
    if addr:
        parts.append(f"<br/><b>Address:</b> {addr}")
    if tags.get("operator"):
        parts.append(f"<br/><b>Operator:</b> {tags.get('operator')}")
    if tags.get("capacity"):
        parts.append(f"<br/><b>Capacity:</b> {tags.get('capacity')}")
    if tags.get("air_conditioning"):
        parts.append(f"<br/><b>Air conditioning:</b> {tags.get('air_conditioning')}")
    if tags.get("wheelchair"):
        parts.append(f"<br/><b>Wheelchair:</b> {tags.get('wheelchair')}")
    if tags.get("phone") or tags.get("contact:phone"):
        parts.append(f"<br/><b>Phone:</b> {tags.get('phone') or tags.get('contact:phone')}")
    parts.append("<br/><b>Source:</b> OpenStreetMap")
    return "".join(parts)


def _fountain_tooltip(name: str, element_id, tags: dict) -> str:
    parts = [
        f"<b style='font-size: 14px; color: #00e5ff;'>{name}</b>",
        f"<br/><span style='color:#94a3b8; font-size:11px; font-family: monospace;'>ID: FOUNTAIN-{element_id}</span>",
        f"<br/><br/><b>Type:</b> Hydration Access",
    ]
    if tags.get("operator"):
        parts.append(f"<br/><b>Operator:</b> {tags.get('operator')}")
    fee = tags.get("fee", "no")
    parts.append(f"<br/><b>Free access:</b> {'Yes' if fee in ('no', 'false', '0') else fee}")
    if tags.get("wheelchair"):
        parts.append(f"<br/><b>Wheelchair:</b> {tags.get('wheelchair')}")
    if tags.get("seasonal") or tags.get("seasonal:yes"):
        parts.append(f"<br/><b>Seasonal:</b> {tags.get('seasonal', 'yes')}")
    parts.append("<br/><b>Source:</b> OpenStreetMap")
    return "".join(parts)


def _sensor_tooltip(sensor_id: str, aqi: int, lat: float, lon: float, pollutant: str = "PM2.5") -> str:
    return (
        f"<b style='font-size: 14px; color: #00e5ff;'>Air Quality Node</b>"
        f"<br/><span style='color:#94a3b8; font-size:11px; font-family: monospace;'>"
        f"ID: {sensor_id}</span><br/><br/>"
        f"<b>Main Pollutant:</b> {pollutant}<br/>"
        f"<b>Calculated AQI:</b> <span style='font-size: 14px; font-weight:bold;'>{aqi}</span>"
        f"<br/><span style='color:#94a3b8; font-size:11px;'>Lat: {lat:.4f} | Lon: {lon:.4f}</span>"
    )

def _thermal_point_tooltip(lat: float, lon: float, temp: float) -> str:
    return (
        f"<b style='font-size: 14px; color: #ff5555;'>LST Sensor Data</b>"
        f"<br/><span style='color:#94a3b8; font-size:11px; font-family: monospace;'>"
        f"Source: Open-Meteo</b></span><br/><br/>"
        f"<b>Surface Temp:</b> <span style='font-size: 14px; font-weight:bold;'>{temp:.1f}°C</span>"
        f"<br/><span style='color:#94a3b8; font-size:11px;'>Lat: {lat:.4f} | Lon: {lon:.4f}</span>"
    )
