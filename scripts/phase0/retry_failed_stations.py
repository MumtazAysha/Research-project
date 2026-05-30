import pandas as pd
import requests
import os
import time

# ⭐ CHANGE YEAR HERE ⭐
YEAR_TO_DOWNLOAD = 2019

def parse_weather_stations(excel_file):
    """Parse stations and identify which data types they need"""
    df = pd.read_excel(excel_file, sheet_name='Sheet1')
    
    # --- Main Stations (Rows 0-25) ---
    # These have Daily AND 3-Hourly data
    main_stations = df.iloc[:26].copy()
    main_stations['Station_ID'] = main_stations['Unnamed: 0']
    main_stations['Station_Name'] = main_stations['Unnamed: 1']
    main_stations['Latitude'] = pd.to_numeric(main_stations['Unnamed: 2'], errors='coerce')
    main_stations['Longitude'] = pd.to_numeric(main_stations['Unnamed: 3'], errors='coerce')
    main_stations['Has_3hourly'] = True  # ✅ Main stations have 3-hourly
    
    # --- Rainfall Stations (Row 28 onwards) ---
    # These have Daily data only
    rainfall_stations = df.iloc[28:].copy()
    rainfall_stations['Station_ID'] = rainfall_stations['Unnamed: 0']
    rainfall_stations['Station_Name'] = rainfall_stations['Unnamed: 1']
    rainfall_stations['Latitude'] = pd.to_numeric(rainfall_stations['Unnamed: 2'], errors='coerce')
    rainfall_stations['Longitude'] = pd.to_numeric(rainfall_stations['Unnamed: 3'], errors='coerce')
    rainfall_stations['Has_3hourly'] = False # ❌ Rainfall stations do not
    
    # Combine
    all_stations = pd.concat([
        main_stations[['Station_ID', 'Station_Name', 'Latitude', 'Longitude', 'Has_3hourly']],
        rainfall_stations[['Station_ID', 'Station_Name', 'Latitude', 'Longitude', 'Has_3hourly']]
    ], ignore_index=True)
    
    # Clean data
    all_stations = all_stations.dropna(subset=['Latitude', 'Longitude'])
    all_stations = all_stations.drop_duplicates(subset=['Latitude', 'Longitude'])
    
    return all_stations

def download_data(lat, lon, station_id, year, has_3hourly, output_dir):
    """Downloads Daily, Monthly (derived), and 3-Hourly data"""
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    # 1. Setup Folders
    daily_dir = f"{output_dir}/year_{year}/daily"
    monthly_dir = f"{output_dir}/year_{year}/monthly"
    hourly_dir = f"{output_dir}/year_{year}/3hourly"
    
    os.makedirs(daily_dir, exist_ok=True)
    os.makedirs(monthly_dir, exist_ok=True)
    if has_3hourly:
        os.makedirs(hourly_dir, exist_ok=True)

    # ---------------------------------------------------------
    # PART A: Download DAILY Data (All stations need this)
    # ---------------------------------------------------------
    daily_params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "daily": [
            "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
            "relative_humidity_2m_max", "relative_humidity_2m_min",
            "precipitation_sum", "rain_sum", 
            "shortwave_radiation_sum", 
            "wind_speed_10m_max", "wind_direction_10m_dominant",
            "pressure_msl_mean", "cloud_cover_mean", "sunshine_duration"
        ],
        "timezone": "Asia/Colombo"
    }
    
    try:
        # Request Daily Data
        r = requests.get(url, params=daily_params, timeout=30)
        r.raise_for_status()
        data = r.json()
        
        # Save Daily Data
        if 'daily' in data:
            df_daily = pd.DataFrame(data['daily'])
            # Rename time to date
            df_daily.rename(columns={'time': 'date'}, inplace=True)
            df_daily['station_id'] = station_id
            
            # Save Daily File
            daily_path = f"{daily_dir}/station_{station_id}_{year}_daily.csv"
            df_daily.to_csv(daily_path, index=False)
            
            # ---------------------------------------------------------
            # PART B: Create MONTHLY Data (Aggregate from Daily)
            # ---------------------------------------------------------
            # We calculate monthly sums/means from the daily data we just got
            df_daily['date'] = pd.to_datetime(df_daily['date'])
            df_monthly = df_daily.resample('ME', on='date').agg({
                'temperature_2m_max': 'max',
                'temperature_2m_min': 'min',
                'temperature_2m_mean': 'mean',
                'precipitation_sum': 'sum',
                'rain_sum': 'sum',
                'shortwave_radiation_sum': 'sum',
                'wind_speed_10m_max': 'max',
                'station_id': 'first'
            }).reset_index()
            
            monthly_path = f"{monthly_dir}/station_{station_id}_{year}_monthly.csv"
            df_monthly.to_csv(monthly_path, index=False)
            
        else:
            return False, "No Daily Data Found"

    except Exception as e:
        return False, f"Daily/Monthly Error: {str(e)}"

    # ---------------------------------------------------------
    # PART C: Download 3-HOURLY Data (Only for Main Stations)
    # ---------------------------------------------------------
    if has_3hourly:
        # We download hourly, then filter for every 3rd hour
        hourly_params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
            "hourly": [
                "temperature_2m", "relative_humidity_2m", "dew_point_2m",
                "precipitation", "rain", 
                "wind_speed_10m", "wind_direction_10m",
                "pressure_msl", "cloud_cover", "visibility"
            ],
            "timezone": "Asia/Colombo"
        }
        
        try:
            time.sleep(2) # Short pause to be nice to API
            r_h = requests.get(url, params=hourly_params, timeout=60)
            r_h.raise_for_status()
            data_h = r_h.json()
            
            if 'hourly' in data_h:
                df_hourly = pd.DataFrame(data_h['hourly'])
                
                # Filter to keep only 00:00, 03:00, 06:00, etc.
                df_hourly['time'] = pd.to_datetime(df_hourly['time'])
                df_3hourly = df_hourly[df_hourly['time'].dt.hour % 3 == 0].copy()
                df_3hourly['station_id'] = station_id
                
                # Save 3-Hourly File
                hourly_path = f"{hourly_dir}/station_{station_id}_{year}_3hourly.csv"
                df_3hourly.to_csv(hourly_path, index=False)
            else:
                return False, "No Hourly Data Found"

        except Exception as e:
            return False, f"3-Hourly Error: {str(e)}"

    return True, None

