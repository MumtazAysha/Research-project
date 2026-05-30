import pandas as pd

coords = pd.read_csv('data/bronze/metadata/grid_coordinates_with_exact_locations.csv')

# Filter unknown cells
unknown = coords[coords['location_name'] == 'Unknown']

print(f"Total Unknown cells: {len(unknown)}")
print(f"\nBy cell type:")
print(unknown['cell_type'].value_counts())

print(f"\nFirst 20 Unknown cells:")
print(unknown[['grid_id', 'centroid_lat', 'centroid_lon', 'cell_type', 'district', 'formatted_address']].head(20))
