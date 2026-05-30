import os
import pandas as pd

print("="*70)
print("🔍 DETAILED CHECK (FIXED): Did we keep one from each duplicate?")
print("="*70)

# 1. Get downloaded station IDs - EXTRACT from filename format
folder = 'data/silver/openmeteo/year_2019/daily'
csv_files = [f for f in os.listdir(folder) if f.endswith('.csv')]

# Extract station ID from format: station_01RT0196_2019_daily.csv
downloaded_ids = set()
for f in csv_files:
    # Remove .csv, remove 'station_', remove '_2019_daily'
    clean_id = f.replace('.csv', '').replace('station_', '').replace('_2019_daily', '')
    downloaded_ids.add(clean_id)

print(f"\n📊 Downloaded CSV files: {len(csv_files)}")
print(f"   Sample cleaned IDs: {list(downloaded_ids)[:5]}")

# 2. Load original Excel
excel = pd.read_excel('data/bronze/weather_data/Met data weather stations(AutoRecovered).xlsx', header=1)
excel = excel[['Station ID', 'Station Name', 'Latitude', 'Longitude']]
excel = excel.dropna(subset=['Latitude', 'Longitude'])
excel.columns = ['Station_ID', 'Station_Name', 'Latitude', 'Longitude']
excel['Station_ID'] = excel['Station_ID'].astype(str).str.strip()

print(f"\n📊 Excel stations: {len(excel)}")
print(f"   Sample Excel IDs: {list(excel['Station_ID'].head())}")

# 3. Find duplicate groups
duplicates = excel[excel.duplicated(subset=['Latitude', 'Longitude'], keep=False)]
duplicate_groups = duplicates.groupby(['Latitude', 'Longitude'])

print(f"\n🔍 Duplicate groups in Excel: {len(duplicate_groups)}")

# 4. Check each duplicate group
print("\n" + "="*70)
print("📊 CHECKING EACH DUPLICATE GROUP:")
print("="*70)

kept_one = 0
kept_all = 0
kept_none = 0

for (lat, lon), group in duplicate_groups:
    group_ids = set(group['Station_ID'].astype(str).str.strip())
    downloaded_from_group = group_ids.intersection(downloaded_ids)
    
    if len(downloaded_from_group) == 1:
        print(f"\n✅ ({lat}, {lon}): KEPT 1, REMOVED {len(group)-1}")
        station_name = group[group['Station_ID'].isin(downloaded_from_group)]['Station_Name'].iloc[0]
        print(f"   → Kept: {list(downloaded_from_group)[0]} - {station_name}")
        kept_one += 1
    elif len(downloaded_from_group) == len(group):
        print(f"\n⚠️  ({lat}, {lon}): KEPT ALL {len(group)} (no dedup!)")
        for sid in downloaded_from_group:
            print(f"   → Downloaded: {sid}")
        kept_all += 1
    elif len(downloaded_from_group) == 0:
        print(f"\n❌ ({lat}, {lon}): REMOVED ALL {len(group)}")
        kept_none += 1
    else:
        print(f"\n⚠️  ({lat}, {lon}): KEPT {len(downloaded_from_group)} of {len(group)}")

# 5. Summary
print("\n" + "="*70)
print("📈 FINAL ANSWER:")
print("="*70)
print(f"   Duplicate groups that kept 1 station: {kept_one}")
print(f"   Duplicate groups that kept ALL: {kept_all}")
print(f"   Duplicate groups that removed ALL: {kept_none}")
print(f"   Total duplicate groups: {len(duplicate_groups)}")

if kept_one == len(duplicate_groups):
    print("\n✅✅✅ PERFECT! ✅✅✅")
    print("   You kept ONE from each duplicate and removed the rest!")
    print("   This is EXACTLY what you should do!")
elif kept_all > 0:
    print(f"\n⚠️  WARNING: {kept_all} groups still have all duplicates!")
elif kept_none > 0:
    print(f"\n❌ PROBLEM: {kept_none} groups removed ALL entries (both deleted!)")
    print("   You should keep one from each pair, not delete both.")

print("="*70)