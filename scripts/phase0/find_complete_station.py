import os

# These are the 24 main stations that should have 3-hourly data
main_stations = ["43404", "43410", "43413", "43415", "43418", "43421", "43424", 
                 "43436", "43441", "43444", "43450", "43466", "43467", "43473",
                 "43479", "43486", "43495", "43497", "43MAT", "43MMM", "43PPP"]

print("🔍 CHECKING WHICH STATIONS HAVE COMPLETE 2019-2025 DATA:")
print("="*80)

for station in main_stations:
    years_found = []
    for year in range(2019, 2026):
        hourly_path = f'data/silver/openmeteo/year_{year}/3hourly/station_{station}_{year}_3hourly.csv'
        if os.path.exists(hourly_path):
            years_found.append(year)
    
    if len(years_found) >= 5:  # At least 5 years
        print(f"✅ {station:8} - {len(years_found)} years: {years_found}")
    elif len(years_found) > 0:
        print(f"⚠️  {station:8} - {len(years_found)} years: {years_found}")

print("\n💡 Pick a station with ✅ to continue!")
