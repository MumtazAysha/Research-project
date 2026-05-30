"""
Find common weather locations across high-quality resource zones
(Solar: Moderate-Excellent, Wind: Moderate-Excellent, Hydro: Has plants)

Output: Weather stations in the intersection of all three resource types
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path

# ============================================================================
# STEP 1: Load All Data
# ============================================================================

print("="*70)
print("FINDING COMMON WEATHER LOCATIONS IN MULTI-RESOURCE ZONES")
print("="*70)

# Grid cells with geometry
grid_gdf = gpd.read_file("data/bronze/metadata/grid_cells_all.geojson")
print(f"\n✓ Loaded {len(grid_gdf)} grid cells")

# Weather station to grid mapping
station_mapping = pd.read_csv("data/bronze/metadata/grid_weather_station_mapping.csv")
print(f"✓ Loaded {len(station_mapping)} weather station-grid mappings")

# Solar resource data
solar_data = pd.read_csv("data/bronze/metadata/grid_with_real_solar_data.csv")
print(f"✓ Loaded solar resource data for {len(solar_data)} grids")

# Wind resource data
wind_data = pd.read_csv("data/bronze/metadata/grid_with_wind_data.csv")
print(f"✓ Loaded wind resource data for {len(wind_data)} grids")

# Hydro power plants - try multiple possible locations
possible_hydro_paths = [
    "Hydro power plants.xlsx",
    "Hydro-power-plants-1.xlsx",
    "data/raw/Hydro power plants.xlsx",
    "data/raw/stations/Hydro power plants.xlsx",
]

hydro_plants = None
hydro_plants_path = None
for path in possible_hydro_paths:
    if Path(path).exists():
        print(f"✓ Found hydro plants file: {path}")
        hydro_plants_path = path
        hydro_plants = pd.read_excel(path)
        break

if hydro_plants is None:
    print("ERROR: Could not find Hydro power plants Excel file!")
    print("Searched in:", possible_hydro_paths)
    exit(1)

print(f"✓ Loaded {len(hydro_plants)} hydroelectric plants")

# ============================================================================
# STEP 2: Filter Solar Grids (Moderate to Excellent)
# ============================================================================

print("\n" + "="*70)
print("FILTERING SOLAR RESOURCE GRIDS")
print("="*70)

# Solar ratings: Excellent, Very Good, Good, Moderate, Low, Very Low
solar_good_ratings = ['Excellent', 'Very Good', 'Good', 'Moderate']

solar_filtered = solar_data[solar_data['solar_rating'].isin(solar_good_ratings)].copy()

print(f"\nSolar resource grids (Moderate to Excellent):")
print(f"  Total grids: {len(solar_filtered)}")
print(f"\n  Breakdown by rating:")
for rating in solar_good_ratings:
    count = len(solar_filtered[solar_filtered['solar_rating'] == rating])
    print(f"    {rating}: {count} grids")

solar_grid_ids = set(solar_filtered['grid_id'].unique())
print(f"\n✓ Selected {len(solar_grid_ids)} solar resource grids")

# ============================================================================
# STEP 3: Filter Wind Grids (Moderate to Excellent)
# ============================================================================

print("\n" + "="*70)
print("FILTERING WIND RESOURCE GRIDS")
print("="*70)

# Wind ratings: Excellent, Very Good, Good, Moderate, Fair, Poor
wind_good_ratings = ['Excellent', 'Very Good', 'Good', 'Moderate']

wind_filtered = wind_data[
    wind_data['wind_rating'].isin(wind_good_ratings) & 
    wind_data['wind_speed_100m'].notna()
].copy()

print(f"\nWind resource grids (Moderate to Excellent):")
print(f"  Total grids: {len(wind_filtered)}")
print(f"\n  Breakdown by rating:")
for rating in wind_good_ratings:
    count = len(wind_filtered[wind_filtered['wind_rating'] == rating])
    print(f"    {rating}: {count} grids")

wind_grid_ids = set(wind_filtered['grid_id'].unique())
print(f"\n✓ Selected {len(wind_grid_ids)} wind resource grids")

# ============================================================================
# STEP 4: Filter Hydro Grids (Has Power Plants)
# ============================================================================

print("\n" + "="*70)
print("FILTERING HYDRO RESOURCE GRIDS")
print("="*70)

# Read Excel file with header detection
# The headers are NOT in row 0, they're in row 2 (after "Major Hydro Power Plants" title)
try:
    # First, read to see structure
    df_test = pd.read_excel(hydro_plants_path, nrows=5)
    print(f"\nFirst few rows (raw):")
    print(df_test)
    
    # Try reading with different header rows
    for header_row in [0, 1, 2, 3]:
        try:
            df = pd.read_excel(hydro_plants_path, header=header_row)
            # Check if we found proper columns
            cols_lower = [str(c).lower() for c in df.columns]
            if any('name' in c for c in cols_lower) and any('capacity' in c for c in cols_lower):
                print(f"\n✓ Found headers at row {header_row}")
                print(f"  Columns: {list(df.columns)}")
                hydro_plants = df
                break
        except:
            continue
    
    # If still no good columns, try skipping rows
    if not any('name' in str(c).lower() for c in hydro_plants.columns):
        print("\nTrying with skiprows...")
        hydro_plants = pd.read_excel(hydro_plants_path, skiprows=2)
        print(f"Columns after skipping rows: {list(hydro_plants.columns)}")
        
except Exception as e:
    print(f"Error: {e}")
    exit(1)

# Now standardize column names - be very flexible
hydro_plants.columns = hydro_plants.columns.astype(str)

# Manual column mapping based on position if needed
if len(hydro_plants.columns) >= 3:
    # Assume: Column 0 = Name, Column 1 = Capacity, Column 2 = Coordinates
    new_cols = {}
    for i, col in enumerate(hydro_plants.columns):
        col_lower = str(col).lower()
        if i == 0 or 'name' in col_lower:
            new_cols[col] = 'Name'
        elif i == 1 or 'capacity' in col_lower or 'mw' in col_lower:
            new_cols[col] = 'Capacity'
        elif i == 2 or 'coord' in col_lower:
            new_cols[col] = 'Coordinates'
    
    hydro_plants = hydro_plants.rename(columns=new_cols)
    print(f"\nMapped columns: {list(hydro_plants.columns)}")

# If we still don't have the right columns, try positional approach
if 'Coordinates' not in hydro_plants.columns and len(hydro_plants.columns) >= 3:
    print("\nUsing positional column mapping...")
    cols_list = list(hydro_plants.columns)
    hydro_plants = hydro_plants.rename(columns={
        cols_list[0]: 'Name',
        cols_list[1]: 'Capacity', 
        cols_list[2]: 'Coordinates'
    })
    print(f"Renamed to: {list(hydro_plants.columns)}")

# Parse coordinates from "lat, lon" format
def parse_coordinates(coord_str):
    """Parse 'lat, lon' string into separate values"""
    try:
        coord_str = str(coord_str).strip()
        if coord_str == 'nan' or coord_str == '':
            return pd.Series({'Latitude': None, 'Longitude': None})
        
        # Handle both comma and space separators
        if ',' in coord_str:
            parts = coord_str.split(',')
        else:
            parts = coord_str.split()
        
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        return pd.Series({'Latitude': lat, 'Longitude': lon})
    except Exception as e:
        return pd.Series({'Latitude': None, 'Longitude': None})

# Apply the parsing
if 'Coordinates' in hydro_plants.columns:
    print(f"\nParsing coordinates...")
    hydro_plants[['Latitude', 'Longitude']] = hydro_plants['Coordinates'].apply(parse_coordinates)
else:
    print(f"\nERROR: Still cannot find 'Coordinates' column!")
    print(f"Final columns: {list(hydro_plants.columns)}")
    print(f"\nFirst few rows:")
    print(hydro_plants.head())
    exit(1)

# Remove rows with invalid coordinates
initial_count = len(hydro_plants)
hydro_plants = hydro_plants.dropna(subset=['Latitude', 'Longitude'])
print(f"Parsed coordinates: {len(hydro_plants)}/{initial_count} plants")
if initial_count > len(hydro_plants):
    print(f"  (removed {initial_count - len(hydro_plants)} plants with invalid coordinates)")

# Remove header rows that might have been included
hydro_plants = hydro_plants[hydro_plants['Latitude'].notna()]
hydro_plants = hydro_plants[pd.to_numeric(hydro_plants['Latitude'], errors='coerce').notna()]

print(f"After cleaning: {len(hydro_plants)} valid plants")

# Convert hydro plants to GeoDataFrame
hydro_plants['geometry'] = gpd.points_from_xy(
    hydro_plants['Longitude'], 
    hydro_plants['Latitude']
)
hydro_gdf = gpd.GeoDataFrame(hydro_plants, geometry='geometry', crs='EPSG:4326')

# Spatial join: which grid contains each hydro plant
hydro_with_grids = gpd.sjoin(
    hydro_gdf,
    grid_gdf[['grid_id', 'geometry']],
    how='inner',
    predicate='within'
)

print(f"\nHydro resource grids (with power plants):")
print(f"  Total plants mapped to grids: {len(hydro_with_grids)}")

# Check if Capacity column exists for breakdown
if 'Capacity' in hydro_with_grids.columns:
    # Convert to numeric
    hydro_with_grids['Capacity'] = pd.to_numeric(hydro_with_grids['Capacity'], errors='coerce')
    print(f"  By capacity:")
    major_count = len(hydro_with_grids[hydro_with_grids['Capacity'] > 10])
    mini_count = len(hydro_with_grids[hydro_with_grids['Capacity'] <= 10])
    print(f"    >10 MW (Major): {major_count}")
    print(f"    ≤10 MW (Mini): {mini_count}")

hydro_grid_ids = set(hydro_with_grids['grid_id'].unique())
print(f"\n✓ Selected {len(hydro_grid_ids)} hydro resource grids")

# ============================================================================
# STEP 5: Find Common Grids (Intersection)
# ============================================================================

print("\n" + "="*70)
print("FINDING COMMON GRIDS ACROSS ALL THREE RESOURCES")
print("="*70)

# Intersection of all three
common_grids = solar_grid_ids & wind_grid_ids & hydro_grid_ids

print(f"\nGrid intersection analysis:")
print(f"  Solar grids (Moderate-Excellent): {len(solar_grid_ids)}")
print(f"  Wind grids (Moderate-Excellent): {len(wind_grid_ids)}")
print(f"  Hydro grids (with plants): {len(hydro_grid_ids)}")
print(f"\n  Pairwise intersections:")
print(f"    Solar ∩ Wind: {len(solar_grid_ids & wind_grid_ids)}")
print(f"    Solar ∩ Hydro: {len(solar_grid_ids & hydro_grid_ids)}")
print(f"    Wind ∩ Hydro: {len(wind_grid_ids & hydro_grid_ids)}")
print(f"\n  ✓ Solar ∩ Wind ∩ Hydro (ALL THREE): {len(common_grids)} grids")

# ============================================================================
# STEP 6: Extract Weather Stations in Common Grids
# ============================================================================

print("\n" + "="*70)
print("EXTRACTING WEATHER STATIONS IN COMMON GRIDS")
print("="*70)

# Filter station mapping to only common grids
common_stations = station_mapping[
    station_mapping['grid_id'].isin(common_grids)
].copy()

print(f"\nWeather stations in common resource zones:")
print(f"  Total station-grid mappings: {len(common_stations)}")
print(f"  Unique stations: {common_stations['station_id'].nunique()}")
print(f"  Across {len(common_grids)} grid cells")

# Add resource information
common_stations = common_stations.merge(
    solar_filtered[['grid_id', 'real_ghi', 'solar_rating']],
    on='grid_id',
    how='left'
)

common_stations = common_stations.merge(
    wind_filtered[['grid_id', 'wind_speed_100m', 'wind_rating']],
    on='grid_id',
    how='left'
)

# Count hydro plants per grid
hydro_counts = hydro_with_grids.groupby('grid_id').size().reset_index(name='hydro_plant_count')
common_stations = common_stations.merge(
    hydro_counts,
    on='grid_id',
    how='left'
)

# ============================================================================
# STEP 7: Save Results
# ============================================================================

print("\n" + "="*70)
print("SAVING RESULTS")
print("="*70)

output_dir = Path("data/bronze/metadata")
output_dir.mkdir(parents=True, exist_ok=True)

# 1. Common weather stations (detailed)
common_stations_file = output_dir / "common_resource_weather_stations.csv"
common_stations.to_csv(common_stations_file, index=False)
print(f"\n✓ Saved: {common_stations_file}")
print(f"  Rows: {len(common_stations)}")
print(f"  Columns: {list(common_stations.columns)}")

# 2. Common grid IDs (simple list)
common_grids_file = output_dir / "common_resource_grids.csv"
pd.DataFrame({
    'grid_id': list(common_grids)
}).to_csv(common_grids_file, index=False)
print(f"\n✓ Saved: {common_grids_file}")

# 3. Summary by grid
summary_by_grid = common_stations.groupby('grid_id').agg({
    'station_id': 'count',
    'solar_rating': 'first',
    'wind_rating': 'first',
    'real_ghi': 'first',
    'wind_speed_100m': 'first',
    'hydro_plant_count': 'first'
}).rename(columns={'station_id': 'num_weather_stations'})

summary_file = output_dir / "common_resource_grid_summary.csv"
summary_by_grid.to_csv(summary_file)
print(f"\n✓ Saved: {summary_file}")

# ============================================================================
# STEP 8: Create Separate Files for Each Resource Type
# ============================================================================

print("\n" + "="*70)
print("CREATING INDIVIDUAL RESOURCE FILES")
print("="*70)

# Solar-only stations
solar_only_stations = station_mapping[
    station_mapping['grid_id'].isin(solar_grid_ids)
].copy()
solar_file = output_dir / "solar_resource_weather_stations.csv"
solar_only_stations.to_csv(solar_file, index=False)
print(f"\n✓ Solar resource stations: {len(solar_only_stations)} → {solar_file}")

# Wind-only stations
wind_only_stations = station_mapping[
    station_mapping['grid_id'].isin(wind_grid_ids)
].copy()
wind_file = output_dir / "wind_resource_weather_stations.csv"
wind_only_stations.to_csv(wind_file, index=False)
print(f"✓ Wind resource stations: {len(wind_only_stations)} → {wind_file}")

# Hydro-only stations
hydro_only_stations = station_mapping[
    station_mapping['grid_id'].isin(hydro_grid_ids)
].copy()
hydro_file = output_dir / "hydro_resource_weather_stations.csv"
hydro_only_stations.to_csv(hydro_file, index=False)
print(f"✓ Hydro resource stations: {len(hydro_only_stations)} → {hydro_file}")

# ============================================================================
# STEP 9: Display Sample Results
# ============================================================================

print("\n" + "="*70)
print("SAMPLE RESULTS - COMMON RESOURCE ZONES")
print("="*70)

if len(summary_by_grid) > 0:
    print("\nTop 10 grids by number of weather stations:")
    top_grids = summary_by_grid.nlargest(10, 'num_weather_stations')
    print(top_grids.to_string())
    
    print("\n\nSample weather stations in common zones:")
    display_cols = ['grid_id', 'station_id', 'station_name', 'lat', 'lon', 
                    'solar_rating', 'wind_rating', 'hydro_plant_count']
    # Only show columns that exist
    display_cols = [c for c in display_cols if c in common_stations.columns]
    print(common_stations[display_cols].head(15).to_string(index=False))
else:
    print("\nNo common grids found with all three resources!")
    print("This means no single grid has Moderate-Excellent solar AND wind AND hydro plants.")

# ============================================================================
# DONE
# ============================================================================

print("\n" + "="*70)
print("✓ ANALYSIS COMPLETE!")
print("="*70)

print(f"""
Summary of Results:
-------------------
1. Common grids (all 3 resources): {len(common_grids)}
2. Weather stations in common zones: {common_stations['station_id'].nunique() if len(common_stations) > 0 else 0}
3. Solar resource grids (Moderate-Excellent): {len(solar_grid_ids)}
4. Wind resource grids (Moderate-Excellent): {len(wind_grid_ids)}
5. Hydro resource grids (with plants): {len(hydro_grid_ids)}
""")


