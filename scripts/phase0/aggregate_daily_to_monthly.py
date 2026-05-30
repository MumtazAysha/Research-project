"""
Aggregation Script: Daily → Monthly CSV
24 Sri Lanka Met Stations | 2010-2025
Output: One combined monthly CSV for all 24 stations
"""

import pandas as pd
import os
import glob

# ─── Settings ─────────────────────────────────────────────────────────────────
os.chdir(os.path.dirname(os.path.abspath(__file__)))

INPUT_FOLDER  = "openmeteo_24_stations"
OUTPUT_FILE   = "openmeteo_24_stations_monthly.csv"

# ─── Aggregation Rules ────────────────────────────────────────────────────────
# Temperature  → monthly MEAN
# Rainfall     → monthly SUM
# Wind Speed   → monthly MEAN
# Sunshine     → monthly SUM (total hours/month)

AGG_RULES = {
    "temp_mean_C":  "mean",
    "precip_mm":    "sum",
    "wind_max_ms":  "mean",
    "sunshine_hrs": "sum"
}

# ─── Load & Aggregate All Stations ────────────────────────────────────────────
all_files = sorted(glob.glob(os.path.join(INPUT_FOLDER, "*_daily.csv")))

print("=" * 65)
print("AGGREGATION: Daily → Monthly | 24 Stations")
print("=" * 65)
print(f"Found {len(all_files)} station files\n")

monthly_frames = []

for i, filepath in enumerate(all_files, 1):
    station_name = os.path.basename(filepath).replace("_daily.csv", "")

    df = pd.read_csv(filepath, parse_dates=["date"])

    # Add year-month period column
    df["year"]  = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # Aggregate
    monthly = df.groupby(["station", "latitude", "longitude", "year", "month"]).agg(AGG_RULES).reset_index()

    # Rename for clarity
    monthly.rename(columns={
        "temp_mean_C":  "temp_mean_C",
        "precip_mm":    "precip_sum_mm",
        "wind_max_ms":  "wind_mean_ms",
        "sunshine_hrs": "sunshine_sum_hrs"
    }, inplace=True)

    monthly_frames.append(monthly)
    print(f"[{i:02d}/24] ✅ {station_name:25s} → {len(monthly)} months aggregated")

# ─── Combine & Save ───────────────────────────────────────────────────────────
combined = pd.concat(monthly_frames, ignore_index=True)
combined.sort_values(["station", "year", "month"], inplace=True)
combined.reset_index(drop=True, inplace=True)

combined.to_csv(OUTPUT_FILE, index=False)

# ─── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("AGGREGATION COMPLETE")
print("=" * 65)
print(f"\n✅ Total rows     : {len(combined):,}")
print(f"✅ Stations       : {combined['station'].nunique()}")
print(f"✅ Year range     : {combined['year'].min()} – {combined['year'].max()}")
print(f"✅ Months covered : {combined['month'].nunique()} (Jan–Dec)")
print(f"📁 Saved to       : {OUTPUT_FILE}")
print("\n📋 Columns in output CSV:")
for col in combined.columns:
    print(f"   - {col}")
print("\n📋 Next step:")
print("   Merge with actual Met station observations for error correction")