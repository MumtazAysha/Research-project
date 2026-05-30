import os

print("🔍 CHECKING ALL 24 MAIN STATIONS:")
print("="*80)

# Get ALL main stations from your 2019 folder
folder_2019 = 'data/silver/openmeteo/year_2019/3hourly'
all_files = os.listdir(folder_2019)

# Extract station IDs from filenames
main_stations = []
for file in all_files:
    if file.endswith('_3hourly.csv'):
        station_id = file.replace('station_', '').split('_')[0]
        main_stations.append(station_id)

main_stations = sorted(set(main_stations))
print(f"📊 Found {len(main_stations)} main stations in 2019\n")

# Check each station's coverage
complete = []
incomplete = []

for station in main_stations:
    years_found = []
    for year in range(2019, 2026):
        hourly_path = f'data/silver/openmeteo/year_{year}/3hourly/station_{station}_{year}_3hourly.csv'
        if os.path.exists(hourly_path):
            years_found.append(year)
    
    if len(years_found) == 7:
        complete.append(station)
        print(f"✅ {station:8} - COMPLETE (7 years)")
    else:
        incomplete.append(station)
        print(f"⚠️  {station:8} - INCOMPLETE ({len(years_found)} years): {years_found}")

print(f"\n" + "="*80)
print(f"📊 SUMMARY:")
print(f"   Total main stations: {len(main_stations)}")
print(f"   Complete (7 years): {len(complete)}")
print(f"   Incomplete: {len(incomplete)}")

if incomplete:
    print(f"\n⚠️  INCOMPLETE STATIONS: {incomplete}")
