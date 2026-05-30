import pandas as pd

print("="*70)
print("DIAGNOSTIC: Checking for Major Met Stations")
print("="*70)

# The 24 major met stations we're looking for
MAJOR_STATIONS = [
    'BANDARAWELA', 'JAFFNA', 'MULLATIVE', 'MANNAR', 'VAVUNIYA',
    'TRINCOMALEE', 'ANURADHAPURA', 'MAHA ILLUPPALLAMA', 'PUTTALAM',
    'BATTICALOA', 'KURUNEGALA', 'KATUGASTOTA', 'KATUNAYAKA',
    'COLOMBO', 'NUWARA ELIYA', 'BADULLA', 'RATNAPURA', 'GALLE',
    'HAMBANTOTA', 'POTTUVIL', 'MATTALA', 'MONARAGALA', 'POLONNARUWA',
    'RATMALANA'
]

# Load your station mapping file
print("\nLoading station mapping file...")
station_mapping = pd.read_csv("data/bronze/metadata/grid_weather_station_mapping.csv")
print(f"Total stations in mapping: {len(station_mapping)}")
print(f"Unique stations: {station_mapping['station_id'].nunique()}")

# Check if station_name column exists
print(f"\nColumns in file: {list(station_mapping.columns)}")

if 'station_name' in station_mapping.columns:
    # Normalize station names for comparison
    station_mapping['name_upper'] = station_mapping['station_name'].str.strip().str.upper()

    print(f"\nChecking for 24 major met stations...")
    print("="*70)

    found = 0
    not_found = 0

    for major in MAJOR_STATIONS:
        matches = station_mapping[station_mapping['name_upper'] == major]
        if len(matches) > 0:
            print(f"✓ {major:20s} - FOUND ({len(matches)} records)")
            found += 1
        else:
            # Try partial match
            partial = station_mapping[station_mapping['name_upper'].str.contains(major, na=False)]
            if len(partial) > 0:
                print(f"~ {major:20s} - PARTIAL MATCH: {partial['station_name'].iloc[0]}")
                found += 1
            else:
                print(f"✗ {major:20s} - NOT FOUND")
                not_found += 1

    print("\n" + "="*70)
    print(f"Summary: {found} found, {not_found} not found")

    if not_found > 0:
        print("\n⚠ WARNING: Some major met stations are NOT in your weather station mapping!")
        print("   This means they might not be in any grid cells.")

    # Show sample of what IS in the file
    print("\n" + "="*70)
    print("Sample station names in your mapping file:")
    print("="*70)
    print(station_mapping['station_name'].head(30).to_string(index=False))

else:
    print("\n✗ ERROR: 'station_name' column not found!")
    print(f"Available columns: {list(station_mapping.columns)}")