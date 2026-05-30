"""
Phase 0 — Step 4: Merge Open-Meteo vs Met Observations
Output: data/gold/merged_openmeteo_vs_observed.csv
"""

import pandas as pd
import numpy as np
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ─── FILE PATHS ───────────────────────────────────────────────────
OBS_FILE    = "../../data/silver/met_observations_monthly.csv"
OM_FILE     = "../../data/silver/openmeteo_24_stations_monthly.csv"
OUTPUT_FILE = "../../data/gold/merged_openmeteo_vs_observed.csv"

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

print("=" * 65)
print("PHASE 0 — STEP 4: Merge Open-Meteo vs Observed")
print("=" * 65)

# ─── LOAD ─────────────────────────────────────────────────────────
obs = pd.read_csv(OBS_FILE)
om  = pd.read_csv(OM_FILE)

print(f"\n📂 Observed data : {len(obs):,} rows | {obs['station_name'].nunique()} stations")
print(f"📂 Open-Meteo    : {len(om):,} rows  | {om['station'].nunique()} stations")

# ─── STANDARDISE STATION NAMES ────────────────────────────────────
obs["station_name"] = obs["station_name"].str.upper().str.strip()
om["station"]       = om["station"].str.upper().str.strip()
om = om.rename(columns={"station": "station_name"})

obs["year"]  = obs["year"].astype(int)
obs["month"] = obs["month"].astype(int)
om["year"]   = om["year"].astype(int)
om["month"]  = om["month"].astype(int)

# ─── SUNSHINE STATION MAPPING ─────────────────────────────────────
# Map 15 PUCSL sunshine station names → closest of 24 met stations
SUNSHINE_STATION_MAP = {
    "AGALAWATTA"       : "RATNAPURA",
    "GIRADURUKOTTE"    : "POLONNARUWA",
    "KOTTAWA"          : "COLOMBO",
    "SEETHAELIYA"      : "NUWARA_ELIYA",
    "WEERAWILA"        : "HAMBANTOTA",
    "BATHALEGODA"      : "KURUNEGALA",
    "DENIYAYA"         : "GALLE",
    "MAHAILLUPPALLAMA" : "MAHA_ILLUPPALLAMA",
    "RATHMALAGARA"     : "POLONNARUWA",
    "JAFFANA"          : "JAFFNA",           # typo in original data
    "GANNORUWA"        : "KATUGASTOTA",
    "COLOMBO"          : "COLOMBO",
    "POLONNARUWA"      : "POLONNARUWA",
    "MONARAGALA"       : "MONARAGALA",
    "RATNAPURA"        : "RATNAPURA",
}

# Extract sunshine rows, apply mapping, average duplicates
if "sunshine_sum_obs_hrs" in obs.columns:
    sun_obs = obs[["station_name","year","month","sunshine_sum_obs_hrs"]].dropna(
        subset=["sunshine_sum_obs_hrs"]
    ).copy()

    sun_obs["station_name"] = sun_obs["station_name"].replace(SUNSHINE_STATION_MAP)

    # Average where two PUCSL stations map to same met station
    # (e.g. COLOMBO gets Colombo + Kottawa averaged)
    # (e.g. POLONNARUWA gets Giradurukotte + Rathmalagara averaged)
    sun_obs = sun_obs.groupby(
        ["station_name","year","month"], as_index=False
    )["sunshine_sum_obs_hrs"].mean()

    # Remove sunshine from main obs and re-attach the mapped version
    obs = obs.drop(columns=["sunshine_sum_obs_hrs"]).merge(
        sun_obs,
        on=["station_name","year","month"],
        how="left"
    )

    print(f"\n   Sunshine rows after mapping : {obs['sunshine_sum_obs_hrs'].notna().sum():,}")
    print(f"   Stations with sunshine      : {obs.dropna(subset=['sunshine_sum_obs_hrs'])['station_name'].nunique()}")

# ─── MERGE ────────────────────────────────────────────────────────
merged = obs.merge(
    om[["station_name","year","month",
        "temp_mean_C","precip_sum_mm","wind_mean_ms","sunshine_sum_hrs"]],
    on=["station_name","year","month"],
    how="inner",
    suffixes=("_obs","_om")
)

print(f"\n✅ Merged rows   : {len(merged):,}")
print(f"✅ Stations       : {merged['station_name'].nunique()}")
print(f"✅ Year range     : {merged['year'].min()} – {merged['year'].max()}")

# ─── RENAME FOR CLARITY ───────────────────────────────────────────
merged = merged.rename(columns={
    "temp_mean_C":      "temp_om_C",
    "precip_sum_mm":    "precip_om_mm",
    "wind_mean_ms":     "wind_om_ms",
    "sunshine_sum_hrs": "sunshine_om_hrs",
})

# Convert Open-Meteo wind from km/h → m/s
merged["wind_om_ms"] = merged["wind_om_ms"] / 3.6

# ─── COMPUTE BIAS ─────────────────────────────────────────────────
merged["temp_bias_C"]       = merged["temp_mean_obs_C"]      - merged["temp_om_C"]
merged["precip_bias_mm"]    = merged["precip_obs_mm"]        - merged["precip_om_mm"]
merged["wind_bias_ms"]      = merged["wind_obs_ms"]          - merged["wind_om_ms"]
merged["sunshine_bias_hrs"] = merged["sunshine_sum_obs_hrs"] - merged["sunshine_om_hrs"]

merged.to_csv(OUTPUT_FILE, index=False)

# ─── BIAS SUMMARY ─────────────────────────────────────────────────
print("\n" + "=" * 65)
print("BIAS SUMMARY (Observed − Open-Meteo)")
print("=" * 65)

for var, bias_col, unit in [
    ("Temperature",    "temp_bias_C",       "°C"),
    ("Rainfall",       "precip_bias_mm",    "mm"),
    ("Wind Speed",     "wind_bias_ms",      "m/s"),
    ("Sunshine Hours", "sunshine_bias_hrs", "hrs"),
]:
    col = merged[bias_col].dropna()
    if len(col) > 0:
        print(f"\n  {var}:")
        print(f"    Mean bias : {col.mean():+.3f} {unit}  ({'OM overestimates' if col.mean() < 0 else 'OM underestimates'})")
        print(f"    MAE       : {col.abs().mean():.3f} {unit}")
        print(f"    RMSE      : {np.sqrt((col**2).mean()):.3f} {unit}")
        print(f"    Min / Max : {col.min():.3f} / {col.max():.3f} {unit}")
    else:
        print(f"\n  {var}: ⚠️  No overlapping data")

print(f"\n📁 Saved to: {OUTPUT_FILE}")
print("\n📋 Next step: Build correction equations (Phase 0 Step 5)")
