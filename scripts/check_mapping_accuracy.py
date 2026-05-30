"""
Check the station mapping file used for grid intersection
"""
import pandas as pd

print("="*70)
print("CHECKING GRID-STATION MAPPING FILE")
print("="*70)

# This is the file used for finding stations in grids
mapping = pd.read_csv("data/bronze/metadata/grid_weather_station_mapping.csv")

print(f"\nColumns: {list(mapping.columns)}")
print(f"Total mappings: {len(mapping)}")
print(f"Unique stations: {mapping['station_id'].nunique()}")

print("\nSample rows:")
print(mapping.head(10))

print("\n" + "="*70)
print("Checking if these station IDs match rainfall stations...")

# Load rainfall stations
rainfall = pd.read_csv("data/raw/stations/Copy of Met Stations Rainfall stations all from the begining.xlsx.csv",
                       on_bad_lines='skip')
print(f"\nRainfall stations file has:")
print(f"  Columns: {list(rainfall.columns)}")
print(f"  Total stations: {len(rainfall)}")

# Check overlap
mapping_ids = set(mapping['station_id'].unique())
rainfall_ids = set(rainfall['id'].unique())

overlap = mapping_ids & rainfall_ids
print(f"\nStation ID overlap:")
print(f"  In mapping file: {len(mapping_ids)} unique IDs")
print(f"  In rainfall file: {len(rainfall_ids)} unique IDs")
print(f"  Match: {len(overlap)} stations ({len(overlap)/len(mapping_ids)*100:.1f}%)")

if len(overlap) < len(mapping_ids):
    print(f"\n⚠️ WARNING: {len(mapping_ids) - len(overlap)} stations in mapping NOT in rainfall file!")
    print("Sample missing IDs:", list(mapping_ids - rainfall_ids)[:5])
