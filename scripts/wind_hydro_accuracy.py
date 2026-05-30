"""
Check accuracy of wind and hydro resource station files
"""
import pandas as pd

print("="*70)
print("CHECKING WIND & HYDRO RESOURCE STATION FILES")
print("="*70)

# Load all three resource station files
solar_stations = pd.read_csv("data/bronze/metadata/solar_resource_weather_stations.csv")
wind_stations = pd.read_csv("data/bronze/metadata/wind_resource_weather_stations.csv")
hydro_stations = pd.read_csv("data/bronze/metadata/hydro_resource_weather_stations.csv")

print("\n1. SOLAR RESOURCE STATIONS")
print(f"   Total: {len(solar_stations)}")
print(f"   Unique stations: {solar_stations['station_id'].nunique()}")
print(f"   Sample IDs: {list(solar_stations['station_id'].head(3))}")

print("\n2. WIND RESOURCE STATIONS")
print(f"   Total: {len(wind_stations)}")
print(f"   Unique stations: {wind_stations['station_id'].nunique()}")
print(f"   Sample IDs: {list(wind_stations['station_id'].head(3))}")

print("\n3. HYDRO RESOURCE STATIONS")
print(f"   Total: {len(hydro_stations)}")
print(f"   Unique stations: {hydro_stations['station_id'].nunique()}")
print(f"   Sample IDs: {list(hydro_stations['station_id'].head(3))}")

# Load original rainfall stations for verification
rainfall = pd.read_csv("data/raw/stations/Copy of Met Stations Rainfall stations all from the begining.xlsx.csv",
                       on_bad_lines='skip')
rainfall_ids = set(rainfall['id'].unique())

print("\n" + "="*70)
print("VERIFICATION AGAINST RAINFALL STATIONS FILE")
print("="*70)

# Check each file
for name, df in [("Solar", solar_stations), ("Wind", wind_stations), ("Hydro", hydro_stations)]:
    station_ids = set(df['station_id'].unique())
    match_count = len(station_ids & rainfall_ids)
    match_pct = (match_count / len(station_ids)) * 100
    
    print(f"\n{name} Resource Stations:")
    print(f"   Station IDs in file: {len(station_ids)}")
    print(f"   Match with rainfall file: {match_count} ({match_pct:.1f}%)")
    
    if match_count < len(station_ids):
        missing = station_ids - rainfall_ids
        print(f"   ⚠️ Missing from rainfall file: {len(missing)} stations")
        print(f"   Sample missing IDs: {list(missing)[:5]}")

# Check if all three files use the same column structure
print("\n" + "="*70)
print("COLUMN STRUCTURE CHECK")
print("="*70)

print(f"\nSolar columns: {list(solar_stations.columns)}")
print(f"Wind columns: {list(wind_stations.columns)}")
print(f"Hydro columns: {list(hydro_stations.columns)}")

# Show sample data from each
print("\n" + "="*70)
print("SAMPLE DATA FROM EACH FILE")
print("="*70)

print("\nSolar (first 3):")
print(solar_stations[['station_id', 'station_name', 'district', 'grid_id']].head(3))

print("\nWind (first 3):")
print(wind_stations[['station_id', 'station_name', 'district', 'grid_id']].head(3))

print("\nHydro (first 3):")
print(hydro_stations[['station_id', 'station_name', 'district', 'grid_id']].head(3))

print("\n" + "="*70)
print("✓ VERIFICATION COMPLETE")
print("="*70)

