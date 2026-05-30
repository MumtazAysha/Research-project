import pandas as pd
import requests
from tqdm import tqdm
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import json

# ⭐ CHANGE THIS EACH TIME ⭐
YEAR_TO_DOWNLOAD = 2019

file_lock = Lock()
failed_stations = []

def parse_weather_stations(excel_file):
    """Parse stations"""
    df = pd.read_excel(excel_file, sheet_name='Sheet1') 
    
    main_stations = df.iloc[:26].copy()
    main_stations['Station_ID'] = main_stations['Unnamed: 0']
    main_stations['Station_Name'] = main_stations['Unnamed: 1']
    main_stations['Latitude'] = pd.to_numeric(main_stations['Unnamed: 2'], errors='coerce')
    main_stations['Longitude'] = pd.to_numeric(main_stations['Unnamed: 3'], errors='coerce')
    main_stations['Has_3hourly'] = True
    
    rainfall_stations = df.iloc[28:].copy() 
    rainfall_stations['Station_ID'] = rainfall_stations['Unnamed: 0']
    rainfall_stations['Station_Name'] = rainfall_stations['Unnamed: 1']
    rainfall_stations['Latitude'] = pd.to_numeric(rainfall_stations['Unnamed: 2'], errors='coerce')
    rainfall_stations['Longitude'] = pd.to_numeric(rainfall_stations['Unnamed: 3'], errors='coerce')
    rainfall_stations['Has_3hourly'] = False
    
    all_stations = pd.concat([
        main_stations[['Station_ID', 'Station_Name', 'Latitude', 'Longitude', 'Has_3hourly']],
        rainfall_stations[['Station_ID', 'Station_Name', 'Latitude', 'Longitude', 'Has_3hourly']]
    ], ignore_index=True)
    
    all_stations = all_stations.dropna(subset=['Latitude', 'Longitude'])
    all_stations = all_stations.drop_duplicates(subset=['Latitude', 'Longitude']) 
    
    print(f"✅ {len(all_stations)} stations ({all_stations['Has_3hourly'].sum()} with 3-hourly)")
    return all_stations


def download_daily(lat, lon, station_id, year, max_retries=3):
    """Download daily data WITH solar radiation and retry logic"""
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "relative_humidity_2m_max",
            "relative_humidity_2m_min",
            "precipitation_sum",
            "rain_sum",
            "snowfall_sum",
            "shortwave_radiation_sum",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "wind_direction_10m_dominant",
            "pressure_msl_mean",
            "cloud_cover_mean",
            "et0_fao_evapotranspiration",
            "sunshine_duration"
        ],
        "timezone": "Asia/Colombo"
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=60)
            
            # Handle rate limiting
            if response.status_code == 429: 
                wait_time = 2 ** attempt * 5  # 5s, 10s, 20s
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            data = response.json()
            
            if 'daily' not in data:
                return None, f"No 'daily' key in response"
            
            df = pd.DataFrame({
                'date': data['daily']['time'],
                'year': year,
                'station_id': station_id,
                'lat': lat,
                'lon': lon,
                'temp_max_C': data['daily']['temperature_2m_max'],
                'temp_min_C': data['daily']['temperature_2m_min'],
                'temp_mean_C': data['daily']['temperature_2m_mean'],
                'RH_max_pct': data['daily']['relative_humidity_2m_max'],
                'RH_min_pct': data['daily']['relative_humidity_2m_min'],
                'precipitation_mm': data['daily']['precipitation_sum'],
                'rain_mm': data['daily']['rain_sum'],
                'snowfall_mm': data['daily']['snowfall_sum'],
                'solar_radiation_MJ': data['daily']['shortwave_radiation_sum'],
                'wind_speed_max_ms': data['daily']['wind_speed_10m_max'],
                'wind_gusts_max_ms': data['daily']['wind_gusts_10m_max'],
                'wind_direction_deg': data['daily']['wind_direction_10m_dominant'],
                'pressure_msl_hPa': data['daily']['pressure_msl_mean'],
                'cloud_cover_pct': data['daily']['cloud_cover_mean'],
                'evapotranspiration_mm': data['daily']['et0_fao_evapotranspiration'],
                'sunshine_duration_s': data['daily']['sunshine_duration']
            })
            return df, None
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt * 3)
                continue
            return None, "Timeout after retries"
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt * 2)
                continue
            return None, f"RequestException: {str(e)}"
        except Exception as e:
            return None, f"{type(e).__name__}: {str(e)}"
    
    return None, "Max retries exceeded"


