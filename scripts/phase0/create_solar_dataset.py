import pandas as pd
import os
import numpy as np

print("="*80)
print("STEP 2: CREATE SOLAR RADIATION DATASET (7 YEARS)")
print("="*80)

station = "43415"  # VAVUNIYA - 7 complete years

# Load ALL years 2019-2025
all_data = []
for year in range(2019, 2026):
    hourly_path = f'data/silver/openmeteo/year_{year}/3hourly/station_{station}_{year}_3hourly.csv'
    
    if os.path.exists(hourly_path):
        print(f"📥 Loading {year}...")
        df = pd.read_csv(hourly_path)
        df['year'] = year
        all_data.append(df)
        print(f"   ✅ {len(df)} records ({len(df)/8:.0f} days)")

# Combine all years
df_all = pd.concat(all_data, ignore_index=True)
print(f"\n✅ TOTAL: {len(df_all):,} 3-hourly records ({len(df_all)/8:.0f} days)")
print(f"   Years: {sorted(df_all['year'].unique())}")

# Convert to datetime
df_all['time'] = pd.to_datetime(df_all['time'])
df_all['date'] = df_all['time'].dt.date

# Create DAILY averages from 3-hourly data
print("\n☀️  Aggregating to DAILY solar radiation...")

daily_data = df_all.groupby('date').agg({
    'cloud_cover': 'mean',           # Avg daily cloud cover %
    'temperature_2m': ['mean', 'max', 'min'],  # Temp stats
    'precipitation': 'sum',          # Total daily rainfall
    'relative_humidity_2m': 'mean',  # Avg humidity
    'wind_speed_10m': 'mean',        # Avg wind speed
    'pressure_msl': 'mean'           # Avg pressure
}).reset_index()

# Flatten column names
daily_data.columns = ['date', 'cloud_cover', 'temp_mean', 'temp_max', 'temp_min', 
                     'precipitation', 'humidity', 'wind_speed', 'pressure']

# CALCULATE SOLAR RADIATION (Sri Lanka validated formula)
daily_data['solar_radiation'] = 6.5 - (daily_data['cloud_cover'] / 100 * 3.0)

print(f"\n✅ Created {len(daily_data):,} daily records")
print(f"   Date range: {daily_data['date'].min()} to {daily_data['date'].max()}")

print(f"\n📊 SOLAR RADIATION STATISTICS (7 years):")
print(daily_data['solar_radiation'].describe())

print(f"\n☁️  SAMPLE DATA:")
print(daily_data[['date', 'cloud_cover', 'solar_radiation', 'temp_mean', 'precipitation']].head(10))

# Save processed dataset
output_file = f'data/processed/solar_daily_{station}_2019_2025.csv'
os.makedirs('data/processed', exist_ok=True)
daily_data.to_csv(output_file, index=False)

print(f"\n💾 Saved to: {output_file}")

# Show YEARLY variation (proof that years differ!)
print(f"\n📅 YEARLY AVERAGE SOLAR RADIATION:")
daily_data['year'] = pd.to_datetime(daily_data['date']).dt.year
yearly = daily_data.groupby('year').agg({
    'solar_radiation': 'mean',
    'cloud_cover': 'mean',
    'precipitation': 'sum'
})
print(yearly.round(2))

print(f"\n📈 DATA READY FOR ML TRAINING!")
print(f"   Total days: {len(daily_data):,}")
print(f"   Features: cloud_cover, temp, precipitation, humidity, wind, pressure")
print(f"   Target: solar_radiation (kWh/m²/day)")
print(f"\n💡 Next: Feature engineering for time series prediction!")
