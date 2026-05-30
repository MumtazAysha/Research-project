"""
Check what wind speeds were extracted for Hambantota grid cells
"""
import pandas as pd

# Load the extracted wind data
df = pd.read_csv('data/bronze/metadata/grid_with_wind_data.csv')

# Filter Hambantota region (lat 6.0-6.5, lon 80.8-81.5)
hambantota_cells = df[
    (df['centroid_lat'] >= 6.0) & 
    (df['centroid_lat'] <= 6.5) & 
    (df['centroid_lon'] >= 80.8) & 
    (df['centroid_lon'] <= 81.5)
]

print("="*70)
print("HAMBANTOTA GRID CELLS - EXTRACTED WIND DATA")
print("="*70)

print(f"\nTotal Hambantota cells: {len(hambantota_cells)}")

if len(hambantota_cells) > 0:
    print(f"\nWind Speed Statistics:")
    print(f"  Min: {hambantota_cells['wind_speed_100m'].min():.2f} m/s")
    print(f"  Max: {hambantota_cells['wind_speed_100m'].max():.2f} m/s")
    print(f"  Mean: {hambantota_cells['wind_speed_100m'].mean():.2f} m/s ⭐")
    print(f"  Median: {hambantota_cells['wind_speed_100m'].median():.2f} m/s")
    
    print(f"\nRating Distribution:")
    print(hambantota_cells['wind_rating'].value_counts())
    
    print(f"\nSample of Hambantota cells:")
    print(hambantota_cells[['grid_id', 'location_name', 'centroid_lat', 'centroid_lon', 
                            'wind_speed_100m', 'wind_rating']].head(20).to_string(index=False))
    
    # Check if any cells have suspiciously high values
    high_speed = hambantota_cells[hambantota_cells['wind_speed_100m'] >= 8.5]
    if len(high_speed) > 0:
        print(f"\n⚠️ WARNING: {len(high_speed)} cells with speed ≥8.5 m/s (should be rare):")
        print(high_speed[['grid_id', 'location_name', 'wind_speed_100m', 'wind_rating']].to_string(index=False))
else:
    print("\n❌ No Hambantota cells found!")

print("\n" + "="*70)
