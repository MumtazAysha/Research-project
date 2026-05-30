import requests
import pandas as pd
import time
import os

OUTPUT_FILE = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\weather_data\corrected_historical_2010_2025.csv'

missing_grids = [
    ('grid_12_13', 6.953036, 80.819382),
    ('grid_12_14', 6.953036, 80.910332),
    ('grid_12_15', 6.953036, 81.001282),
    ('grid_12_16', 6.953036, 81.092231),
    ('grid_12_17', 6.953036, 81.183181),
    ('grid_12_18', 6.953036, 81.274131),
    ('grid_12_19', 6.953036, 81.365080),
    ('grid_13_14', 7.043126, 80.910332),
    ('grid_13_15', 7.043126, 81.001282),
    ('grid_13_16', 7.043126, 81.092231),
    ('grid_13_17', 7.043126, 81.183181),
    ('grid_13_18', 7.043126, 81.274131),
    ('grid_13_19', 7.043126, 81.365080),
    ('grid_13_20', 7.043126, 81.456030),
    ('grid_13_21', 7.043126, 81.546980),
    ('grid_14_4',  7.133216, 80.000835),
    ('grid_14_15', 7.133216, 81.001282),
    ('grid_14_16', 7.133216, 81.092231),
    ('grid_14_17', 7.133216, 81.183181),
    ('grid_14_21', 7.133216, 81.546980),
    ('grid_15_16', 7.223306, 81.092231),
    ('grid_16_6',  7.313396, 80.182735),
    ('grid_16_11', 7.313396, 80.637483),
    ('grid_16_15', 7.313396, 81.001282),
    ('grid_16_16', 7.313396, 81.092231),
    ('grid_18_8',  7.493577, 80.364634),
    ('grid_18_15', 7.493577, 81.001282),
    ('grid_19_11', 7.583667, 80.637483),
    ('grid_19_15', 7.583667, 81.001282),
    ('grid_20_22', 7.673757, 81.637929),
    ('grid_25_19', 8.124207, 81.365080),
]

def fetch_grid(grid_id, lat, lon):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "2010-01-01",
        "end_date": "2025-12-31",
        "daily": "temperature_2m_mean,precipitation_sum",
        "timezone": "Asia/Colombo"
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()

    daily = data.get("daily", {})
    df_daily = pd.DataFrame({
        'date': pd.to_datetime(daily["time"]),
        'T':    daily["temperature_2m_mean"],
        'RF':   daily["precipitation_sum"],
    })
    df_daily['year']  = df_daily['date'].dt.year
    df_daily['month'] = df_daily['date'].dt.month
    df_monthly = df_daily.groupby(['year', 'month']).agg(
        T_om=('T',  'mean'),
        RF_om=('RF', 'sum')
    ).reset_index()

    df_monthly['grid_id']      = grid_id
    df_monthly['lat']          = lat
    df_monthly['lon']          = lon
    df_monthly['elevation']    = data.get('elevation', None)
    df_monthly['T_corrected']  = df_monthly['T_om']
    df_monthly['RF_corrected'] = df_monthly['RF_om']

    return df_monthly[['grid_id','lat','lon','elevation','year','month',
                        'T_om','RF_om','T_corrected','RF_corrected']]


# Load existing and find already-downloaded grids
existing = pd.read_csv(OUTPUT_FILE)
already_done = set(existing['grid_id'].unique())
print(f"Existing rows: {len(existing)}")
print(f"Already downloaded: {len(already_done)} grids")

new_rows = []
for i, (grid_id, lat, lon) in enumerate(missing_grids):
    # Skip if already downloaded
    if grid_id in already_done:
        print(f"  [{i+1}/{len(missing_grids)}] Skipping {grid_id} (already exists)")
        continue

    print(f"  [{i+1}/{len(missing_grids)}] Downloading {grid_id}...", end=' ')

    # Retry up to 3 times on 429
    for attempt in range(3):
        try:
            df = fetch_grid(grid_id, lat, lon)
            new_rows.append(df)
            print(f"✓ {len(df)} rows")
            time.sleep(2)   # 2 seconds between successful requests
            break
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait = 60 * (attempt + 1)   # 60s, 120s, 180s
                print(f"  Rate limited. Waiting {wait}s...", end=' ')
                time.sleep(wait)
            else:
                print(f"✗ FAILED: {e}")
                break
        except Exception as e:
            print(f"✗ FAILED: {e}")
            break

if new_rows:
    combined = pd.concat([existing] + new_rows, ignore_index=True)
    combined.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone! Total rows now: {len(combined)}")
    print(f"Added {sum(len(d) for d in new_rows)} rows for {len(new_rows)} new grid cells")
else:
    print("\nNo new data downloaded.")
