import pandas as pd
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# ⭐ CHANGE YEAR HERE ⭐
YEAR_TO_DOWNLOAD = 2019

file_lock = Lock()

def parse_weather_stations(excel_file):
    """Parse stations and classify them WITH DIAGNOSTICS"""
    df = pd.read_excel(excel_file, sheet_name='Sheet1')
    
    print(f"\n{'='*70}")
    print(f"📊 PARSING DIAGNOSTICS")
    print(f"{'='*70}")
    
    # Main stations (Rows 3-26 in Excel = index 2-25 in pandas)
    main_stations = df.iloc[2:26].copy()
    main_stations['Station_ID'] = main_stations['Unnamed: 0']
    main_stations['Station_Name'] = main_stations['Unnamed: 1']
    main_stations['Latitude'] = pd.to_numeric(main_stations['Unnamed: 2'], errors='coerce')
    main_stations['Longitude'] = pd.to_numeric(main_stations['Unnamed: 3'], errors='coerce')
    main_stations['Type'] = 'MAIN'
    main_stations['Source_Row'] = range(3, 27)  # Excel row numbers
    
    print(f"\n📍 MAIN STATIONS (Rows 3-26 in Excel):")
    print(f"   Total parsed: {len(main_stations)}")
    
    # Check for nulls in main stations
    main_nulls = main_stations[main_stations[['Latitude', 'Longitude']].isnull().any(axis=1)]
    if len(main_nulls) > 0:
        print(f"\n⚠️  MAIN STATIONS WITH MISSING COORDINATES:")
        for _, row in main_nulls.iterrows():
            print(f"   ❌ Row {row['Source_Row']}: {row['Station_ID']} - {row['Station_Name']}")
            print(f"      Lat: {row['Latitude']}, Lon: {row['Longitude']}")
    
    # Rainfall stations (Row 30+ in Excel = index 29+ in pandas)
    rainfall_stations = df.iloc[29:].copy()
    rainfall_stations['Station_ID'] = rainfall_stations['Unnamed: 0']
    rainfall_stations['Station_Name'] = rainfall_stations['Unnamed: 1']
    rainfall_stations['Latitude'] = pd.to_numeric(rainfall_stations['Unnamed: 2'], errors='coerce')
    rainfall_stations['Longitude'] = pd.to_numeric(rainfall_stations['Unnamed: 3'], errors='coerce')
    rainfall_stations['Type'] = 'RAINFALL'
    rainfall_stations['Source_Row'] = range(30, 30 + len(rainfall_stations))  # Excel row numbers
    
    print(f"\n📍 RAINFALL STATIONS (Row 30+ in Excel):")
    print(f"   Total parsed: {len(rainfall_stations)}")
    
    # Check for nulls in rainfall stations
    rainfall_nulls = rainfall_stations[rainfall_stations[['Latitude', 'Longitude']].isnull().any(axis=1)]
    if len(rainfall_nulls) > 0:
        print(f"\n⚠️  RAINFALL STATIONS WITH MISSING COORDINATES (First 20):")
        for _, row in rainfall_nulls.head(20).iterrows():
            print(f"   ❌ Row {row['Source_Row']}: {row['Station_ID']} - {row['Station_Name']}")
            print(f"      Lat: {row['Latitude']}, Lon: {row['Longitude']}")
        if len(rainfall_nulls) > 20:
            print(f"   ... and {len(rainfall_nulls) - 20} more")
    
    # Combine
    all_stations = pd.concat([
        main_stations[['Station_ID', 'Station_Name', 'Latitude', 'Longitude', 'Type', 'Source_Row']],
        rainfall_stations[['Station_ID', 'Station_Name', 'Latitude', 'Longitude', 'Type', 'Source_Row']]
    ], ignore_index=True)
    
    print(f"\n📊 COMBINED:")
    print(f"   Total before cleaning: {len(all_stations)}")
    
    # Remove nulls
    before_dropna = len(all_stations)
    all_stations_clean = all_stations.dropna(subset=['Latitude', 'Longitude'])
    removed_nulls = before_dropna - len(all_stations_clean)
    
    print(f"   Removed (missing coords): {removed_nulls}")
    
    # Check for duplicates
    before_dedup = len(all_stations_clean)
    duplicates = all_stations_clean[all_stations_clean.duplicated(subset=['Latitude', 'Longitude'], keep=False)]
    
    if len(duplicates) > 0:
        print(f"\n⚠️  DUPLICATE COORDINATES FOUND:")
        for (lat, lon), group in duplicates.groupby(['Latitude', 'Longitude']):
            print(f"   📍 Location ({lat:.4f}, {lon:.4f}) has {len(group)} stations:")
            for _, row in group.iterrows():
                print(f"      - Row {row['Source_Row']}: {row['Station_ID']} - {row['Station_Name']}")
    
    all_stations_final = all_stations_clean.drop_duplicates(subset=['Latitude', 'Longitude'])
    removed_duplicates = before_dedup - len(all_stations_final)
    
    print(f"   Removed (duplicates): {removed_duplicates}")
    print(f"\n✅ FINAL COUNT: {len(all_stations_final)} valid unique stations")
    print(f"{'='*70}\n")
    
    # Save diagnostic report
    all_stations.to_csv("data/silver/openmeteo/station_parsing_full_list.csv", index=False)
    print(f"💾 Full station list saved: data/silver/openmeteo/station_parsing_full_list.csv")
    
    if removed_nulls > 0 or removed_duplicates > 0:
        removed_stations = all_stations[~all_stations.index.isin(all_stations_final.index)]
        removed_stations.to_csv("data/silver/openmeteo/removed_stations.csv", index=False)
        print(f"💾 Removed stations saved: data/silver/openmeteo/removed_stations.csv\n")
    
    return all_stations_final[['Station_ID', 'Station_Name', 'Latitude', 'Longitude', 'Type']]


