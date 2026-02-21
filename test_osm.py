import requests
import time

center_lat = 34.0522
center_lon = -118.2437
radius_meters = 2000
area_filter = f"(around:{radius_meters},{center_lat},{center_lon})"
building_radius = f"(around:{radius_meters // 2},{center_lat},{center_lon})"

query = f"""
[out:json][timeout:50];
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
    way["building"]{building_radius};
    way["highway"~"motorway|trunk|primary"]{area_filter};
);
out geom;
"""

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
start = time.time()
print("Starting query...")
try:
    response = requests.get(OVERPASS_URL, params={"data": query}, timeout=60)
    print(f"Status: {response.status_code}, Time: {time.time() - start:.2f}s")
    if response.status_code == 200:
        data = response.json()
        print(f"Elements: {len(data.get('elements', []))}")
    else:
        print(response.text[:200])
except Exception as e:
    print(e)
