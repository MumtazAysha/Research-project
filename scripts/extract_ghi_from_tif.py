"""
Extract real GHI values from the downloaded GHI.tif file
"""
import pandas as pd
import rasterio
from pathlib import Path
import numpy as np

# File path - adjust this to where you saved the file
geotiff_path = 'GHI.tif'  # Or 'data/external/GHI.tif' if you moved it

# Check if file exists
if not Path(geotiff_path).exists():
    print(f"❌ File not found: {geotiff_path}")
    print("Please make sure GHI.tif is in the project root directory")
    print("Or update the geotiff_path variable to the correct location")
    exit(1)

print("="*70)
print("EXTRACTING REAL GHI DATA FROM GeoTIFF")
print("="*70)

# Load grid coordinates
print("\nLoading grid data...")
coords = pd.read_csv('data/bronze/metadata/grid_coordinates_with_exact_locations.csv')

print(f"Processing {len(coords)} grid cells...\n")

# Open the GeoTIFF file
try:
    with rasterio.open(geotiff_path) as src:
        print("GeoTIFF File Information:")
        print(f"  ✓ Width: {src.width} pixels")
        print(f"  ✓ Height: {src.height} pixels")
        print(f"  ✓ CRS (Coordinate System): {src.crs}")
        print(f"  ✓ Bounds: {src.bounds}")
        print(f"  ✓ Resolution: {src.res}")
        print(f"  ✓ Data Type: {src.dtypes[0]}")
        print(f"  ✓ No Data Value: {src.nodata}\n")
        
        # Read the raster band
        band1 = src.read(1)
        
        # Get statistics
        valid_data = band1[band1 != src.nodata]
        print(f"Data Statistics:")
        print(f"  Min value: {valid_data.min():.2f}")
        print(f"  Max value: {valid_data.max():.2f}")
        print(f"  Mean value: {valid_data.mean():.2f}")
        print(f"  Median value: {np.median(valid_data):.2f}\n")
        
        print("Extracting GHI for each grid cell...")
        
        # Extract GHI value for each grid cell
        ghi_values = []
        success_count = 0
        fail_count = 0
        
        for idx, row in coords.iterrows():
            lat = row['centroid_lat']
            lon = row['centroid_lon']
            
            try:
                # Sample the raster at this coordinate
                # rasterio uses (lon, lat) order
                for val in src.sample([(lon, lat)]):
                    ghi_value = val[0]
                    
                    # Check if valid data
                    if ghi_value != src.nodata and not np.isnan(ghi_value):
                        ghi = float(ghi_value)
                        
                        # The Global Solar Atlas data is usually in kWh/m²/year
                        # If values are very small (< 10), they might be daily values
                        if ghi < 10:
                            ghi = ghi * 365
                        
                        # Classify based on SLSEA ranges
                        if ghi >= 2042:
                            rating = "Excellent"
                            range_str = "2,042-2,106 kWh/m²"
                        elif ghi >= 2002:
                            rating = "Very Good"
                            range_str = "2,002-2,039 kWh/m²"
                        elif ghi >= 1904:
                            rating = "Good"
                            range_str = "1,904-1,966 kWh/m²"
                        elif ghi >= 1830:
                            rating = "Moderate"
                            range_str = "1,830-1,903 kWh/m²"
                        elif ghi >= 1766:
                            rating = "Low"
                            range_str = "1,766-1,829 kWh/m²"
                        else:
                            rating = "Very Low"
                            range_str = "<1,766 kWh/m²"
                        
                        ghi_values.append({
                            'grid_id': row['grid_id'],
                            'real_ghi': int(ghi),
                            'solar_rating': rating,
                            'solar_range': range_str
                        })
                        success_count += 1
                    else:
                        # No data at this location (probably ocean)
                        ghi_values.append({
                            'grid_id': row['grid_id'],
                            'real_ghi': 1900,
                            'solar_rating': 'Good',
                            'solar_range': 'No data (default)'
                        })
                        fail_count += 1
                        
            except Exception as e:
                # Coordinate outside raster bounds
                ghi_values.append({
                    'grid_id': row['grid_id'],
                    'real_ghi': 1900,
                    'solar_rating': 'Good',
                    'solar_range': 'Outside bounds (default)'
                })
                fail_count += 1
            
            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{len(coords)} cells...")
        
        print(f"\n✓ Extraction complete!")
        print(f"  Successfully extracted: {success_count} cells")
        print(f"  Used defaults: {fail_count} cells")
        
except Exception as e:
    print(f"❌ Error opening GeoTIFF file: {e}")
    print("\nPossible issues:")
    print("  1. File might be corrupted")
    print("  2. rasterio not installed: pip install rasterio")
    print("  3. File format not supported")
    exit(1)

# Create DataFrame
ghi_df = pd.DataFrame(ghi_values)

# Merge with original data
coords_with_real_ghi = coords.merge(ghi_df, on='grid_id', how='left')

# Save
output_file = 'data/bronze/metadata/grid_with_real_solar_data.csv'
coords_with_real_ghi.to_csv(output_file, index=False)

print(f"\n✓ Saved to: {output_file}")

# Statistics
print("\n" + "="*70)
print("REAL SOLAR RESOURCE DISTRIBUTION")
print("="*70)

print("\nSolar Rating Distribution:")
rating_counts = coords_with_real_ghi['solar_rating'].value_counts()
for rating, count in rating_counts.items():
    print(f"  {rating}: {count} cells")

print("\nGHI Statistics:")
print(f"  Min GHI: {coords_with_real_ghi['real_ghi'].min()} kWh/m²/year")
print(f"  Max GHI: {coords_with_real_ghi['real_ghi'].max()} kWh/m²/year")
print(f"  Mean GHI: {coords_with_real_ghi['real_ghi'].mean():.0f} kWh/m²/year")
print(f"  Median GHI: {coords_with_real_ghi['real_ghi'].median():.0f} kWh/m²/year")

print("\n" + "="*70)
print("VERIFICATION: Key Locations")
print("="*70)

# Check key locations that should have high solar
key_locations = ['Jaffna', 'Mannar', 'Kilinochchi', 'Hambantota', 'Trincomalee', 'Batticaloa', 'Puttalam']

for location in key_locations:
    cells = coords_with_real_ghi[coords_with_real_ghi['location_name'].str.contains(location, case=False, na=False)]
    if len(cells) > 0:
        avg_ghi = cells['real_ghi'].mean()
        rating = cells['solar_rating'].mode()[0] if len(cells['solar_rating'].mode()) > 0 else 'N/A'
        print(f"\n{location}:")
        print(f"  Average GHI: {avg_ghi:.0f} kWh/m²/year")
        print(f"  Most Common Rating: {rating}")
        print(f"  Number of cells: {len(cells)}")

print("\n" + "="*70) 
print("✓ Extraction complete! You now have REAL solar data!")
print("="*70)
