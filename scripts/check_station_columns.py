"""
Check actual column names in weather station CSV files
"""
import pandas as pd

print("="*70)
print("CHECKING WEATHER STATION CSV COLUMN NAMES")
print("="*70)

# Check solar_resource_weather_stations.csv
print("\n1. solar_resource_weather_stations.csv")
try:
    df = pd.read_csv("data/bronze/metadata/solar_resource_weather_stations.csv")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Sample row:")
    print(df.head(1).to_string())
except Exception as e:
    print(f"   Error: {e}")

# Check rainfall stations
print("\n2. Rainfall stations CSV")
try:
    df = pd.read_csv("data/raw/stations/Copy of Met Stations Rainfall stations all from the begining.xlsx.csv",
                     on_bad_lines='skip')
    print(f"   Columns: {list(df.columns)}")
    print(f"   Sample row:")
    print(df.head(1).to_string())
except Exception as e:
    print(f"   Error: {e}")

# Check major Met stations
print("\n3. Major Met Stations CSV")
try:
    df = pd.read_csv("data/raw/stations/Copy of Met Stations Met Stations & Parameters.xlsx.csv",
                     on_bad_lines='skip')
    print(f"   Columns: {list(df.columns)}")
    print(f"   Sample row:")
    print(df.head(1).to_string())
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*70)
