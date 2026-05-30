import pandas as pd

# Load your wind data
data = pd.read_csv('data/bronze/metadata/grid_with_wind_data.csv')

# Check cell types
print("Cell Type Distribution:")
print(data['cell_type'].value_counts())

print("\nOcean cells with wind data:")
ocean_cells = data[data['cell_type'] == 'ocean']
print(f"Total ocean cells: {len(ocean_cells)}")
print(f"Ocean cells with wind speed: {ocean_cells['wind_speed_100m'].notna().sum()}")

if len(ocean_cells) > 0:
    print("\nSample ocean cells:")
    print(ocean_cells[['grid_id', 'location_name', 'cell_type', 'wind_speed_100m', 'wind_rating']].head(10))