def download_with_retry(lat, lon, station_id, station_name, year, station_type, output_dir):
    """Download one station with automatic retry on rate limits"""
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    daily_dir = f"{output_dir}/year_{year}/daily"
    monthly_dir = f"{output_dir}/year_{year}/monthly"
    hourly_dir = f"{output_dir}/year_{year}/3hourly"
    
    # Create directories
    with file_lock:
        os.makedirs(daily_dir, exist_ok=True)
        os.makedirs(monthly_dir, exist_ok=True)
        if station_type == 'MAIN':
            os.makedirs(hourly_dir, exist_ok=True)
    
    # Check if already downloaded
    daily_file = f"{daily_dir}/station_{station_id}_{year}_daily.csv"
    if os.path.exists(daily_file):
        return station_id, True, "Already exists"
    
    # Define parameters based on station type
    if station_type == 'MAIN':
        # Main stations: Temp Max/Min, Rain, RH
        daily_params = [
            "temperature_2m_max", 
            "temperature_2m_min", 
            "precipitation_sum",
            "relative_humidity_2m_max",
            "relative_humidity_2m_min"
        ]
        hourly_params = [
            "precipitation", "relative_humidity_2m", "temperature_2m",
            "dew_point_2m", "wind_speed_10m", "wind_direction_10m",
            "pressure_msl", "visibility", "cloud_cover"
        ]
    else:
        # Rainfall stations: Rain ONLY
        daily_params = ["precipitation_sum"]
        hourly_params = []
    
    # ===== DOWNLOAD DAILY DATA =====
    max_retries = 5
    for attempt in range(max_retries):
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": f"{year}-01-01",
                "end_date": f"{year}-12-31",
                "daily": daily_params,
                "timezone": "Asia/Colombo"
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            # Handle rate limiting
            if response.status_code == 429:
                wait_time = min(300, (2 ** attempt) * 20)
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            data = response.json()
            
            if 'daily' not in data:
                return station_id, False, "No daily data"
            

            # Save daily data
            df_daily = pd.DataFrame(data['daily'])
            df_daily.rename(columns={'time': 'date'}, inplace=True)
            df_daily['station_id'] = station_id
            df_daily['station_name'] = station_name
            
            with file_lock:
                df_daily.to_csv(daily_file, index=False)
            
            # Create monthly data
            df_daily['date'] = pd.to_datetime(df_daily['date'])
            agg_dict = {'station_id': 'first', 'station_name': 'first'}
            
            for col in df_daily.columns:
                if 'precipitation' in col or 'rain' in col:
                    agg_dict[col] = 'sum'
                elif 'temperature' in col and 'max' in col:
                    agg_dict[col] = 'max'
                elif 'temperature' in col and 'min' in col:
                    agg_dict[col] = 'min'
                elif col not in ['date', 'station_id', 'station_name']:
                    agg_dict[col] = 'mean'
            
            df_monthly = df_daily.resample('ME', on='date').agg(agg_dict).reset_index()
            monthly_file = f"{monthly_dir}/station_{station_id}_{year}_monthly.csv"
            
            with file_lock:
                df_monthly.to_csv(monthly_file, index=False)
            
            break
            
        except Exception as e:
            if attempt == max_retries - 1:
                return station_id, False, f"Daily failed: {str(e)}"
            time.sleep(5)
    
    # ===== DOWNLOAD 3-HOURLY DATA (Main stations only) =====
    if station_type == 'MAIN' and hourly_params:
        time.sleep(2)  # Pause between requests
        
        for attempt in range(max_retries):
            try:
                params = {
                    "latitude": lat,
                    "longitude": lon,
                    "start_date": f"{year}-01-01",
                    "end_date": f"{year}-12-31",
                    "hourly": hourly_params,
                    "timezone": "Asia/Colombo"
                }
                
                response = requests.get(url, params=params, timeout=60)
                
                if response.status_code == 429:
                    wait_time = min(300, (2 ** attempt) * 20)
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if 'hourly' in data:
                    df_hourly = pd.DataFrame(data['hourly'])
                    df_hourly['time'] = pd.to_datetime(df_hourly['time'])
                    df_3h = df_hourly[df_hourly['time'].dt.hour % 3 == 0].copy()
                    df_3h['station_id'] = station_id
                    df_3h['station_name'] = station_name
                    
                    hourly_file = f"{hourly_dir}/station_{station_id}_{year}_3hourly.csv"
                    with file_lock:
                        df_3h.to_csv(hourly_file, index=False)
                
                break
                
            except Exception as e:
                if attempt == max_retries - 1:
                    return station_id, False, f"3-hourly failed: {str(e)}"
                time.sleep(5)
    
    return station_id, True, "Success"


