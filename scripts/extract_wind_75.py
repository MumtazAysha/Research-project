"""
Extract wind speed using 75th percentile (better for wind resource assessment)
"""
import rasterio
import geopandas as gpd
import pandas as pd
from pathlib import Path
import numpy as np
from rasterio.mask import mask

print("="*70)
print("EXTRACTING WIND SPEED DATA - 75th PERCENTILE METHOD")
print("="*70)

# [Same file loading code as before...]
project_root = Path(__file__).parent.parent
wind_tif_path = project_root / 'LKA_wind-speed_100m (2).tif'

grid_geojson_path = project_root / 'data' / 'bronze' / 'metadata' / 'grid_cells_all.geojson'
coords_csv_path = project_root / 'data' / 'bronze' / 'metadata' / 'grid_with_real_solar_data.csv'
output_csv_path = project_root / 'data' / 'bronze' / 'metadata' / 'grid_with_wind_data.csv'

with rasterio.open(str(wind_tif_path)) as src:
    grid_gdf = gpd.read_file(str(grid_geojson_path))
    print(f"Processing {len(grid_gdf)} cells with 75th percentile method...")
    
    mean_speeds = []
    p75_speeds = []
    median_speeds = []
    
    for i, row in grid_gdf.iterrows():
        if (i + 1) % 100 == 0:
            print(f"   Cell {i+1}/{len(grid_gdf)}...")
        
        try:
            out_image, out_transform = mask(src, [row.geometry], crop=True, all_touched=True)
            cell_data = out_image[0]
            valid_cell_data = cell_data[(cell_data >= 0) & (cell_data < 50)]
            
            if len(valid_cell_data) > 0:
                mean_val = float(np.mean(valid_cell_data))
                p75_val = float(np.percentile(valid_cell_data, 75))
                median_val = float(np.median(valid_cell_data))
                
                mean_speeds.append(round(mean_val, 2))
                p75_speeds.append(round(p75_val, 2))
                median_speeds.append(round(median_val, 2))
            else:
                mean_speeds.append(None)
                p75_speeds.append(None)
                median_speeds.append(None)
        except:
            mean_speeds.append(None)
            p75_speeds.append(None)
            median_speeds.append(None)

# Add all three to compare
grid_gdf['wind_speed_100m_mean'] = mean_speeds
grid_gdf['wind_speed_100m_p75'] = p75_speeds
grid_gdf['wind_speed_100m_median'] = median_speeds

# Use 75th percentile as primary
grid_gdf['wind_speed_100m'] = grid_gdf['wind_speed_100m_p75']

# Merge and classify
solar_data = pd.read_csv(str(coords_csv_path))
merged_data = solar_data.merge(
    grid_gdf[['grid_id', 'wind_speed_100m', 'wind_speed_100m_mean', 'wind_speed_100m_median']], 
    on='grid_id', 
    how='left'
)

def classify_wind_speed(speed):
    if pd.isna(speed):
        return 'No Data'
    elif speed >= 9.0:
        return 'Excellent'
    elif speed >= 7.5:
        return 'Very Good'
    elif speed >= 6.5:
        return 'Good'
    elif speed >= 5.5:
        return 'Moderate'
    elif speed >= 4.0:
        return 'Fair'
    else:
        return 'Poor'

def wind_speed_range(speed):
    if pd.isna(speed):
        return 'No Data'
    elif speed >= 9.0:
        return '≥9.0 m/s'
    elif speed >= 7.5:
        return '7.5-9.0 m/s'
    elif speed >= 6.5:
        return '6.5-7.5 m/s'
    elif speed >= 5.5:
        return '5.5-6.5 m/s'
    elif speed >= 4.0:
        return '4.0-5.5 m/s'
    else:
        return '<4.0 m/s'

merged_data['wind_rating'] = merged_data['wind_speed_100m'].apply(classify_wind_speed)
merged_data['wind_range'] = merged_data['wind_speed_100m'].apply(wind_speed_range)
merged_data['wind_power_density'] = merged_data['wind_speed_100m'].apply(
    lambda x: round(0.5 * 1.225 * (x ** 3), 2) if pd.notna(x) else None
)

# Save
merged_data.to_csv(str(output_csv_path), index=False)

# Statistics comparison
print("\n" + "="*70)
print("COMPARISON: Mean vs 75th Percentile vs Median")
print("="*70)

valid_data = merged_data[merged_data['wind_speed_100m_mean'].notna()]

print(f"\nAverage across all cells:")
print(f"  Mean method:       {valid_data['wind_speed_100m_mean'].mean():.2f} m/s")
print(f"  75th Percentile:   {valid_data['wind_speed_100m'].mean():.2f} m/s ⭐")
print(f"  Median method:     {valid_data['wind_speed_100m_median'].mean():.2f} m/s")

print(f"\n75th Percentile Rating Distribution:")
print(merged_data['wind_rating'].value_counts())

print("\n✓ Using 75th percentile gives more realistic wind resource potential!")
print("="*70)