def download_3hourly(lat, lon, station_id, year, max_retries=3):
    """Download 3-hourly data WITH solar radiation and retry logic"""
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "dew_point_2m",
            "precipitation",
            "cloud_cover",
            "pressure_msl",
            "wind_speed_10m",
            "wind_direction_10m",
            "shortwave_radiation",
            "direct_radiation",
            "diffuse_radiation",
            "direct_normal_irradiance"
        ],
        "timezone": "Asia/Colombo"
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=60)
            
            # Handle rate limiting
            if response.status_code == 429:
                wait_time = 2 ** attempt * 5
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            data = response.json()
            
            if 'hourly' not in data:
                return None, f"No 'hourly' key in response"
            
            times = pd.to_datetime(data['hourly']['time'])
            hours = times.hour
            mask_3hourly = hours % 3 == 0
            
            df = pd.DataFrame({
                'time': times[mask_3hourly],
                'year': year,
                'station_id': station_id,
                'lat': lat,
                'lon': lon,
                'temperature_2m': pd.Series(data['hourly']['temperature_2m'])[mask_3hourly].values,
                'relative_humidity_2m': pd.Series(data['hourly']['relative_humidity_2m'])[mask_3hourly].values,
                'dew_point_2m': pd.Series(data['hourly']['dew_point_2m'])[mask_3hourly].values,
                'precipitation': pd.Series(data['hourly']['precipitation'])[mask_3hourly].values,
                'cloud_cover': pd.Series(data['hourly']['cloud_cover'])[mask_3hourly].values,
                'pressure_msl': pd.Series(data['hourly']['pressure_msl'])[mask_3hourly].values,
                'wind_speed_10m': pd.Series(data['hourly']['wind_speed_10m'])[mask_3hourly].values,
                'wind_direction_10m': pd.Series(data['hourly']['wind_direction_10m'])[mask_3hourly].values,
                'shortwave_radiation': pd.Series(data['hourly']['shortwave_radiation'])[mask_3hourly].values,
                'direct_radiation': pd.Series(data['hourly']['direct_radiation'])[mask_3hourly].values,
                'diffuse_radiation': pd.Series(data['hourly']['diffuse_radiation'])[mask_3hourly].values,
                'direct_normal_irradiance': pd.Series(data['hourly']['direct_normal_irradiance'])[mask_3hourly].values
            })
            
            return df, None
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt * 3)
                continue
            return None, "Timeout after retries"
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt * 2)
                continue
            return None, f"RequestException: {str(e)}"
        except Exception as e:
            return None, f"{type(e).__name__}: {str(e)}"
    
    return None, "Max retries exceeded"


