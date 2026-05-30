"""
Bulk Download: Open-Meteo Historical Weather Data
24 Sri Lanka Met Stations | 2010-2025
Variables: Temperature, Rainfall, Wind Speed, Sunshine Duration
"""

import requests
import pandas as pd
import time
import os

# Force output to script's own folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Working directory: {os.getcwd()}")
print("Starting download...\n")

# ─── 24 Met Station Coordinates ───────────────────────────────────────────────
stations = [
    {"name": "ANURADHAPURA",      "lat": 8.35,  "lon": 80.38},
    {"name": "BADULLA",           "lat": 6.98,  "lon": 81.05},
    {"name": "BANDARAWELA",       "lat": 6.84,  "lon": 80.98},
    {"name": "BATTICALOA",        "lat": 7.72,  "lon": 81.70},
    {"name": "COLOMBO",           "lat": 6.90,  "lon": 79.87},
    {"name": "GALLE",             "lat": 6.03,  "lon": 80.22},
    {"name": "HAMBANTOTA",        "lat": 6.12,  "lon": 81.13},
    {"name": "JAFFNA",            "lat": 9.68,  "lon": 80.03},
    {"name": "KATUGASTOTA",       "lat": 7.33,  "lon": 80.63},
    {"name": "KATUNAYAKA",        "lat": 7.17,  "lon": 79.88},
    {"name": "KURUNEGALA",        "lat": 7.47,  "lon": 80.37},
    {"name": "MAHA_ILLUPPALLAMA", "lat": 8.12,  "lon": 80.47},
    {"name": "MANNAR",            "lat": 8.98,  "lon": 79.92},
    {"name": "MATTALA",           "lat": 6.30,  "lon": 81.13},
    {"name": "MONARAGALA",        "lat": 6.50,  "lon": 81.30},
    {"name": "MULLAITIVU",        "lat": 9.25,  "lon": 80.82},
    {"name": "NUWARA_ELIYA",      "lat": 6.97,  "lon": 80.77},
    {"name": "POLONNARUWA",       "lat": 7.87,  "lon": 81.05},
    {"name": "POTTUVIL",          "lat": 6.88,  "lon": 81.83},
    {"name": "PUTTALAM",          "lat": 8.03,  "lon": 79.83},
    {"name": "RATMALANA",         "lat": 6.82,  "lon": 79.88},
    {"name": "RATNAPURA",         "lat": 6.68,  "lon": 80.40},
    {"name": "TRINCOMALEE",       "lat": 8.58,  "lon": 81.25},
    {"name": "VAVUNIYA",          "lat": 8.75,  "lon": 80.50},
]

# ─── Settings ─────────────────────────────────────────────────────────────────
OUTPUT_FOLDER = "openmeteo_24_stations"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

PARAMS_COMMON = {
    "start_date": "2010-01-01",
    "end_date":   "2025-12-31",
    "daily": [
        "temperature_2m_mean",
        "precipitation_sum",
        "wind_speed_10m_max",
        "sunshine_duration"       # seconds/day → divide by 3600 = hours/day
    ],
    "timezone": "Asia/Colombo"
}

# ─── Download Loop ─────────────────────────────────────────────────────────────
print("=" * 65)
print("BULK OPEN-METEO DOWNLOAD: 24 Met Stations | 2010-2025")
print("=" * 65)

failed = []

for i, station in enumerate(stations, 1):

    output_file = os.path.join(OUTPUT_FOLDER, f"{station['name']}_daily.csv")

    # Skip if already downloaded
    if os.path.exists(output_file):
        print(f"[{i:02d}/24] ✅ SKIP  {station['name']} (already exists)")
        continue

    print(f"[{i:02d}/24] ⬇️  Downloading {station['name']}...", end=" ")

    params = {
        "latitude":  station["lat"],
        "longitude": station["lon"],
        **PARAMS_COMMON
    }

    for attempt in range(1, 4):   # up to 3 retries
        try:
            response = requests.get(BASE_URL, params=params, timeout=60)

            if response.status_code == 200:
                data = response.json()["daily"]

                df = pd.DataFrame({
                    "date":           data["time"],
                    "temp_mean_C":    data["temperature_2m_mean"],
                    "precip_mm":      data["precipitation_sum"],
                    "wind_max_ms":    data["wind_speed_10m_max"],
                    "sunshine_hrs":   [s / 3600 if s is not None else None
                                       for s in data["sunshine_duration"]]
                })

                df["station"] = station["name"]
                df["latitude"]  = station["lat"]
                df["longitude"] = station["lon"]

                df.to_csv(output_file, index=False)
                print(f"✅  {len(df)} days saved → {output_file}")
                break

            elif response.status_code == 429:
                wait = 30 * attempt
                print(f"⚠️  Rate limited. Waiting {wait}s (attempt {attempt}/3)...", end=" ")
                time.sleep(wait)

            else:
                print(f"❌  HTTP {response.status_code}")
                failed.append(station["name"])
                break

        except Exception as e:
            print(f"❌  Error: {e}")
            failed.append(station["name"])
            break

    time.sleep(3)   # polite delay between stations

# ─── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("DOWNLOAD COMPLETE")
print("=" * 65)

downloaded = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith(".csv")]
print(f"\n✅ Successfully downloaded: {len(downloaded)}/24 stations")
print(f"📁 Saved to folder: {OUTPUT_FOLDER}/")

if failed:
    print(f"\n❌ Failed stations ({len(failed)}): {failed}")
    print("   Re-run the script — it will skip already-downloaded stations")
    print("   and retry only the failed ones.")
else:
    print("\n🎉 All 24 stations downloaded successfully!")

print("\n📋 Next step:")
print("   Run the aggregation script to convert daily → monthly CSV")