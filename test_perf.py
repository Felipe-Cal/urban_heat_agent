import time
import random

# Generate mock data
elements = []
tags_choices = [
    {"natural": "tree"}, {"natural": "water"}, {"leisure": "park"},
    {"amenity": "shelter"}, {"amenity": "community_centre"},
    {"amenity": "drinking_water"}, {"green_roof": "yes"},
    {"roof:material": "grass"}, {"landuse": "allotments"},
    {"leisure": "garden"}, {"landuse": "forest"}, {"natural": "wood"},
    {"natural": "wetland"}, {"building": "yes"}, {"highway": "primary"},
    {"other": "tag"}
]

for i in range(100000):
    elements.append({"id": i, "tags": random.choice(tags_choices)})

def method_list_comprehension():
    start = time.time()
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
    end = time.time()
    return end - start

def method_single_pass():
    start = time.time()
    trees, water, parks, shelters, fountains = [], [], [], [], []
    green_roofs, gardens, forests, wetlands = [], [], [], []
    raw_buildings, raw_traffic = [], []

    for e in elements:
        tags = e.get("tags", {})
        if not tags: continue

        natural = tags.get("natural")
        if natural == "tree": trees.append(e)
        elif natural == "water": water.append(e)
        elif natural == "wood": forests.append(e)
        elif natural == "wetland": wetlands.append(e)

        leisure = tags.get("leisure")
        if leisure == "park": parks.append(e)
        elif leisure == "garden": gardens.append(e)

        amenity = tags.get("amenity")
        if amenity in ("shelter", "community_centre"): shelters.append(e)
        elif amenity == "drinking_water": fountains.append(e)

        if tags.get("green_roof") == "yes" or tags.get("roof:material") == "grass": green_roofs.append(e)

        landuse = tags.get("landuse")
        if landuse == "allotments": gardens.append(e)
        elif landuse == "forest": forests.append(e)

        if "building" in tags: raw_buildings.append(e)
        if "highway" in tags: raw_traffic.append(e)

    end = time.time()
    return end - start

t1 = method_list_comprehension()
t2 = method_single_pass()

print(f"List Comprehensions: {t1:.4f}s")
print(f"Single Pass: {t2:.4f}s")
print(f"Improvement: {t1/t2:.2f}x")
