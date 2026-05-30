"""
Find common weather locations with parameters - FUZZY NAME MATCHING
Matches major met stations even when names have suffixes
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# STEP 0: Load Meteorological Station Parameter Data
# ============================================================================

print("="*70)
print("LOADING METEOROLOGICAL STATION PARAMETERS")
print("="*70)

met_params_file = "data/raw/stations/Copy of Met Stations Met Stations & Parameters.xlsx.csv"
rainfall_params_file = "data/raw/stations/Copy of Met Stations Rainfall Stations & Parameters 2023-2025.xlsx.csv"

try:
    print(f"Loading: {met_params_file}")
    try:
        met_stations = pd.read_csv(met_params_file, on_bad_lines='skip', encoding='utf-8')
    except TypeError:
        met_stations = pd.read_csv(met_params_file, error_bad_lines=False, encoding='utf-8')

    print(f"✓ Loaded {len(met_stations)} major met stations")

    print(f"\nLoading: {rainfall_params_file}")
    try:
        rainfall_stations = pd.read_csv(rainfall_params_file, on_bad_lines='skip', encoding='utf-8')
    except TypeError:
        rainfall_stations = pd.read_csv(rainfall_params_file, error_bad_lines=False, encoding='utf-8')

    print(f"✓ Loaded {len(rainfall_stations)} rainfall stations")

except Exception as e:
    print(f"ERROR: {e}")
    exit(1)


# ============================================================================
# Create Parameter Lookup with FUZZY MATCHING
# ============================================================================

print("\n" + "="*70)
print("PROCESSING PARAMETER INFORMATION (FUZZY MATCHING)")
print("="*70)

# The 24 major met stations - these have FULL parameters
MAJOR_MET_STATIONS = {
    'BANDARAWELA': 'Full Meteorological',
    'JAFFNA': 'Full Meteorological',
    'MULLATIVE': 'Full Meteorological',
    'MANNAR': 'Full Meteorological',
    'VAVUNIYA': 'Full Meteorological',
    'TRINCOMALEE': 'Full Meteorological',
    'ANURADHAPURA': 'Full Meteorological',
    'MAHA ILLUPPALLAMA': 'Full Meteorological',
    'PUTTALAM': 'Full Meteorological',
    'BATTICALOA': 'Full Meteorological',
    'KURUNEGALA': 'Full Meteorological',
    'KATUGASTOTA': 'Full Meteorological',
    'KATUNAYAKA': 'Full Meteorological',
    'COLOMBO': 'Full Meteorological',
    'NUWARA ELIYA': 'Full Meteorological',
    'BADULLA': 'Full Meteorological',
    'RATNAPURA': 'Full Meteorological',
    'GALLE': 'Full Meteorological',
    'HAMBANTOTA': 'Full Meteorological',
    'POTTUVIL': 'Full Meteorological',
    'MATTALA': 'Full Meteorological',
    'MONARAGALA': 'Full Meteorological',
    'POLONNARUWA': 'Full Meteorological',
    'RATMALANA': 'Full Meteorological'
}

def is_major_station(station_name):
    """
    Check if a station name matches any of the 24 major met stations
    Uses fuzzy matching (checks if major station name is IN the given name)
    """
    name_upper = str(station_name).upper().strip()

    for major_name in MAJOR_MET_STATIONS.keys():
        # Check if the major station name appears in the given name
        # e.g., "COLOMBO" matches "COLOMBO-FORT (S.G.O)"
        if major_name in name_upper:
            return True, major_name

    return False, None

def get_station_parameters(station_name):
    """
    Return parameter info for a station based on fuzzy name matching
    """
    is_major, major_name = is_major_station(station_name)

    if is_major:
        return {
            'parameters_available': 'Rainfall, Temperature (Max/Min/Dry/Wet), Relative Humidity, Wind Speed & Direction, Pressure (MSL & SL), Visibility, Cloud Cover, Weather Observations',
            'parameter_type': 'Full Meteorological',
            'observation_frequency': '3-hourly (0000-2100 UTC)',
            'num_parameters': 8,
            'matched_major_station': major_name
        }
    else:
        return {
            'parameters_available': 'Rainfall',
            'parameter_type': 'Rainfall Only',
            'observation_frequency': 'Daily/Monthly',
            'num_parameters': 1,
            'matched_major_station': None
        }


# ============================================================================
# STEP 1: Load Grid and Resource Data
# ============================================================================

print("\n" + "="*70)
print("LOADING GRID AND RESOURCE DATA")
print("="*70)

try:
    grid_gdf = gpd.read_file("data/bronze/metadata/grid_cells_all.geojson")
    print(f"✓ Grid cells: {len(grid_gdf)}")

    station_mapping = pd.read_csv("data/bronze/metadata/grid_weather_station_mapping.csv")
    print(f"✓ Station mappings: {len(station_mapping)}")

    solar_data = pd.read_csv("data/bronze/metadata/grid_with_real_solar_data.csv")
    print(f"✓ Solar data: {len(solar_data)} grids")

    wind_data = pd.read_csv("data/bronze/metadata/grid_with_wind_data.csv")
    print(f"✓ Wind data: {len(wind_data)} grids")

    hydro_file = "Hydro power plants.xlsx"
    if not Path(hydro_file).exists():
        hydro_file = "Hydro-power-plants-1.xlsx"

    hydro_plants = pd.read_excel(hydro_file)
    print(f"✓ Hydro plants: {len(hydro_plants)}")

except Exception as e:
    print(f"ERROR loading data: {e}")
    exit(1)


# ============================================================================
# STEP 2-4: Filter Resource Grids
# ============================================================================

print("\n" + "="*70)
print("FILTERING RESOURCE GRIDS")
print("="*70)

# Solar
solar_good = ['Excellent', 'Very Good', 'Good', 'Moderate']
solar_filtered = solar_data[solar_data['solar_rating'].isin(solar_good)].copy()
solar_grids = set(solar_filtered['grid_id'])
print(f"✓ Solar grids: {len(solar_grids)}")

# Wind
wind_good = ['Excellent', 'Very Good', 'Good', 'Moderate']
wind_filtered = wind_data[
    wind_data['wind_rating'].isin(wind_good) & 
    wind_data['wind_speed_100m'].notna()
].copy()
wind_grids = set(wind_filtered['grid_id'])
print(f"✓ Wind grids: {len(wind_grids)}")

# Hydro
def parse_coords(coord_str):
    try:
        coord_str = str(coord_str).strip()
        if ',' in coord_str:
            parts = coord_str.split(',')
        else:
            parts = coord_str.split()
        return pd.Series({'Latitude': float(parts[0]), 'Longitude': float(parts[1])})
    except:
        return pd.Series({'Latitude': None, 'Longitude': None})

hydro_df = None
for hr in [0, 1, 2]:
    try:
        hp = pd.read_excel(hydro_file, header=hr)
        if any('coord' in str(c).lower() for c in hp.columns):
            hydro_df = hp
            break
    except:
        continue

if hydro_df is None:
    hydro_df = hydro_plants

coord_col = next((c for c in hydro_df.columns if 'coord' in str(c).lower()), None)
if not coord_col and len(hydro_df.columns) >= 3:
    coord_col = list(hydro_df.columns)[2]

if coord_col:
    hydro_df[['Latitude', 'Longitude']] = hydro_df[coord_col].apply(parse_coords)
    hydro_df = hydro_df.dropna(subset=['Latitude', 'Longitude'])
    hydro_df['geometry'] = gpd.points_from_xy(hydro_df['Longitude'], hydro_df['Latitude'])
    hydro_gdf = gpd.GeoDataFrame(hydro_df, geometry='geometry', crs='EPSG:4326')
    hydro_with_grids = gpd.sjoin(hydro_gdf, grid_gdf[['grid_id', 'geometry']], 
                                   how='inner', predicate='within')
    hydro_grids = set(hydro_with_grids['grid_id'])
    print(f"✓ Hydro grids: {len(hydro_grids)}")
else:
    hydro_grids = set()
    hydro_with_grids = pd.DataFrame()

common_grids = solar_grids & wind_grids & hydro_grids
print(f"\n✓ Common grids: {len(common_grids)}")


# ============================================================================
# Add Parameters Using FUZZY MATCHING
# ============================================================================

print("\n" + "="*70)
print("ADDING PARAMETERS TO STATION FILES (FUZZY MATCHING)")
print("="*70)

def add_params_fuzzy(row):
    """Add parameters using fuzzy name matching"""
    return pd.Series(get_station_parameters(row['station_name']))

# Test fuzzy matching first
print("\nTesting fuzzy matching on station names...")
test_stations = station_mapping['station_name'].head(50)
major_found = []
for name in test_stations:
    params = get_station_parameters(name)
    if params['parameter_type'] == 'Full Meteorological':
        major_found.append((name, params['matched_major_station']))

if major_found:
    print(f"\n✓ Found {len(major_found)} major met stations in sample:")
    for actual_name, matched_name in major_found[:10]:
        print(f"  • {actual_name} → matched as {matched_name}")
else:
    print("\n⚠ No major stations found in first 50 records")

# Common stations
common_stations = station_mapping[station_mapping['grid_id'].isin(common_grids)].copy()

if len(common_stations) > 0:
    common_stations = common_stations.merge(
        solar_filtered[['grid_id', 'real_ghi', 'solar_rating']], 
        on='grid_id', how='left'
    )
    common_stations = common_stations.merge(
        wind_filtered[['grid_id', 'wind_speed_100m', 'wind_rating']], 
        on='grid_id', how='left'
    )

    if len(hydro_with_grids) > 0:
        hydro_counts = hydro_with_grids.groupby('grid_id').size().reset_index(name='hydro_plant_count')
        common_stations = common_stations.merge(hydro_counts, on='grid_id', how='left')

    # Add parameters using fuzzy matching
    param_info = common_stations.apply(add_params_fuzzy, axis=1)
    common_stations = pd.concat([common_stations, param_info], axis=1)

    print(f"\n✓ Common stations: {len(common_stations)}")
    full_met_count = len(common_stations[common_stations['parameter_type']=='Full Meteorological'])
    rainfall_count = len(common_stations[common_stations['parameter_type']=='Rainfall Only'])
    print(f"  - Full meteorological: {full_met_count}")
    print(f"  - Rainfall only: {rainfall_count}")

    # Show major met stations found in common zones
    major_in_common = common_stations[common_stations['parameter_type']=='Full Meteorological']
    if len(major_in_common) > 0:
        print(f"\n  🌟 Major met stations in common resource zones:")
        for _, row in major_in_common.iterrows():
            print(f"    • {row['station_name']} → {row['matched_major_station']}")
            print(f"      District: {row['district']}, Solar: {row['solar_rating']}, Wind: {row['wind_rating']}")
    else:
        print("\n  ⚠ No major met stations in common resource zones")


# ============================================================================
# Save Results
# ============================================================================

print("\n" + "="*70)
print("SAVING RESULTS")
print("="*70)

output_dir = Path("data/bronze/metadata")
output_dir.mkdir(parents=True, exist_ok=True)

# Common stations
if len(common_stations) > 0:
    out_file = output_dir / "common_resource_weather_stations_with_parameters.csv"
    common_stations.to_csv(out_file, index=False)
    print(f"✓ {out_file} ({len(common_stations)} rows)")

# Individual resources
for name, grids in [('solar', solar_grids), ('wind', wind_grids), ('hydro', hydro_grids)]:
    df = station_mapping[station_mapping['grid_id'].isin(grids)].copy()
    if len(df) > 0:
        param_info = df.apply(add_params_fuzzy, axis=1)
        df = pd.concat([df, param_info], axis=1)
        out_file = output_dir / f"{name}_resource_weather_stations_with_parameters.csv"
        df.to_csv(out_file, index=False)

        full_met = len(df[df['parameter_type']=='Full Meteorological'])
        print(f"✓ {out_file}")
        print(f"  {len(df)} total, {full_met} with full meteorological parameters")

print("\n" + "="*70)
print("✓ COMPLETE!")
print("="*70)

# Final summary
all_stations = station_mapping.copy()
all_params = all_stations.apply(add_params_fuzzy, axis=1)
all_stations = pd.concat([all_stations, all_params], axis=1)
total_major = len(all_stations[all_stations['parameter_type']=='Full Meteorological'])

print(f"""
Summary:
--------
Total weather stations: {len(station_mapping)}
Major met stations found (fuzzy matching): {total_major}
Common grids (all 3 resources): {len(common_grids)}

Fuzzy matching examples:
  "COLOMBO-FORT (S.G.O)" → matched as COLOMBO
  "NUWARA ELIYA(LOVERS LP)" → matched as NUWARA ELIYA
  "ANURADHAPURA-MET 19B" → matched as ANURADHAPURA

Files created:
  ✓ common_resource_weather_stations_with_parameters.csv
  ✓ solar_resource_weather_stations_with_parameters.csv
  ✓ wind_resource_weather_stations_with_parameters.csv
  ✓ hydro_resource_weather_stations_with_parameters.csv

New columns:
  - parameters_available: Full list of parameters
  - parameter_type: "Full Meteorological" (8 params) or "Rainfall Only" (1 param)
  - observation_frequency: "3-hourly" or "Daily/Monthly"
  - num_parameters: 1-8
  - matched_major_station: Name of the 24 major stations (if matched)
""")