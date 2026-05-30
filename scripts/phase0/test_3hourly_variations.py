import pandas as pd
import os

# Test one of your MAIN stations (these have 3-hourly data)
main_stations = ["43476", "43415", "43404", "43410", "43413"]  # Bandarawela, Vavuniya, etc.
station = "43476"  # CHANGE THIS to test different main stations

print("="*80)
print("🔍 3-HOURLY vs DAILY DATA COMPARISON - MAIN STATION")
print("="*80)

for year in [2019, 2020, 2021, 2022, 2023, 2024]:
    # Check 3-hourly first (rich data)
    hourly_path = f'data/silver/openmeteo/year_{year}/3hourly/station_{station}_{year}_3hourly.csv'
    
    try:
        if os.path.exists(hourly_path):
            df_hourly = pd.read_csv(hourly_path)
            df_hourly['time'] = pd.to_datetime(df_hourly['time'])
            df_hourly['date'] = df_hourly['time'].dt.date
            
            # Daily averages from 3-hourly
            daily_cloud = df_hourly.groupby('date')['cloud_cover'].mean()
            avg_cloud = daily_cloud.mean()
            
            print(f"\n📅 {year} - 3HOURLY ({station}):")
            print(f"   ☁️  Cloud cover: {avg_cloud:.1f}%")
            print(f"   📊 Records: {len(df_hourly)}")
        else:
            print(f"\n📅 {year} - 3HOURLY ({station}): ❌ Missing")
        
        # Check daily data
        daily_path = f'data/silver/openmeteo/year_{year}/daily/station_{station}_{year}_daily.csv'
        if os.path.exists(daily_path):
            df_daily = pd.read_csv(daily_path)
            print(f"   🌡️  Daily temp max: {df_daily.get('temperature_2m_max', 'N/A').mean():.1f}°C" if 'temperature_2m_max' in df_daily.columns else "   🌡️  Daily data: Limited params")
            
    except Exception as e:
        print(f"\n📅 {year}: ❌ Error: {e}")

print("\n💡 Test other main stations by changing: station = '43476'")
