"""
Extract wind speed data from Global Wind Atlas GeoTIFF for all grid cells
CORRECTED: Uses MEAN (average) value within each cell for better representation
"""
import rasterio
import geopandas as gpd
import pandas as pd
from pathlib import Path
import numpy as np
from rasterio.mask import mask


print("="*70)
print("EXTRACTING WIND SPEED DATA FROM GEOTIFF")
print("Method: MEAN wind speed within each 10km x 10km cell")
print("="*70)


# File paths
project_root = Path(__file__).parent.parent

possible_wind_paths = [
    project_root / 'LKA_wind-speed_100m (2).tif',
    project_root / 'data' / 'bronze' / 'geotiff' / 'LKA_wind-speed_100m-2.tif',
    Path.home() / 'Downloads' / 'LKA_wind-speed_100m-2.tif',
]

print("\nSearching for wind TIF file...")
wind_tif_path = None
for path in possible_wind_paths:
    if path.exists():
        wind_tif_path = str(path)
        print(f"  ✓ Found: {path}")
        break

if wind_tif_path is None:
    print("\n❌ ERROR: Could not find wind TIF file")
    exit(1)

grid_geojson_path = project_root / 'data' / 'bronze' / 'metadata' / 'grid_cells_all.geojson'
coords_csv_path = project_root / 'data' / 'bronze' / 'metadata' / 'grid_with_real_solar_data.csv'
output_csv_path = project_root / 'data' / 'bronze' / 'metadata' / 'grid_with_wind_data.csv'


# Load the wind speed GeoTIFF
print(f"\n1. Loading Wind Speed GeoTIFF...")
with rasterio.open(wind_tif_path) as src:
    print(f"   ✓ CRS: {src.crs}")
    print(f"   ✓ Resolution: {src.res}")
    
    # Load grid cells
    print("\n2. Loading grid cells...")
    grid_gdf = gpd.read_file(str(grid_geojson_path))
    print(f"   ✓ Loaded {len(grid_gdf)} grid cells")
    
    # Extract wind speed for each grid cell using MEAN
    print("\n3. Extracting MEAN wind speed for each cell...")
    print("   (This may take a few minutes...)")
    
    mean_speeds = []
    min_speeds = []
    max_speeds = []
    valid_count = 0
    nodata_count = 0
    
    for i, row in grid_gdf.iterrows():
        if (i + 1) % 100 == 0:
            print(f"   Processing cell {i+1}/{len(grid_gdf)}...")
        
        try:
            # Mask the raster by the grid cell polygon
            out_image, out_transform = mask(src, [row.geometry], crop=True, all_touched=True)
            
            # Extract valid values (not NoData)
            cell_data = out_image[0]
            valid_cell_data = cell_data[(cell_data >= 0) & (cell_data < 50)]
            
            if len(valid_cell_data) > 0:
                # Calculate statistics
                mean_value = float(np.mean(valid_cell_data))
                min_value = float(np.min(valid_cell_data))
                max_value = float(np.max(valid_cell_data))
                
                mean_speeds.append(round(mean_value, 2))
                min_speeds.append(round(min_value, 2))
                max_speeds.append(round(max_value, 2))
                valid_count += 1
            else:
                mean_speeds.append(None)
                min_speeds.append(None)
                max_speeds.append(None)
                nodata_count += 1
                
        except Exception as e:
            mean_speeds.append(None)
            min_speeds.append(None)
            max_speeds.append(None)
            nodata_count += 1
    
    print(f"   ✓ Valid cells: {valid_count}")
    print(f"   ✓ NoData/Ocean cells: {nodata_count}")


# Add wind data to grid
grid_gdf['wind_speed_100m'] = mean_speeds
grid_gdf['wind_speed_100m_min'] = min_speeds
grid_gdf['wind_speed_100m_max'] = max_speeds


# Load existing solar data to merge
print("\n4. Merging with existing solar data...")
solar_data = pd.read_csv(str(coords_csv_path))

merged_data = solar_data.merge(
    grid_gdf[['grid_id', 'wind_speed_100m', 'wind_speed_100m_min', 'wind_speed_100m_max']], 
    on='grid_id', 
    how='left'
)


# Classify wind speed ratings
print("\n5. Classifying wind resource quality...")

def classify_wind_speed(speed):
    """Classify wind speed - adjusted thresholds"""
    if pd.isna(speed) or speed is None:
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
    """Return wind speed range"""
    if pd.isna(speed) or speed is None:
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

# Calculate wind power density
merged_data['wind_power_density'] = merged_data['wind_speed_100m'].apply(
    lambda x: round(0.5 * 1.225 * (x ** 3), 2) if pd.notna(x) else None
)


# Save to CSV
print("\n6. Saving results...")
merged_data.to_csv(str(output_csv_path), index=False)
print(f"   ✓ Saved to: {output_csv_path}")


# Statistics
print("\n" + "="*70)
print("WIND SPEED STATISTICS (MEAN values per cell)")
print("="*70)

wind_data_only = merged_data[merged_data['wind_speed_100m'].notna()]

print(f"\nTotal grid cells: {len(merged_data)}")
print(f"Cells with wind data: {len(wind_data_only)}")

if len(wind_data_only) > 0:
    print(f"\nWind Speed (100m height) - MEAN per cell:")
    print(f"  Min: {wind_data_only['wind_speed_100m'].min():.2f} m/s")
    print(f"  Max: {wind_data_only['wind_speed_100m'].max():.2f} m/s")
    print(f"  Mean: {wind_data_only['wind_speed_100m'].mean():.2f} m/s")
    print(f"  Median: {wind_data_only['wind_speed_100m'].median():.2f} m/s")
    
    print(f"\nWind Rating Distribution:")
    rating_counts = merged_data['wind_rating'].value_counts()
    for rating, count in rating_counts.items():
        percentage = (count / len(merged_data)) * 100
        print(f"  {rating}: {count} cells ({percentage:.1f}%)")
    
    print(f"\nTop 10 locations with highest MEAN wind speeds:")
    top_wind = merged_data.nlargest(10, 'wind_speed_100m')[
        ['grid_id', 'location_name', 'district', 'wind_speed_100m', 'wind_rating']
    ]
    print(top_wind.to_string(index=False))
    
    # Check specific areas
    print(f"\n" + "="*70)
    print("CHECKING SPECIFIC AREAS")
    print("="*70)
    
    check_areas = ['Galewela', 'Dambulla', 'Galgamuwa', 'Kandy']
    for area in check_areas:
        area_data = merged_data[merged_data['location_name'].str.contains(area, case=False, na=False)]
        if len(area_data) > 0:
            print(f"\n{area}:")
            print(f"  Cells: {len(area_data)}")
            print(f"  Mean wind speed: {area_data['wind_speed_100m'].mean():.2f} m/s")
            print(f"  Range: {area_data['wind_speed_100m'].min():.2f} - {area_data['wind_speed_100m'].max():.2f} m/s")
            print(f"  Ratings: {dict(area_data['wind_rating'].value_counts())}")

print("\n" + "="*70)
print("✓ Wind speed extraction complete!")
print("="*70)

