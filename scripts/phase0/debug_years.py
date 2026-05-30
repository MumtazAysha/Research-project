import os

station = "43476"

print("🔍 CHECKING ALL YEARS FOR STATION 43476:")
print("="*80)

for year in range(2019, 2026):
    hourly_path = f'data/silver/openmeteo/year_{year}/3hourly/station_{station}_{year}_3hourly.csv'
    
    print(f"\n{year}:")
    print(f"  Looking for: {hourly_path}")
    
    if os.path.exists(hourly_path):
        print(f"  ✅ FILE EXISTS!")
        # Get file size to confirm it's not empty
        size = os.path.getsize(hourly_path)
        print(f"  File size: {size:,} bytes")
    else:
        print(f"  ❌ NOT FOUND")
        
        # Check if the FOLDER exists
        folder = f'data/silver/openmeteo/year_{year}/3hourly'
        if os.path.exists(folder):
            print(f"  📂 Folder exists, checking what's inside...")
            files = [f for f in os.listdir(folder) if station in f]
            if files:
                print(f"  Found: {files}")
            else:
                print(f"  No files with {station} in name")
        else:
            print(f"  📂 Folder doesn't exist: {folder}")

print("\n" + "="*80)
