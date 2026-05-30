"""
Phase 1: Generate Corrected Grid Data — BATCH VERSION
  - Fetches up to 100 locations per API call (721 grids = ~8 requests)
  - Much faster, avoids rate limiting
"""

import os
import pandas as pd
import numpy as np
import joblib
import time
import requests

os.chdir(os.path.dirname(os.path.abspath(__file__)))

GRID_FILE        = "../../data/bronze/metadata/grid_coordinates_all.csv"
MODELS_DIR       = "../../data/gold/models"
OUTPUT_RAW       = "../../data/silver/grid_weather_raw_2010_2025.csv"
OUTPUT_CORRECTED = "../../data/gold/grid_weather_corrected_2010_2025.csv"

os.makedirs("../../data/silver", exist_ok=True)
os.makedirs("../../data/gold",   exist_ok=True)

BATCH_SIZE = 100  # max locations per API call

def fetch_batch(lats, lons, grid_ids):
    """Fetch multiple locations in one API call."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":   lats,
        "longitude":  lons,
        "start_date": "2010-01-01",
        "end_date":   "2025-12-31",
        "daily":      ["temperature_2m_mean", "precipitation_sum"],
        "timezone":   "auto"
    }
    try:
        response = requests.get(url, params=params, timeout=120)

        if response.status_code == 429:
            print(f"  ⏳ Rate limited — waiting 120s...")
            time.sleep(120)
            return None

        if response.status_code != 200:
            print(f"  ❌ HTTP {response.status_code}")
            return None

        results = response.json()

        # If single location, API returns dict not list
        if isinstance(results, dict):
            results = [results]

        all_rows = []
        for i, data in enumerate(results):
            elevation = data.get("elevation", 0)
            grid_id   = grid_ids[i]
            lat       = lats[i]
            lon       = lons[i]

            df = pd.DataFrame({
                "date":         pd.to_datetime(data["daily"]["time"]),
                "temp_om_C":    data["daily"]["temperature_2m_mean"],
                "precip_om_mm": data["daily"]["precipitation_sum"]
            })
            df["year"]      = df["date"].dt.year
            df["month"]     = df["date"].dt.month
            df_m = df.groupby(["year","month"]).agg(
                temp_om_C    = ("temp_om_C",    "mean"),
                precip_om_mm = ("precip_om_mm", "sum")
            ).reset_index()

            df_m["grid_id"]   = grid_id
            df_m["latitude"]  = lat
            df_m["longitude"] = lon
            df_m["elevation"] = elevation
            all_rows.append(df_m)

        return pd.concat(all_rows, ignore_index=True)

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


# ─── LOAD GRID ────────────────────────────────────────────────────
print("=" * 65)
print("PHASE 1: GRID DATA FETCH & CORRECTION (BATCH MODE)")
print("=" * 65)

grid_df = pd.read_csv(GRID_FILE)
if "cell_type" in grid_df.columns:
    grid_df = grid_df[grid_df["cell_type"].isin(["land", "coastal"])].copy()
grid_df = grid_df.reset_index(drop=True)
print(f"\n📍 Total grid cells : {len(grid_df)}")

# ─── RESUME ───────────────────────────────────────────────────────
if os.path.exists(OUTPUT_RAW):
    raw_results   = pd.read_csv(OUTPUT_RAW)
    fetched_grids = set(raw_results["grid_id"].unique())
    print(f"📥 Already fetched  : {len(fetched_grids)} grids")
else:
    raw_results   = pd.DataFrame()
    fetched_grids = set()

pending = grid_df[~grid_df["grid_id"].isin(fetched_grids)].reset_index(drop=True)
print(f"⏳ Remaining        : {len(pending)} grids")
print(f"📦 Batch size       : {BATCH_SIZE} locations per request")
print(f"🔢 Total batches    : {int(np.ceil(len(pending)/BATCH_SIZE))}\n")

# ─── BATCH FETCH LOOP ─────────────────────────────────────────────
all_new = []
total_batches = int(np.ceil(len(pending) / BATCH_SIZE))

for batch_num in range(total_batches):
    start = batch_num * BATCH_SIZE
    end   = min(start + BATCH_SIZE, len(pending))
    batch = pending.iloc[start:end]

    lats     = batch["centroid_lat"].tolist()
    lons     = batch["centroid_lon"].tolist()
    grid_ids = batch["grid_id"].tolist()

    print(f"  📦 Batch {batch_num+1}/{total_batches} "
          f"(grids {start+1}–{end}) ...", end=" ", flush=True)

    df_batch = fetch_batch(lats, lons, grid_ids)

    if df_batch is not None:
        all_new.append(df_batch)
        print(f"✅  ({len(df_batch):,} rows)")
    else:
        print(f"⚠️  failed — will need fix_missing_grids.py later")

    # Save after every batch
    if all_new:
        raw_results = pd.concat([raw_results] + all_new, ignore_index=True)
        raw_results.to_csv(OUTPUT_RAW, index=False)
        all_new = []
        print(f"     💾 Saved progress\n")

    time.sleep(15)  # polite delay between batches

print(f"\n💾 Raw data saved : {len(raw_results):,} rows | "
      f"{raw_results['grid_id'].nunique()} grids")

