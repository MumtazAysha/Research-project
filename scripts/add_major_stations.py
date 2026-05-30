"""Add Major Stations - Use existing hydro grids"""
import pandas as pd
import geopandas as gpd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("LOADING MAJOR STATIONS")
print("="*70)

met_stations = pd.read_csv("data/raw/stations/Copy of Met Stations Met Stations & Parameters.xlsx.csv")
print(f"✓ {len(met_stations)} stations loaded\n")

for _, row in met_stations.iterrows():
    print(f"  {str(row['id']):10s} {row['station_name']:20s} ({row['longitude']:.2f}, {row['latitude']:.2f})")

print("\n" + "="*70)
print("MAPPING TO GRIDS")
print("="*70)

grid_gdf = gpd.read_file("data/bronze/metadata/grid_cells_all.geojson")
station_mapping = pd.read_csv("data/bronze/metadata/grid_weather_station_mapping.csv")

met_stations['geometry'] = gpd.points_from_xy(met_stations['longitude'], met_stations['latitude'])
met_gdf = gpd.GeoDataFrame(met_stations, geometry='geometry', crs='EPSG:4326')

met_with_grids = gpd.sjoin(met_gdf, grid_gdf[['grid_id', 'geometry']], how='inner', predicate='within')

major_mapping = pd.DataFrame({
    'grid_id': met_with_grids['grid_id'],
    'station_id': met_with_grids['id'].astype(str),
    'station_name': met_with_grids['station_name'],
    'district': '',
    'lat': met_with_grids['latitude'],
    'lon': met_with_grids['longitude']
})

print(f"✓ Mapped {len(major_mapping)} stations\n")

# Remove old major stations, add new ones
station_mapping = station_mapping[~station_mapping['station_id'].astype(str).str.startswith('43', na=False)]
station_mapping = pd.concat([station_mapping, major_mapping], ignore_index=True)

print("="*70)
print("ADDING PARAMETERS")
print("="*70)

param_lookup = {}
for _, row in met_stations.iterrows():
    param_lookup[str(row['id']).strip()] = {
        'parameters_available': 'Rainfall, Temperature (Max/Min/Dry/Wet), Relative Humidity, Wind Speed & Direction, Pressure (MSL & SL), Visibility, Cloud Cover, Weather Observations',
        'parameter_type': 'Full Meteorological',
        'observation_frequency': '3-hourly (0000-2100 UTC)',
        'num_parameters': 8
    }

try:
    rainfall = pd.read_csv("data/raw/stations/Copy of Met Stations Rainfall Stations & Parameters 2023-2025.xlsx.csv", on_bad_lines='skip')
    for _, row in rainfall.iterrows():
        sid = str(row['id']).strip()
        if sid not in param_lookup:
            param_lookup[sid] = {'parameters_available': 'Rainfall', 'parameter_type': 'Rainfall Only', 'observation_frequency': 'Daily/Monthly', 'num_parameters': 1}
except: pass

print(f"✓ {len(param_lookup)} stations in lookup\n")

def add_params(row):
    sid = str(row['station_id']).strip()
    return pd.Series(param_lookup.get(sid, {'parameters_available': 'Rainfall', 'parameter_type': 'Rainfall Only', 'observation_frequency': 'Daily/Monthly', 'num_parameters': 1}))

print("="*70)
print("SAVING FILES")
print("="*70)

output_dir = Path("data/bronze/metadata")
station_mapping.to_csv(output_dir / "grid_weather_station_mapping_with_major.csv", index=False)
print("✓ grid_weather_station_mapping_with_major.csv")

solar_data = pd.read_csv("data/bronze/metadata/grid_with_real_solar_data.csv")
wind_data = pd.read_csv("data/bronze/metadata/grid_with_wind_data.csv")

solar_grids = set(solar_data[solar_data['solar_rating'].isin(['Excellent', 'Very Good', 'Good', 'Moderate'])]['grid_id'])
wind_grids = set(wind_data[(wind_data['wind_rating'].isin(['Excellent', 'Very Good', 'Good', 'Moderate'])) & (wind_data['wind_speed_100m'].notna())]['grid_id'])

# Load existing hydro and common grids from previous files
print("\n✓ Using existing hydro grids from previous files")
prev_hydro = pd.read_csv("data/bronze/metadata/hydro_resource_weather_stations_with_parameters.csv")
hydro_grids = set(prev_hydro['grid_id'].unique())
print(f"  Hydro grids: {len(hydro_grids)}")

prev_common = pd.read_csv("data/bronze/metadata/common_resource_weather_stations.csv")
common_grids = set(prev_common['grid_id'].unique())
print(f"  Common grids: {len(common_grids)}")

for name, grids in [('solar', solar_grids), ('wind', wind_grids), ('hydro', hydro_grids), ('common', common_grids)]:
    df = station_mapping[station_mapping['grid_id'].isin(grids)].copy()
    if len(df) > 0:
        df = pd.concat([df, df.apply(add_params, axis=1)], axis=1)
        df.to_csv(output_dir / f"{name}_resource_weather_stations_with_parameters.csv", index=False)
        fm = len(df[df['parameter_type']=='Full Meteorological'])
        print(f"✓ {name}: {len(df)} stations ({fm} full met)")
    else:
        print(f"✗ {name}: No stations found")

print("\n✅ DONE!")