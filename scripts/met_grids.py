"""
Extract Grids with At Least One Weather Station
(Met, Rainfall Old, or Rainfall New)
Shows location name, coordinates, and what types of data are available
"""
import pandas as pd
import geopandas as gpd
from pathlib import Path

print("="*70)
print("GRIDS WITH AT LEAST ONE WEATHER STATION")
print("="*70)

# Load grid GeoJSON to get proper coordinates
print("\nLoading grid data...")
grid_gdf = gpd.read_file("data/bronze/metadata/grid_cells_all.geojson")

# Calculate centroids if not present
if 'centroid_lat' not in grid_gdf.columns:
    print("Calculating grid centroids...")
    grid_gdf['centroid_lat'] = grid_gdf.geometry.centroid.y
    grid_gdf['centroid_lon'] = grid_gdf.geometry.centroid.x

# Load grid summary
grid_summary = pd.read_csv('outputs/reports/grid_summary.csv')

# Merge to get coordinates
grid_summary = grid_summary.merge(
    grid_gdf[['grid_id', 'centroid_lat', 'centroid_lon']], 
    on='grid_id', 
    how='left'
)

# Filter grids with at least one station
grids_with_stations = grid_summary[grid_summary['total_stations'] > 0].copy()

print(f"\nFound {len(grids_with_stations)} grids with at least one station")

# Prepare report data
report_data = []

for idx, row in grids_with_stations.iterrows():
    # Check which types of stations exist
    has_met = row['met'] > 0
    has_old = row['rainfall_old'] > 0
    has_new = row['rainfall_new'] > 0

    # Create list of available data types
    data_types = []
    if has_met:
        data_types.append(f"Met ({int(row['met'])})")
    if has_old:
        data_types.append(f"Rainfall-Old ({int(row['rainfall_old'])})")
    if has_new:
        data_types.append(f"Rainfall-New ({int(row['rainfall_new'])})")

    report_data.append({
        'Location_Name': row['location_name'],
        'Grid_ID': row['grid_id'],
        'Latitude': round(row['centroid_lat'], 5) if pd.notna(row['centroid_lat']) else 'N/A',
        'Longitude': round(row['centroid_lon'], 5) if pd.notna(row['centroid_lon']) else 'N/A',
        'Total_Stations': int(row['total_stations']),
        'Has_Met_Station': 'Yes' if has_met else 'No',
        'Has_Rainfall_Old': 'Yes' if has_old else 'No',
        'Has_Rainfall_New': 'Yes' if has_new else 'No',
        'Met_Count': int(row['met']),
        'Rainfall_Old_Count': int(row['rainfall_old']),
        'Rainfall_New_Count': int(row['rainfall_new']),
        'Available_Data_Types': ', '.join(data_types)
    })

# Create DataFrame
report_df = pd.DataFrame(report_data)
report_df = report_df.sort_values('Total_Stations', ascending=False)

# Save report
output_path = Path('outputs/reports/grids_with_stations.csv')
report_df.to_csv(output_path, index=False)

print(f"\n✓ Saved: {output_path}")

# Print statistics
print(f"\n{'='*70}")
print("STATISTICS:")
print("="*70)
print(f"Total grids with stations: {len(report_df)}")
print(f"Grids with Met stations: {(report_df['Has_Met_Station'] == 'Yes').sum()}")
print(f"Grids with Rainfall Old: {(report_df['Has_Rainfall_Old'] == 'Yes').sum()}")
print(f"Grids with Rainfall New: {(report_df['Has_Rainfall_New'] == 'Yes').sum()}")
print(f"\nGrids with all 3 types: {((report_df['Has_Met_Station'] == 'Yes') & (report_df['Has_Rainfall_Old'] == 'Yes') & (report_df['Has_Rainfall_New'] == 'Yes')).sum()}")
print(f"Grids with only Met: {((report_df['Has_Met_Station'] == 'Yes') & (report_df['Has_Rainfall_Old'] == 'No') & (report_df['Has_Rainfall_New'] == 'No')).sum()}")
print(f"Grids with only Rainfall: {((report_df['Has_Met_Station'] == 'No') & ((report_df['Has_Rainfall_Old'] == 'Yes') | (report_df['Has_Rainfall_New'] == 'Yes'))).sum()}")

# Show top 20
print(f"\n{'='*70}")
print("TOP 20 GRIDS BY TOTAL STATION COUNT:")
print("="*70)
print(report_df[['Location_Name', 'Latitude', 'Longitude', 'Total_Stations', 'Available_Data_Types']].head(20).to_string(index=False))

# Show sample with all details
print(f"\n{'='*70}")
print("SAMPLE (First 10 with all details):")
print("="*70)
print(report_df[['Location_Name', 'Latitude', 'Longitude', 'Has_Met_Station', 'Has_Rainfall_Old', 'Has_Rainfall_New', 'Total_Stations']].head(10).to_string(index=False))

print(f"\n{'='*70}")
print("✓ REPORT GENERATED SUCCESSFULLY!")
print("="*70)
print(f"\nFile saved to: {output_path}")
print(f"\nThis file contains ALL {len(report_df)} grids with at least one station")
print(f"\nColumns include:")
print(f"  - Location_Name")
print(f"  - Grid_ID")
print(f"  - Latitude & Longitude (grid center coordinates)")
print(f"  - Total number of stations")
print(f"  - Whether it has Met/Rainfall Old/Rainfall New data")
print(f"  - Count of each type")
print(f"  - Summary of available data types")
print(f"\n✓ All coordinates properly calculated from grid geometry!")