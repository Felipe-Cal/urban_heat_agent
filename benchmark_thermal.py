import time
import numpy as np
import pandas as pd

def original_logic(center_lat, center_lon, num_interp_points=2000, steps=10):
    # Setup data
    lat_step = 0.006
    lon_step = 0.006
    start_lat = center_lat - (lat_step * steps / 2)
    start_lon = center_lon - (lon_step * steps / 2)

    lats = []
    lons = []
    for i in range(steps):
        for j in range(steps):
            lats.append(round(start_lat + i * lat_step, 6))
            lons.append(round(start_lon + j * lon_step, 6))

    raw_temps = [25.0 + np.random.random() * 5 for _ in range(steps*steps)]

    # Logic from data_generator.py
    thermal_data = []

    grid_pts = np.column_stack((lats, lons))
    temps_arr = np.array(raw_temps)

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
    temp_variation = 2.0 # simplified

    start_time = time.perf_counter()
    for r_lon, r_lat, t in zip(rand_lons, rand_lats, interp_temps):
        t += temp_variation
        frac = np.clip((t - t_lo) / (t_hi - t_lo), 0.0, 1.0)
        norm_t = 0.05 + 0.45 * frac
        thermal_data.append([r_lon, r_lat, norm_t])

    df_thermal = pd.DataFrame(thermal_data, columns=["lon", "lat", "weight"])
    end_time = time.perf_counter()
    return end_time - start_time

def optimized_logic(center_lat, center_lon, num_interp_points=2000, steps=10):
    # Setup data
    lat_step = 0.006
    lon_step = 0.006
    start_lat = center_lat - (lat_step * steps / 2)
    start_lon = center_lon - (lon_step * steps / 2)

    lats = []
    lons = []
    for i in range(steps):
        for j in range(steps):
            lats.append(round(start_lat + i * lat_step, 6))
            lons.append(round(start_lon + j * lon_step, 6))

    raw_temps = [25.0 + np.random.random() * 5 for _ in range(steps*steps)]

    # Logic from data_generator.py
    grid_pts = np.column_stack((lats, lons))
    temps_arr = np.array(raw_temps)

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
    temp_variation = 2.0 # simplified

    start_time = time.perf_counter()

    # Vectorized
    # Apply variation
    interp_temps = interp_temps + temp_variation

    # Calculate fraction
    # (t - t_lo) / (t_hi - t_lo)
    fracs = (interp_temps - t_lo) / (t_hi - t_lo)

    # Clip
    fracs = np.clip(fracs, 0.0, 1.0)

    # Normalize
    norm_ts = 0.05 + 0.45 * fracs

    # Stack columns
    thermal_data = np.column_stack((rand_lons, rand_lats, norm_ts))

    # Create DataFrame
    df_thermal = pd.DataFrame(thermal_data, columns=["lon", "lat", "weight"])

    end_time = time.perf_counter()
    return end_time - start_time

t_orig = 0
t_opt = 0
N = 100
for _ in range(N):
    t_orig += original_logic(34.05, -118.24)
    t_opt += optimized_logic(34.05, -118.24)

print(f"Original avg: {t_orig/N*1000:.4f} ms")
print(f"Optimized avg: {t_opt/N*1000:.4f} ms")
print(f"Speedup: {t_orig/t_opt:.2f}x")
