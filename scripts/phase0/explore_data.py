import pandas as pd
import os

print("="*80)
print("STEP 1: DATA EXPLORATION")
print("="*80)

station = "43476"  # BANDARAWELA

print(f"\n📍 Exploring station: {station}")
print("-"*80)

# Check what years we have for 3-hourly (MAIN stations)
years_found = []
for year in range(2019, 2026):
    hourly_path = f'data/silver/openmeteo/year_{year}/3hourly/station_{station}_{year}_3hourly.csv'
    
    if os.path.exists(hourly_path):
        years_found.append(year)
        df = pd.read_csv(hourly_path)
        print(f"\n✅ {year} 3-HOURLY: {len(df)} records ({len(df)/8:.0f} days)")
        print(f"   ALL Columns: {list(df.columns)}")  # Show ALL columns

print(f"\n📊 SUMMARY:")
print(f"   Years available: {years_found}")
print(f"   Total years: {len(years_found)}")

# Load 2024 data for detailed analysis
if os.path.exists(f'data/silver/openmeteo/year_2024/3hourly/station_{station}_2024_3hourly.csv'):
    df = pd.read_csv(f'data/silver/openmeteo/year_2024/3hourly/station_{station}_2024_3hourly.csv')
    
    print(f"\n📋 SAMPLE DATA (First 5 records, 2024):")
    print(df.head())
    
    # Check if cloud_cover exists
    if 'cloud_cover' in df.columns:
        print(f"\n☁️  CLOUD COVER FOUND! ✅")
        print(f"   Min: {df['cloud_cover'].min()}%")
        print(f"   Max: {df['cloud_cover'].max()}%")
        print(f"   Mean: {df['cloud_cover'].mean():.1f}%")
    else:
        print(f"\n⚠️  NO cloud_cover column - we'll estimate from other variables")
    
    print(f"\n📊 KEY STATISTICS:")
    available_cols = [col for col in ['cloud_cover', 'temperature_2m', 'precipitation', 'relative_humidity_2m'] if col in df.columns]
    print(df[available_cols].describe())

print("\n💡 Next: We'll create daily solar radiation estimates!")

