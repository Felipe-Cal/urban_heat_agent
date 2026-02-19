import pandas as pd
import numpy as np
import random
from faker import Faker

fake = Faker()

def generate_mock_data(center_lat=34.0522, center_lon=-118.2437):
    """Generates mock data for Thermal, Trees, and Sensors layers centered on provided coordinates."""
    
    # Use provided coordinates
    CENTER_LAT = center_lat
    CENTER_LON = center_lon
    
    # 1. Thermal Data (Heatmap)
    # Generate random points showing heat islands
    thermal_data = []
    for _ in range(500):
        lat = CENTER_LAT + np.random.normal(0, 0.02)
        lon = CENTER_LON + np.random.normal(0, 0.02)
        temp = random.uniform(25, 52) # 25C to 52C
        weight = (temp - 25) / (52 - 25) # Normalize 0-1 for heatmap intensity
        thermal_data.append([lon, lat, weight])
        
    df_thermal = pd.DataFrame(thermal_data, columns=['lon', 'lat', 'weight'])

    # 2. Tree Canopy (Nature ID)
    # Generate green points
    tree_data = []
    tree_species = ['Quercus agrifolia', 'Platanus racemosa', 'Jacaranda mimosifolia', 'Ficus microcarpa']
    health_statuses = ['Optimal', 'Good', 'Stressed']
    owners = ['Public', 'Private', 'Sovereign']
    
    for _ in range(200):
        lat = CENTER_LAT + np.random.normal(0, 0.015)
        lon = CENTER_LON + np.random.normal(0, 0.015)
        tree_id = f"NID-LA-{fake.bothify(text='####')}"
        species = random.choice(tree_species)
        health = random.choice(health_statuses)
        owner = random.choice(owners)
        
        # Calculate tooltip content
        tree_data.append({
            'lon': lon,
            'lat': lat,
            'tree_id': tree_id,
            'species': species,
            'health': health,
            'owner': owner,
            'cooling_status': 'Active (VDP Verified)',
            # Color as RGBA [R, G, B, A]
            'color': [5, 150, 105, 200],  # Emerald-600 RGB
            'tooltip': f"<b>{species}</b><br>ID: {tree_id}<br>Health: {health}<br>Status: Active"
        })
    
    df_trees = pd.DataFrame(tree_data)

    # 3. Sensors (PurpleAir)
    # Sparse grid
    sensor_data = []
    for _ in range(20):
        lat = CENTER_LAT + np.random.normal(0, 0.03)
        lon = CENTER_LON + np.random.normal(0, 0.03)
        sensor_id = f"PA-{fake.bothify(text='##??')}"
        aqi = random.randint(20, 150)
        sensor_data.append({
            'lon': lon,
            'lat': lat,
            'sensor_id': sensor_id,
            'aqi': aqi,
            'color': [124, 58, 237, 200], # Violet-600
            'tooltip': f"<b>Sensor {sensor_id}</b><br>AQI: {aqi}"
        })
        
    df_sensors = pd.DataFrame(sensor_data)
    
    return df_thermal, df_trees, df_sensors