def main():
    EXCEL_FILE = r"data\bronze\weather_data\Met data weather stations(AutoRecovered).xlsx"
    OUTPUT_DIR = r"data\silver\openmeteo"
    
    # Load stations
    stations = parse_weather_stations(EXCEL_FILE)
    
    # Check what's already done
    daily_check_dir = f"{OUTPUT_DIR}/year_{YEAR_TO_DOWNLOAD}/daily"
    os.makedirs(daily_check_dir, exist_ok=True)
    
    # Find next undownloaded station
    next_station = None
    completed_count = 0
    
    for _, row in stations.iterrows():
        station_id = row['Station_ID']
        file_check = f"{daily_check_dir}/station_{station_id}_{YEAR_TO_DOWNLOAD}_daily.csv"
        
        if os.path.exists(file_check):
            completed_count += 1
        else:
            if next_station is None:
                next_station = row
    
    # --- Status Report ---
    print(f"\n{'='*60}")
    print(f"📥 ULTIMATE DOWNLOADER (Daily + Monthly + 3-Hourly)")
    print(f"{'='*60}")
    print(f"📅 Year: {YEAR_TO_DOWNLOAD}")
    print(f"📊 Progress: {completed_count}/{len(stations)} ({completed_count/len(stations)*100:.1f}%)")
    
    if next_station is None:
        print(f"\n✅ ALL STATIONS COMPLETE FOR {YEAR_TO_DOWNLOAD}!")
        print(f"👉 Change YEAR_TO_DOWNLOAD to {YEAR_TO_DOWNLOAD + 1}")
        return

    print(f"📍 Next: {next_station['Station_ID']} - {next_station['Station_Name']}")
    print(f"   Coords: {next_station['Latitude']:.4f}, {next_station['Longitude']:.4f}")
    print(f"   Type: {'Daily, Monthly, & 3-Hourly' if next_station['Has_3hourly'] else 'Daily & Monthly'}")
    print(f"{'-'*60}")

    # --- Perform Download ---
    success, error = download_data(
        next_station['Latitude'],
        next_station['Longitude'],
        next_station['Station_ID'],
        YEAR_TO_DOWNLOAD,
        next_station['Has_3hourly'],
        OUTPUT_DIR
    )
    
    if success:
        print(f"✅ SUCCESS! Data saved.")
        print(f"👉 Press UP ARROW + ENTER to download next station.")
    else:
        print(f"❌ FAILED: {error}")
        print(f"👉 Press UP ARROW + ENTER to retry.")

if __name__ == "__main__":
    main()
