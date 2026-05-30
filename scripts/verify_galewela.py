"""
Verify extraction for Galewela - check if 7.23 m/s is correct
"""
import rasterio
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from rasterio.mask import mask

print("="*70)
print("VERIFYING GALEWELA EXTRACTION")
print("="*70)

# Load files
project_root = Path(__file__).parent.parent
tif_path = project_root / 'LKA_wind-speed_100m (2).tif'
grid_gdf = gpd.read_file('data/bronze/metadata/grid_cells_all.geojson')

# Load your extracted data
extracted_data = pd.read_csv('data/bronze/metadata/grid_with_wind_data.csv')

# Find Galewela cell(s)
galewela_cells = extracted_data[extracted_data['location_name'].str.contains('Galewela', case=False, na=False)]

print(f"\nFound {len(galewela_cells)} Galewela cell(s):")
print(galewela_cells[['grid_id', 'location_name', 'centroid_lat', 'centroid_lon', 'wind_speed_100m']].to_string(index=False))

# Pick the first one
if len(galewela_cells) > 0:
    grid_id = galewela_cells.iloc[0]['grid_id']
    extracted_value = galewela_cells.iloc[0]['wind_speed_100m']
    
    print(f"\n{'='*70}")
    print(f"Verifying Grid Cell: {grid_id}")
    print(f"Your extracted value: {extracted_value} m/s")
    print("="*70)
    
    # Get the polygon for this cell
    cell_polygon = grid_gdf[grid_gdf['grid_id'] == grid_id].iloc[0]['geometry']
    
    # Extract from TIF
    with rasterio.open(str(tif_path)) as src:
        print(f"\nExtracting from TIF file...")
        
        # Mask by polygon
        out_image, out_transform = mask(src, [cell_polygon], crop=True, all_touched=True)
        cell_data = out_image[0]
        valid_data = cell_data[(cell_data >= 0) & (cell_data < 50)]
        
        print(f"\nPixels extracted: {len(valid_data)}")
        
        if len(valid_data) > 0:
            print(f"\nStatistics from TIF:")
            print(f"  Minimum: {valid_data.min():.2f} m/s")
            print(f"  Maximum: {valid_data.max():.2f} m/s")
            print(f"  Mean: {valid_data.mean():.2f} m/s ⭐")
            print(f"  Median: {np.median(valid_data):.2f} m/s")
            print(f"  75th percentile: {np.percentile(valid_data, 75):.2f} m/s")
            print(f"  25th percentile: {np.percentile(valid_data, 25):.2f} m/s")
            
            print(f"\nValue Distribution:")
            print(f"  < 7.0 m/s:  {np.sum(valid_data < 7.0)} pixels ({np.sum(valid_data < 7.0)/len(valid_data)*100:.1f}%)")
            print(f"  7.0-8.0:    {np.sum((valid_data >= 7.0) & (valid_data < 8.0))} pixels ({np.sum((valid_data >= 7.0) & (valid_data < 8.0))/len(valid_data)*100:.1f}%)")
            print(f"  8.0-9.0:    {np.sum((valid_data >= 8.0) & (valid_data < 9.0))} pixels ({np.sum((valid_data >= 8.0) & (valid_data < 9.0))/len(valid_data)*100:.1f}%)")
            print(f"  ≥ 9.0 m/s:  {np.sum(valid_data >= 9.0)} pixels ({np.sum(valid_data >= 9.0)/len(valid_data)*100:.1f}%)")
            
            # Check if extraction matches
            calculated_mean = valid_data.mean()
            
            print(f"\n{'='*70}")
            print("VERIFICATION RESULT:")
            print(f"  Your extracted value: {extracted_value} m/s")
            print(f"  Recalculated mean:    {calculated_mean:.2f} m/s")
            
            if abs(calculated_mean - extracted_value) < 0.1:
                print(f"  ✅ MATCH! Extraction is working correctly!")
            else:
                print(f"  ⚠️ MISMATCH! Difference: {abs(calculated_mean - extracted_value):.2f} m/s")
                print(f"  Your extraction method might need checking.")
        else:
            print("❌ No valid data in this cell")
else:
    print("\n❌ No Galewela cells found in extracted data")

print("\n" + "="*70)
