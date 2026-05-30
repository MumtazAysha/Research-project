"""
fix_missing_grids.py
Fetches all missing grids automatically in batches with delays.
Just run once - it will loop until all 721 grids are done.
"""

import os
import time
import pandas as pd
import numpy as np
import joblib
import requests

os.chdir(os.path.dirname(os.path.abspath(__file__)))

GRID_FILE        = "../../data/bronze/metadata/grid_coordinates_all.csv"
MODELS_DIR       = "../../data/gold/models"
OUTPUT_RAW       = "../../data/silver/grid_weather_raw_2010_2025.csv"
OUTPUT_CORRECTED = "../../data/gold/grid_weather_corrected_2010_2025.csv"

BATCH_SIZE = 100
DELAY_SECONDS = 60

print("=" * 65)
print("FIX MISSING GRIDS - AUTO LOOP MODE")
print("=" * 65)

grid_df = pd.read_csv(GRID_FILE)
if "cell_type" in grid_df.columns:
    grid_df = grid_df[grid_df["cell_type"].isin(["land", "coastal"])].copy()
grid_df = grid_df.reset_index(drop=True)

while True:

    if os.path.exists(OUTPUT_RAW):
        raw_results   = pd.read_csv(OUTPUT_RAW)
        fetched_grids = set(raw_results["grid_id"].unique())
    else:
        raw_results   = pd.DataFrame()
        fetched_grids = set()

    pending = grid_df[~grid_df["grid_id"].isin(fetched_grids)].reset_index(drop=True)

    print(f"\nTotal grids   : {len(grid_df)}")
    print(f"Already done  : {len(fetched_grids)}")
    print(f"Still missing : {len(pending)}")

    if len(pending) == 0:
        print("\n🎉 All 721 grids fetched! Moving to correction step...")
        break

    batch    = pending.iloc[:BATCH_SIZE]
    lats     = batch["centroid_lat"].tolist()
    lons     = batch["centroid_lon"].tolist()
    grid_ids = batch["grid_id"].tolist()

    print(f"\nFetching next {len(batch)} grids...")

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":   lats,
        "longitude":  lons,
        "start_date": "2010-01-01",
        "end_date":   "2025-12-31",
        "daily":      ["temperature_2m_mean", "precipitation_sum"],
        "timezone":   "auto"
    }

    response = requests.get(url, params=params, timeout=120)

    if response.status_code == 429:
        print(f"Rate limited - waiting {DELAY_SECONDS}s then retrying...")
        time.sleep(DELAY_SECONDS)
        continue

    if response.status_code != 200:
        print(f"HTTP {response.status_code} error - waiting {DELAY_SECONDS}s then retrying...")
        time.sleep(DELAY_SECONDS)
        continue

    results = response.json()
    if isinstance(results, dict):
        results = [results]

    all_rows = []
    for i, data in enumerate(results):
        df = pd.DataFrame({
            "date":         pd.to_datetime(data["daily"]["time"]),
            "temp_om_C":    data["daily"]["temperature_2m_mean"],
            "precip_om_mm": data["daily"]["precipitation_sum"]
        })
        df["year"]  = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df_m = df.groupby(["year", "month"]).agg(
            temp_om_C    = ("temp_om_C",    "mean"),
            precip_om_mm = ("precip_om_mm", "sum")
        ).reset_index()
        df_m["grid_id"]   = grid_ids[i]
        df_m["latitude"]  = lats[i]
        df_m["longitude"] = lons[i]
        df_m["elevation"] = data.get("elevation", 0)
        all_rows.append(df_m)

    new_data    = pd.concat(all_rows, ignore_index=True)
    raw_results = pd.concat([raw_results, new_data], ignore_index=True)
    raw_results.to_csv(OUTPUT_RAW, index=False)

    done_now = len(fetched_grids) + len(batch)
    print(f"Done! {done_now}/{len(grid_df)} grids fetched")
    print(f"Remaining: {len(pending) - len(batch)} grids")
    print(f"Waiting {DELAY_SECONDS}s before next batch...")
    time.sleep(DELAY_SECONDS)

# ─── APPLY CORRECTION MODELS ──────────────────────────────────────
print("\n" + "-" * 65)
print("Applying Phase 0 Correction Models...")

temp_bundle = joblib.load(os.path.join(MODELS_DIR, "model_temperature.pkl"))
rf_bundle   = joblib.load(os.path.join(MODELS_DIR, "model_rainfall.pkl"))

corrected_df = raw_results.dropna(subset=["temp_om_C", "precip_om_mm"]).copy()

corrected_df["temp_corrected_C"] = temp_bundle["model"].predict(
    corrected_df[temp_bundle["features"]]
)

X_rf = corrected_df[rf_bundle["features"]].copy()
X_rf["precip_om_mm"] = np.log1p(X_rf["precip_om_mm"].clip(0))
corrected_df["precip_corrected_mm"] = np.expm1(
    rf_bundle["model"].predict(X_rf)
).clip(0)

final_cols = [
    "grid_id", "latitude", "longitude", "elevation",
    "year", "month",
    "temp_om_C",    "temp_corrected_C",
    "precip_om_mm", "precip_corrected_mm"
]
corrected_df[final_cols].sort_values(
    ["grid_id", "year", "month"]
).to_csv(OUTPUT_CORRECTED, index=False)

print(f"Grids corrected : {corrected_df['grid_id'].nunique()}")
print(f"Total rows      : {len(corrected_df):,}")
print(f"Year range      : {corrected_df['year'].min()} - {corrected_df['year'].max()}")
print(f"Raw       : {OUTPUT_RAW}")
print(f"Corrected : {OUTPUT_CORRECTED}")
print("=" * 65)
print(f"PROGRESS: {corrected_df['grid_id'].nunique()}/{len(grid_df)} grids complete")
print("=" * 65)