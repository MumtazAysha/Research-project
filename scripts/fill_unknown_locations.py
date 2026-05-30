"""
Fill 'Unknown' location names with nearest known location
"""
import pandas as pd
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in km"""
    R = 6371  # Earth radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a)) 
    
    return R * c

def find_nearest_known_location(unknown_lat, unknown_lon, known_cells):
    """Find the nearest cell with a known location name"""
    
    min_distance = float('inf')
    nearest_location = 'Unknown'
    nearest_district = 'Unknown' 
    
    for idx, row in known_cells.iterrows():
        distance = haversine_distance(
            unknown_lat, unknown_lon,
            row['centroid_lat'], row['centroid_lon']
        )
        
        if distance < min_distance:
            min_distance = distance
            nearest_location = row['location_name']
            nearest_district = row['district']
    
    # Add "Near" prefix if distance > 5km
    if min_distance > 5:
        nearest_location = f"Near {nearest_location}"
    
    return nearest_location, nearest_district, min_distance

# Load data
coords = pd.read_csv('data/bronze/metadata/grid_coordinates_with_exact_locations.csv')

print("Filling 'Unknown' locations with nearest known settlements...")

# Separate known and unknown cells (excluding ocean)
unknown_cells = coords[
    (coords['location_name'] == 'Unknown') & 
    (coords['cell_type'] != 'ocean')
]

known_cells = coords[
    (coords['location_name'] != 'Unknown') & 
    (coords['cell_type'] != 'ocean')
]

print(f"\nUnknown cells to process: {len(unknown_cells)}")
print(f"Known cells to reference: {len(known_cells)}")

# Process each unknown cell
updated_count = 0

for idx, row in unknown_cells.iterrows():
    nearest_name, nearest_district, distance = find_nearest_known_location(
        row['centroid_lat'],
        row['centroid_lon'],
        known_cells
    )
    
    coords.at[idx, 'location_name'] = nearest_name
    coords.at[idx, 'district'] = nearest_district
    coords.at[idx, 'locality'] = f"{nearest_name} Region"
    
    updated_count += 1
    
    if updated_count % 50 == 0:
        print(f"  Processed {updated_count}/{len(unknown_cells)}...")

# Save updated data
output_file = 'data/bronze/metadata/grid_coordinates_complete.csv'
coords.to_csv(output_file, index=False)

print(f"\n✓ Updated {updated_count} cells")
print(f"✓ Saved to: {output_file}")

# Show statistics
print("\n" + "="*70)
print("UPDATED LOCATION DISTRIBUTION")
print("="*70)
print(coords['location_name'].value_counts().head(30))

# Check if any unknowns remain
remaining_unknown = len(coords[coords['location_name'] == 'Unknown'])
print(f"\nRemaining 'Unknown' cells: {remaining_unknown}")
