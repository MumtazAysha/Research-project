import pandas as pd
import os

print("="*70)
print("🔍 VERIFYING: Did we keep at least ONE from each duplicate group?")
print("="*70)

# 1. Load ORIGINAL Excel - CORRECT PATH
excel_path = 'data/bronze/weather_data/Met data weather stations(AutoRecovered).xlsx'

print(f"\n📂 Loading original Excel from: {excel_path}")
excel = pd.read_excel(excel_path, header=1)
excel = excel[['Station ID', 'Station Name', 'Latitude', 'Longitude']]
excel = excel.dropna(subset=['Latitude', 'Longitude'])
excel.columns = ['Station_ID', 'Station_Name', 'Latitude', 'Longitude']
print(f"   Original stations: {len(excel)}")

# 2. Load FINAL station list (949 stations)
print("\n📂 Loading final station list...")
final = pd.read_csv('data/silver/openmeteo/station_parsing_full_list.csv')
print(f"   Final stations: {len(final)}")

# 3. Find all duplicate coordinate groups in ORIGINAL
print("\n🔍 Finding duplicate coordinate groups in original Excel...")
duplicates = excel[excel.duplicated(subset=['Latitude', 'Longitude'], keep=False)]
duplicate_groups = duplicates.groupby(['Latitude', 'Longitude'])

print(f"   Found {len(duplicate_groups)} duplicate coordinate groups")

# 4. Check if at least ONE from each group exists in final list
print("\n" + "="*70)
print("📊 CHECKING EACH DUPLICATE GROUP:")
print("="*70)

all_good = True
kept_count = 0
missing_count = 0

for (lat, lon), group in duplicate_groups:
    # Find how many from this group exist in final list
    kept = final[(final['Latitude'] == lat) & (final['Longitude'] == lon)]
    
    if len(kept) >= 1:
        print(f"\n✅ ({lat}, {lon}): KEPT {len(kept)} station(s)")
        print(f"   Original had: {len(group)} stations")
        for _, station in kept.iterrows():
            print(f"   → Kept: {station['Station_ID']} - {station['Station_Name']}")
        kept_count += 1
    else:
        print(f"\n❌ ({lat}, {lon}): ERROR - NO stations kept!")
        print(f"   Original had: {len(group)} stations:")
        for _, station in group.iterrows():
            print(f"   → Lost: {station['Station_ID']} - {station['Station_Name']}")
        all_good = False
        missing_count += 1

# 5. Summary
print("\n" + "="*70)
print("📈 SUMMARY:")
print("="*70)
print(f"   Duplicate groups found: {len(duplicate_groups)}")
print(f"   Groups with ≥1 station kept: {kept_count}")
print(f"   Groups with NO stations kept: {missing_count}")

if all_good:
    print("\n✅ SUCCESS: Every duplicate group has at least ONE station kept!")
else:
    print(f"\n⚠️  WARNING: {missing_count} groups lost ALL their stations!")

print("="*70)
