import os
import pandas as pd

print("="*70)
print("🔍 CHECKING YOUR DOWNLOADED DATA")
print("="*70)

# 1. Count CSV files
folder = 'data/silver/openmeteo/year_2019/daily'
csv_files = [f for f in os.listdir(folder) if f.endswith('.csv')]
print(f"\n📊 Downloaded CSV files: {len(csv_files)}")

# 2. Load station list
station_list = pd.read_csv('data/silver/openmeteo/station_parsing_full_list.csv')
print(f"📊 Station list (full): {len(station_list)}")

# 3. Get station IDs from filenames
downloaded_ids = set([f.replace('.csv', '') for f in csv_files])

# 4. Match with station list
downloaded_stations = station_list[station_list['Station_ID'].astype(str).isin(downloaded_ids)]
print(f"📊 Matched stations: {len(downloaded_stations)}")

# 5. Check for duplicate coordinates in DOWNLOADED stations
duplicates = downloaded_stations[downloaded_stations.duplicated(subset=['Latitude', 'Longitude'], keep=False)]

print("\n" + "="*70)
print("📈 RESULT:")
print("="*70)

if len(duplicates) == 0:
    print("\n✅✅✅ SUCCESS! ✅✅✅")
    print(f"\n   You have {len(csv_files)} CSV files")
    print("   NO duplicate coordinates found!")
    print("   Your downloads are properly deduplicated! 🎉")
else:
    print(f"\n❌ Found {len(duplicates)} stations with duplicate coordinates:")
    dup_groups = duplicates.groupby(['Latitude', 'Longitude']).size()
    print(f"   Number of duplicate location pairs: {len(dup_groups)}")

print("="*70)