def download_station(row, year, output_dir):
    """Download one station - daily and (optionally) 3-hourly"""
    
    station_id = row['Station_ID']
    has_3hourly = row['Has_3hourly']
    
    results = []
    station_failed = False
    
    # DAILY (all stations)
    daily_file = f"{output_dir}/daily/station_{station_id}_{year}_daily.csv"
    if not os.path.exists(daily_file):
        df, error = download_daily(row['Latitude'], row['Longitude'], station_id, year)
        if df is not None:
            df['station_name'] = row['Station_Name']
            try:
                with file_lock:
                    df.to_csv(daily_file, index=False)
                results.append(('daily', True, None))
            except Exception as e:
                results.append(('daily', False, f"Write error: {e}"))
                station_failed = True
        else:
            results.append(('daily', False, error))
            station_failed = True
        time.sleep(2)  # Increased delay between requests
    else:
        results.append(('daily', True, 'exists'))
    
    # 3-HOURLY (main stations only)
    if has_3hourly:
        hourly_file = f"{output_dir}/3hourly/station_{station_id}_{year}_3hourly.csv"
        if not os.path.exists(hourly_file):
            df, error = download_3hourly(row['Latitude'], row['Longitude'], station_id, year)
            if df is not None:
                df['station_name'] = row['Station_Name']
                try:
                    with file_lock:
                        df.to_csv(hourly_file, index=False)
                    results.append(('3hourly', True, None))
                except Exception as e:
                    results.append(('3hourly', False, f"Write error: {e}"))
                    station_failed = True
            else:
                results.append(('3hourly', False, error))
                station_failed = True
            time.sleep(2)
        else:
            results.append(('3hourly', True, 'exists'))
    
    # Log failed stations
    if station_failed:
        with file_lock:
            failed_stations.append({
                'station_id': station_id,
                'station_name': row['Station_Name'],
                'lat': row['Latitude'],
                'lon': row['Longitude'],
                'has_3hourly': has_3hourly
            })
    
    return station_id, results


def download_year_parallel(stations_df, year, output_dir, workers=2):  # Reduced workers from 3 to 2
    """Download with progress tracking"""
    
    year_dir = f"{output_dir}/year_{year}"
    os.makedirs(f"{year_dir}/daily", exist_ok=True)
    os.makedirs(f"{year_dir}/3hourly", exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"📅 DOWNLOADING YEAR {year} - WITH SOLAR RADIATION!")
    print(f"{'='*70}")
    print(f"📊 Stations: {len(stations_df)}")
    print(f"⚡ Workers: {workers}")
    print(f"📦 Data: Daily + 3-Hourly (with solar radiation)")
    print(f"🔄 Auto-retry: 3 attempts per request")
    print(f"⏱️  Estimated: ~{len(stations_df) * 6 / workers / 60:.0f} minutes\n")
    
    successful = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(download_station, row, year, year_dir): row['Station_ID']
            for _, row in stations_df.iterrows()
        }
        
        with tqdm(total=len(stations_df), desc="Stations") as pbar:
            for future in as_completed(futures):
                try:
                    station_id, results = future.result()
                    for freq, success, msg in results:
                        if success:
                            successful += 1
                        else:
                            failed += 1
                except Exception as e:
                    failed += 1
                
                pbar.update(1)
                pbar.set_postfix({'✅': successful, '❌': failed})
    
    print(f"\n{'='*70}")
    print(f"✅ YEAR {year} COMPLETE!")
    print(f"{'='*70}")
    print(f"   Successful downloads: {successful}")
    print(f"   Failed: {failed}")
    
    # Save failed stations log
    if failed_stations:
        failed_log = f"{year_dir}/failed_stations_{year}.json"
        with open(failed_log, 'w') as f:
            json.dump(failed_stations, f, indent=2)
        print(f"\n⚠️  {len(failed_stations)} stations failed - saved to {failed_log}")


def main():
    EXCEL_FILE = r"data\bronze\weather_data\Met data weather stations(AutoRecovered).xlsx"
    OUTPUT_DIR = r"data\silver\openmeteo"
    
    stations = parse_weather_stations(EXCEL_FILE)
    
    print(f"\n🚀 Starting download for year {YEAR_TO_DOWNLOAD}")
    print(f"📦 Will download: Daily + 3-Hourly (all with solar radiation!)")
    
    download_year_parallel(stations, YEAR_TO_DOWNLOAD, OUTPUT_DIR, workers=2)
    
    print(f"\n✅ DOWNLOAD COMPLETE!")
    print(f"📂 Data saved to: {OUTPUT_DIR}/year_{YEAR_TO_DOWNLOAD}/")


if __name__ == "__main__":
    main()