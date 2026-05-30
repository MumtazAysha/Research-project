"""Debug hydro grids"""
import pandas as pd
import geopandas as gpd
from pathlib import Path

# Check hydro file
print("="*70)
print("CHECKING HYDRO FILE")
print("="*70)

hydro_files = ["Hydro power plants.xlsx", "Hydro-power-plants-1.xlsx"]
for hf in hydro_files:
    if Path(hf).exists():
        print(f"✓ Found: {hf}")
        hydro = pd.read_excel(hf)
        print(f"  Columns: {list(hydro.columns)}")
        print(f"  Rows: {len(hydro)}")

        coord_col = next((c for c in hydro.columns if 'coord' in str(c).lower()), None)
        print(f"  Coordinate column: {coord_col}")

        if coord_col:
            print(f"\nSample coordinates:")
            print(hydro[coord_col].head())
    else:
        print(f"✗ Not found: {hf}")

print("\n" + "="*70)
print("CHECKING PREVIOUS HYDRO FILE")
print("="*70)

prev_hydro = "data/bronze/metadata/hydro_resource_weather_stations_with_parameters.csv"
if Path(prev_hydro).exists():
    df = pd.read_csv(prev_hydro)
    print(f"✓ Previous file exists: {len(df)} stations")
    print(f"\nGrids: {sorted(df['grid_id'].unique())}")
else:
    print("✗ Previous file not found")

print("\n" + "="*70)
print("CHECKING GRID INTERSECTIONS")
print("="*70)

solar_data = pd.read_csv("data/bronze/metadata/grid_with_real_solar_data.csv")
wind_data = pd.read_csv("data/bronze/metadata/grid_with_wind_data.csv")

solar_grids = set(solar_data[solar_data['solar_rating'].isin(['Excellent', 'Very Good', 'Good', 'Moderate'])]['grid_id'])
wind_grids = set(wind_data[(wind_data['wind_rating'].isin(['Excellent', 'Very Good', 'Good', 'Moderate'])) & (wind_data['wind_speed_100m'].notna())]['grid_id'])

print(f"Solar grids: {len(solar_grids)}")
print(f"Wind grids: {len(wind_grids)}")

# Try to load previous hydro grids
prev_common = "data/bronze/metadata/common_resource_weather_stations.csv"
if Path(prev_common).exists():
    df_common = pd.read_csv(prev_common)
    print(f"\n✓ Previous common file: {len(df_common)} stations")
    common_grids_prev = set(df_common['grid_id'].unique())
    print(f"  Common grids from previous: {len(common_grids_prev)}")
    print(f"  Grids: {sorted(common_grids_prev)}")