def batch_download(stations_df, year, output_dir, workers=2):
    """Download all stations with parallel workers"""
    
    print(f"\n{'='*70}")
    print(f"🚀 BATCH DOWNLOADER - YEAR {year}")
    print(f"{'='*70}")
    print(f"📊 Total stations: {len(stations_df)}")
    print(f"   - Main stations (Full params): {(stations_df['Type']=='MAIN').sum()}")
    print(f"   - Rainfall stations (Rain only): {(stations_df['Type']=='RAINFALL').sum()}")
    print(f"⚡ Workers: {workers} parallel downloads")
    print(f"⏱️  Estimated time: ~{len(stations_df) * 3 / workers / 60:.0f} minutes")
    print(f"💾 Auto-saves progress (can stop/resume anytime)\n")
    
    time.sleep(3)
    
    successful = []
    failed = []
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                download_with_retry,
                row['Latitude'],
                row['Longitude'],
                row['Station_ID'],
                row['Station_Name'],
                year,
                row['Type'],
                output_dir
            ): row['Station_ID'] 
            for _, row in stations_df.iterrows()
        }
        
        from tqdm import tqdm
        with tqdm(total=len(stations_df), desc="Downloading", ncols=80) as pbar:
            for future in as_completed(futures):
                try:
                    station_id, success, msg = future.result()
                    if success:
                        successful.append(station_id)
                    else:
                        failed.append((station_id, msg))
                except Exception as e:
                    failed.append(("UNKNOWN", str(e)))
                
                pbar.update(1)
                pbar.set_postfix({'✅': len(successful), '❌': len(failed)})
    
    # Summary
    print(f"\n{'='*70}")
    print(f"✅ DOWNLOAD COMPLETE FOR YEAR {year}!")
    print(f"{'='*70}")
    print(f"   Successful: {len(successful)}/{len(stations_df)} ({len(successful)/len(stations_df)*100:.1f}%)")
    print(f"   Failed: {len(failed)}")
    
    if failed:
        print(f"\n❌ Failed stations (showing first 10):")
        for sid, msg in failed[:10]:
            print(f"   - {sid}: {msg}")
        
        # Save failed list
        failed_df = pd.DataFrame(failed, columns=['Station_ID', 'Error'])
        failed_df.to_csv(f"{output_dir}/year_{year}/failed_stations_{year}.csv", index=False)
        print(f"\n💾 Full error list: {output_dir}/year_{year}/failed_stations_{year}.csv")
    
    if len(successful) == len(stations_df):
        print(f"\n🎉 ALL STATIONS DOWNLOADED SUCCESSFULLY!")
        print(f"👉 Change YEAR_TO_DOWNLOAD to {year + 1} and run again")
    elif len(successful) > len(stations_df) * 0.9:
        print(f"\n💡 >90% complete! Re-run this script to retry failed stations")


def main():
    EXCEL_FILE = r"data\bronze\weather_data\Met data weather stations(AutoRecovered).xlsx"
    OUTPUT_DIR = r"data\silver\openmeteo"
    
    stations = parse_weather_stations(EXCEL_FILE)
    print(f"✅ Loaded {len(stations)} stations from Excel")
    
    batch_download(stations, YEAR_TO_DOWNLOAD, OUTPUT_DIR, workers=2)


if __name__ == "__main__":
    main()