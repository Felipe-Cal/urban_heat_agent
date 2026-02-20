import pandas as pd
import numpy as np
import random
from faker import Faker
import requests

fake = Faker()

def generate_mock_data(center_lat=34.0522, center_lon=-118.2437, time_of_day="14:00"):
    """Generates mock data for Thermal, Trees, and Sensors layers centered on provided coordinates."""
    
    # Use provided coordinates
    CENTER_LAT = center_lat
    CENTER_LON = center_lon
    
    # 1. Thermal Data (Heatmap)
    # Fetch real baseline temperature from Open-Meteo
    current_temp = 30.0 # Fallback
    current_aqi = 45 # Fallback
    try:
        meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={CENTER_LAT}&longitude={CENTER_LON}&current=temperature_2m"
        meteo_resp = requests.get(meteo_url, timeout=5)
        if meteo_resp.status_code == 200:
            current_temp = meteo_resp.json().get('current', {}).get('temperature_2m', 30.0)
            
        aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={CENTER_LAT}&longitude={CENTER_LON}&current=us_aqi"
        aqi_resp = requests.get(aqi_url, timeout=5)
        if aqi_resp.status_code == 200:
            current_aqi = aqi_resp.json().get('current', {}).get('us_aqi', 45)
    except Exception as e:
        print(f"Error fetching Open-Meteo APIs: {e}")
        pass

    # Temporal multiplier for time of day (0-23)
    try:
        hour = int(time_of_day.split(":")[0])
    except:
        hour = 14
        
    # Diurnal temperature variation (simplistic curve: min at 4am, max at 3pm/15:00)
    # A 10C swing throughout the day
    temp_variation = -5.0 * np.cos((hour - 4) * np.pi / 11.0)
    current_temp += temp_variation

    # Time of day also affects AQI slightly (worse in traffic hours 8am, 5pm)
    if hour in [7, 8, 9, 16, 17, 18]:
        current_aqi += random.randint(10, 20)
    elif hour < 6 or hour > 20:
        current_aqi = max(0, current_aqi - random.randint(5, 15))

    # Generate synthetic heat islands centered around the real baseline temperature
    thermal_data = []
    # Base it relative to an extreme "hot" map of 50C for the PyDeck weight normalization
    max_theoretical_temp = 50.0 
    for _ in range(500):
        lat = CENTER_LAT + np.random.normal(0, 0.02)
        lon = CENTER_LON + np.random.normal(0, 0.02)
        
        # Simulate an Urban Heat Island effect: 
        # Points closer to the center are hotter (+0 to +8 degrees), points further out are baseline
        distance = np.sqrt((lat - CENTER_LAT)**2 + (lon - CENTER_LON)**2)
        uhi_effect = max(0, 8 - (distance * 200)) 
        
        temp = current_temp + random.uniform(0, uhi_effect)
        
        # Normalize 0-1 for heatmap intensity, guaranteeing visual output even on cold days
        weight = max(0.1, temp / max_theoretical_temp) 
        
        thermal_data.append([lon, lat, weight])
        
    df_thermal = pd.DataFrame(thermal_data, columns=['lon', 'lat', 'weight'])

    # 1b. Synthetic Population Density (Spatially aligned with the heat center but clustered)
    population_data = []
    for _ in range(300):
        # Slightly tighter clustering than the heat island
        p_lat = CENTER_LAT + np.random.normal(0, 0.025)
        p_lon = CENTER_LON + np.random.normal(0, 0.025)
        
        # Base weight on proximity to center + randomness
        distance = np.sqrt((p_lat - CENTER_LAT)**2 + (p_lon - CENTER_LON)**2)
        weight = max(10, 100 - (distance * 3500)) + random.randint(0, 20)
        
        population_data.append({
            'lat': p_lat,
            'lon': p_lon,
            'weight': weight
        })

    # 2. Nature ID & Infrastructure Layers - USING REAL DATA FROM OPENSTREETMAP
    tree_data = []
    water_data = []
    park_data = []
    shelter_data = []
    fountain_data = []
    green_roof_data = []
    garden_data = []
    forest_data = []
    wetland_data = []
    
    try:
        # Query OSM for multiple nature elements within 8km of the city center
        radius_meters = 8000
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        (
          node["natural"="tree"](around:{radius_meters},{CENTER_LAT},{CENTER_LON});
          nwr["natural"="water"](around:{radius_meters},{CENTER_LAT},{CENTER_LON});
          nwr["leisure"="park"](around:{radius_meters},{CENTER_LAT},{CENTER_LON});
          nwr["amenity"~"shelter|community_centre"](around:{radius_meters},{CENTER_LAT},{CENTER_LON});
          node["amenity"="drinking_water"](around:{radius_meters},{CENTER_LAT},{CENTER_LON});
          nwr["green_roof"="yes"](around:{radius_meters},{CENTER_LAT},{CENTER_LON});
          nwr["roof:material"="grass"](around:{radius_meters},{CENTER_LAT},{CENTER_LON});
          nwr["landuse"="allotments"](around:{radius_meters},{CENTER_LAT},{CENTER_LON});
          nwr["leisure"="garden"](around:{radius_meters},{CENTER_LAT},{CENTER_LON});
          nwr["landuse"="forest"](around:{radius_meters},{CENTER_LAT},{CENTER_LON});
          nwr["natural"="wood"](around:{radius_meters},{CENTER_LAT},{CENTER_LON});
          nwr["natural"="wetland"](around:{radius_meters},{CENTER_LAT},{CENTER_LON});
          
          // New Drivers
          nwr["building"](around:{radius_meters / 2},{CENTER_LAT},{CENTER_LON}); // Smaller radius for buildings to prevent massive payloads
          way["highway"~"motorway|trunk|primary"](around:{radius_meters},{CENTER_LAT},{CENTER_LON});
        );
        out geom; // Note: Changed to out geom to get coordinates for polygons and ways
        """
        response = requests.get(overpass_url, params={'data': query})
        
        if response.status_code == 200:
            osm_data = response.json()
            
            # Helper to extract lat/lon (handling ways/relations with out geom)
            def get_coords(el):
                if 'lat' in el and 'lon' in el:
                    return el['lat'], el['lon']
                elif el.get('type') == 'way' and 'geometry' in el and len(el['geometry']) > 0:
                    # Center of the way snippet
                    mid = len(el['geometry']) // 2
                    return el['geometry'][mid]['lat'], el['geometry'][mid]['lon']
                elif el.get('type') == 'relation' and 'members' in el:
                    for member in el['members']:
                        if 'geometry' in member and len(member['geometry']) > 0:
                            mid = len(member['geometry']) // 2
                            return member['geometry'][mid]['lat'], member['geometry'][mid]['lon']
                elif 'center' in el:
                    return el['center']['lat'], el['center']['lon']
                return None, None

            # Group elements by type
            trees = [e for e in osm_data.get('elements', []) if e.get('tags', {}).get('natural') == 'tree']
            water = [e for e in osm_data.get('elements', []) if e.get('tags', {}).get('natural') == 'water']
            parks = [e for e in osm_data.get('elements', []) if e.get('tags', {}).get('leisure') == 'park']
            shelters = [e for e in osm_data.get('elements', []) if e.get('tags', {}).get('amenity') in ['shelter', 'community_centre']]
            fountains = [e for e in osm_data.get('elements', []) if e.get('tags', {}).get('amenity') == 'drinking_water']
            green_roofs = [e for e in osm_data.get('elements', []) if e.get('tags', {}).get('green_roof') == 'yes' or e.get('tags', {}).get('roof:material') == 'grass']
            gardens = [e for e in osm_data.get('elements', []) if e.get('tags', {}).get('landuse') == 'allotments' or e.get('tags', {}).get('leisure') == 'garden']
            forests = [e for e in osm_data.get('elements', []) if e.get('tags', {}).get('landuse') == 'forest' or e.get('tags', {}).get('natural') == 'wood']
            wetlands = [e for e in osm_data.get('elements', []) if e.get('tags', {}).get('natural') == 'wetland']
            
            raw_buildings = [e for e in osm_data.get('elements', []) if 'building' in e.get('tags', {})]
            raw_traffic = [e for e in osm_data.get('elements', []) if 'highway' in e.get('tags', {})]
            
            # Process Geometry for Buildings (PolygonLayer)
            building_data = []
            for b_el in raw_buildings[:500]: # Limit to prevent lag
                if b_el.get('type') == 'way' and 'geometry' in b_el:
                    polygon = [[pt['lon'], pt['lat']] for pt in b_el['geometry']]
                    # Determine synthetic height based on tag or random
                    levels = int(b_el.get('tags', {}).get('building:levels', random.randint(1, 8)))
                    height = levels * 3.5
                    lat, lon = get_coords(b_el)
                    building_data.append({
                        'polygon': polygon,
                        'height': height,
                        'lon': lon, 'lat': lat,
                        'asset_id': f"BLDG-{b_el['id']}",
                        'name': b_el.get('tags', {}).get('name', 'Urban Structure'),
                        'type': 'Concrete Mass',
                        'tooltip': f"<b style='font-size: 14px; color: #ff0055;'>Building Mass</b><br/><span style='color:#94a3b8; font-size:11px; font-family: monospace;'>ID: BLDG-{b_el['id']}</span><br/><br/><b>Est. Height:</b> {height:.1f}m<br/><b>Heat Retention:</b> High"
                    })
                    
            # Process Geometry for Traffic (PathLayer)
            traffic_data = []
            for t_el in raw_traffic[:200]:
                if t_el.get('type') == 'way' and 'geometry' in t_el:
                    path = [[pt['lon'], pt['lat']] for pt in t_el['geometry']]
                    lat, lon = get_coords(t_el)
                    highway_type = t_el.get('tags', {}).get('highway', 'road')
                    traffic_data.append({
                        'path': path,
                        'lon': lon, 'lat': lat,
                        'asset_id': f"TRAFFIC-{t_el['id']}",
                        'name': t_el.get('tags', {}).get('name', 'Transit Artery'),
                        'type': highway_type.capitalize(),
                        'tooltip': f"<b style='font-size: 14px; color: #f59e0b;'>Transit Artery</b><br/><span style='color:#94a3b8; font-size:11px; font-family: monospace;'>ID: TRAFFIC-{t_el['id']}</span><br/><br/><b>Type:</b> {highway_type.capitalize()}<br/><b>Emissions:</b> Active"
                    })
            
            # Process generic assets helper
            def process_assets(elements, data_list, asset_prefix, default_name, asset_type, color, limit=500):
                for element in elements[:limit]:
                    lat, lon = get_coords(element)
                    if lat is None or lon is None: continue
                    
                    tags = element.get('tags', {})
                    name = tags.get('name', default_name)
                    
                    # Generate a plausible cooling/relief impact for tooltips
                    impact_html = ""
                    if asset_prefix in ["TREE", "PARK", "WATER", "FOREST", "ROOF", "GARDEN", "WETLAND"]:
                        temp_offset = round(random.uniform(0.5, 2.5), 1)
                        impact_html = f"<div style='color: #10b981; font-weight: bold; margin-top: 6px;'>🌡️ Cooling Impact: -{temp_offset}°C</div>"
                    elif asset_prefix in ["SHELTER", "FOUNTAIN"]:
                        impact_html = f"<div style='color: #38bdf8; font-weight: bold; margin-top: 6px;'>💧 Emergency Relief Active</div>"
                        
                    data_list.append({
                        'lon': lon,
                        'lat': lat,
                        'asset_id': f"{asset_prefix}-{element['id']}",
                        'name': name,
                        'type': asset_type,
                        'health': 'Verified',
                        'owner': 'Public/Private',
                        'color': color,
                        'tooltip': f"<b style='font-size: 14px; color: #00e5ff;'>{name}</b><br/><span style='color:#94a3b8; font-size:11px; font-family: monospace;'>ID: {asset_prefix}-{element['id']}</span><br/><br/><b>Type:</b> {asset_type}<br/><b>Source:</b> OpenStreetMap{impact_html}"
                    })

            # Process Trees (Limit to 1000, specific handling for species)
            for element in trees[:1000]:
                lat, lon = get_coords(element)
                if lat is None or lon is None: continue
                tags = element.get('tags', {})
                species = tags.get('species', 'Unknown Species')
                if species == 'Unknown Species':
                    species = tags.get('genus', 'Real Tree')
                    
                temp_offset = round(random.uniform(0.1, 1.2), 1)
                impact_html = f"<div style='color: #10b981; font-weight: bold; margin-top: 6px;'>🌡️ Cooling Impact: -{temp_offset}°C</div>"
                
                tree_data.append({
                    'lon': lon, 'lat': lat, 'asset_id': f"TREE-{element['id']}", 'name': species,
                    'type': 'Tree Canopy', 'health': 'Verified', 'owner': 'Public',
                    'color': [5, 150, 105, 200], 'tooltip': f"<b style='font-size: 14px; color: #00e5ff;'>{species}</b><br/><span style='color:#94a3b8; font-size:11px; font-family: monospace;'>ID: TREE-{element['id']}</span><br/><br/><b>Type:</b> Tree Canopy<br/><b>Health:</b> Verified{impact_html}"
                })
                
            process_assets(water, water_data, "WATER", "Water Body", "Water Resource", [14, 165, 233, 200], 500)
            process_assets(parks, park_data, "PARK", "Public Park", "Urban Park", [132, 204, 22, 200], 500)
            process_assets(shelters, shelter_data, "SHELTER", "Cooling Center", "Emergency Shelter", [245, 158, 11, 200], 200) # Amber-500
            process_assets(fountains, fountain_data, "FOUNTAIN", "Drinking Fountain", "Hydration Access", [56, 189, 248, 200], 200) # Sky-400
            process_assets(green_roofs, green_roof_data, "ROOF", "Green Roof", "Eco Infrastructure", [163, 230, 53, 200], 200) # Lime-400
            process_assets(gardens, garden_data, "GARDEN", "Community Garden", "Bio-Asset", [77, 124, 15, 200], 300) # Lime-700
            process_assets(forests, forest_data, "FOREST", "Urban Forest", "Woodland", [21, 128, 61, 200], 200) # Green-700
            process_assets(wetlands, wetland_data, "WETLAND", "Wetland", "Natural Marsh", [12, 74, 110, 200], 100) # Sky-900
                
    except Exception as e:
        print(f"Error fetching OSM data: {e}")
        # Default initialization if API fails
        trees, water, parks, shelters, fountains, green_roofs, gardens, forests, wetlands, building_data, traffic_data = [],[],[],[],[],[],[],[],[],[],[]
        pass
        
    df_trees = pd.DataFrame(tree_data)
    df_water = pd.DataFrame(water_data)
    df_parks = pd.DataFrame(park_data)
    df_shelters = pd.DataFrame(shelter_data)
    df_fountains = pd.DataFrame(fountain_data)
    df_green_roofs = pd.DataFrame(green_roof_data)
    df_gardens = pd.DataFrame(garden_data)
    df_forests = pd.DataFrame(forest_data)
    df_wetlands = pd.DataFrame(wetland_data)
    
    df_buildings = pd.DataFrame(building_data)
    df_traffic = pd.DataFrame(traffic_data)
    df_population = pd.DataFrame(population_data)
    
    # Calculate Climate Resilience Score
    score_trees = min(len(trees) * 0.1, 25)      
    score_parks = min(len(parks) * 1.0, 15)      
    score_forests = min(len(forests) * 2.0, 15)
    score_water = min(len(water) * 1.5, 10)     
    score_wetlands = min(len(wetlands) * 3.0, 5)
    score_gardens = min(len(gardens) * 1.0, 10)
    score_green_roofs = min(len(green_roofs) * 2.0, 5)
    score_shelters = min(len(shelters) * 2.0, 10)
    score_fountains = min(len(fountains)* 1.0, 5)
    
    resilience_score = int(score_trees + score_parks + score_forests + score_water + score_wetlands + score_gardens + score_green_roofs + score_shelters + score_fountains)
    if resilience_score == 0:
        resilience_score = random.randint(45, 65) 

    # 3. Physical Sensors (Air Quality Nodes anchored to real AQI)
    sensor_data = []
    for _ in range(25):
        lat = CENTER_LAT + np.random.normal(0, 0.03)
        lon = CENTER_LON + np.random.normal(0, 0.03)
        sensor_id = f"AQ-{fake.bothify(text='##??')}"
        
        # Local variance around the city's true AQI
        local_aqi = max(0, current_aqi + random.randint(-15, 25))
        
        # Color coding: Green (Good), Yellow (Mod), Purple/Red (Poor)
        if local_aqi < 50:
            color = [16, 185, 129, 200] # Emerald
        elif local_aqi < 100:
            color = [245, 158, 11, 200] # Amber
        else:
            color = [239, 68, 68, 200]  # Red
            
        sensor_data.append({
            'lon': lon,
            'lat': lat,
            'sensor_id': sensor_id,
            'aqi': local_aqi,
            'color': color, 
            'tooltip': f"<b style='font-size: 14px; color: #00e5ff;'>Air Quality Node</b><br/><span style='color:#94a3b8; font-size:11px; font-family: monospace;'>ID: {sensor_id}</span><br/><br/><b>US AQI:</b> <span style='font-size: 14px; font-weight:bold;'>{local_aqi}</span><br/><span style='color:#94a3b8; font-size:11px;'>Lat: {lat:.4f} | Lon: {lon:.4f}</span>"
        })
        
    df_sensors = pd.DataFrame(sensor_data)
    
    # 4. Satellite Indices (Synthetic Heatmaps)
    # NDVI (Normalized Difference Vegetation Index) - Higher further from center, simulating greenery vs concrete
    ndvi_data = []
    for _ in range(400):
        lat = CENTER_LAT + np.random.normal(0, 0.02)
        lon = CENTER_LON + np.random.normal(0, 0.02)
        distance = np.sqrt((lat - CENTER_LAT)**2 + (lon - CENTER_LON)**2)
        
        # Inverse of heat island: Greenery increases moving outward
        ndvi_val = min(1.0, 0.2 + (distance * 10) + random.uniform(0, 0.2))
        ndvi_data.append([lon, lat, ndvi_val])
        
    df_ndvi = pd.DataFrame(ndvi_data, columns=['lon', 'lat', 'weight'])
    
    # Albedo (Surface Reflectance) - High in commercial/concrete zones, low in water/trees
    albedo_data = []
    for _ in range(400):
        lat = CENTER_LAT + np.random.normal(0, 0.02)
        lon = CENTER_LON + np.random.normal(0, 0.02)
        distance = np.sqrt((lat - CENTER_LAT)**2 + (lon - CENTER_LON)**2)
        
        # Albedo is typically higher in dense urban centers with concrete
        albedo_val = max(0.1, 0.8 - (distance * 15) + random.uniform(-0.1, 0.1))
        albedo_data.append([lon, lat, albedo_val])
        
    df_albedo = pd.DataFrame(albedo_data, columns=['lon', 'lat', 'weight'])
    
    return df_thermal, df_trees, df_water, df_parks, df_shelters, df_fountains, df_green_roofs, df_gardens, df_forests, df_wetlands, df_sensors, df_ndvi, df_albedo, df_buildings, df_traffic, df_population, resilience_score, current_temp, current_aqi
