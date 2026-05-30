"""
Phase 0 — Step 6: Validate 2025 Predictions
  - Load saved correction models
  - Apply to 2025 OpenMeteo data
  - Compare predicted vs actual observed values
  - Output: validation_2025.csv + printed metrics per station
"""

import pandas as pd
import numpy as np
import os
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ─── PATHS ────────────────────────────────────────────────────────
INPUT_FILE   = "../../data/gold/merged_openmeteo_vs_observed.csv"
MODELS_DIR   = "../../data/gold/models"
OUTPUT_FILE  = "../../data/gold/validation_2025.csv"

# ─── LOAD DATA ────────────────────────────────────────────────────
df = pd.read_csv(INPUT_FILE)
df_2025 = df[df["year"] == 2025].copy()
print(f"📂 2025 rows loaded: {len(df_2025):,} | {df_2025['station_name'].nunique()} stations")

# ─── LOAD MODELS ──────────────────────────────────────────────────
temp_bundle = joblib.load(os.path.join(MODELS_DIR, "model_temperature.pkl"))
rf_bundle   = joblib.load(os.path.join(MODELS_DIR, "model_rainfall.pkl"))

# ─── APPLY TEMPERATURE MODEL ──────────────────────────────────────
temp_features = temp_bundle["features"]
X_temp = df_2025[temp_features].copy()

df_2025["temp_predicted_C"]  = temp_bundle["model"].predict(X_temp)
df_2025["temp_actual_C"]     = df_2025["temp_mean_obs_C"]
df_2025["temp_raw_om_C"]     = df_2025["temp_om_C"]
df_2025["temp_error_C"]      = df_2025["temp_predicted_C"] - df_2025["temp_actual_C"]

# ─── APPLY RAINFALL MODEL ─────────────────────────────────────────
rf_features = rf_bundle["features"]
X_rf = df_2025[rf_features].copy()
X_rf["precip_om_mm"] = np.log1p(X_rf["precip_om_mm"].clip(lower=0))

log_pred = rf_bundle["model"].predict(X_rf)
df_2025["precip_predicted_mm"] = np.expm1(log_pred)
df_2025["precip_actual_mm"]    = df_2025["precip_obs_mm"]
df_2025["precip_raw_om_mm"]    = df_2025["precip_om_mm"]
df_2025["precip_error_mm"]     = df_2025["precip_predicted_mm"] - df_2025["precip_actual_mm"]

# ─── OVERALL METRICS ──────────────────────────────────────────────
print("\n" + "=" * 65)
print("OVERALL 2025 VALIDATION METRICS")
print("=" * 65)

for label, actual_col, pred_col, raw_col in [
    ("Temperature (°C)", "temp_actual_C",    "temp_predicted_C",    "temp_raw_om_C"),
    ("Rainfall    (mm)", "precip_actual_mm", "precip_predicted_mm", "precip_raw_om_mm"),
]:
    sub = df_2025[[actual_col, pred_col, raw_col]].dropna()

    r2_corrected  = r2_score(sub[actual_col], sub[pred_col])
    mae_corrected = mean_absolute_error(sub[actual_col], sub[pred_col])

    r2_raw  = r2_score(sub[actual_col], sub[raw_col])
    mae_raw = mean_absolute_error(sub[actual_col], sub[raw_col])

    print(f"\n  {label}")
    print(f"  {'':4s}{'':20s}  {'R²':>8}  {'MAE':>10}")
    print(f"  {'':4s}{'Raw OpenMeteo':20s}  {r2_raw:8.4f}  {mae_raw:10.4f}")
    print(f"  {'':4s}{'After Correction':20s}  {r2_corrected:8.4f}  {mae_corrected:10.4f}")

# ─── PER-STATION METRICS ──────────────────────────────────────────
print("\n" + "=" * 65)
print("PER-STATION 2025 METRICS — TEMPERATURE")
print("=" * 65)
print(f"  {'Station':<20} {'Actual Mean':>12} {'Predicted':>12} {'MAE':>8} {'R²':>8}")
print("  " + "-" * 62)

for station, grp in df_2025.groupby("station_name"):
    sub = grp[["temp_actual_C", "temp_predicted_C"]].dropna()
    if len(sub) < 2:
        continue
    mae = mean_absolute_error(sub["temp_actual_C"], sub["temp_predicted_C"])
    r2  = r2_score(sub["temp_actual_C"], sub["temp_predicted_C"]) if len(sub) > 2 else float("nan")
    print(f"  {station:<20} {sub['temp_actual_C'].mean():12.2f} "
          f"{sub['temp_predicted_C'].mean():12.2f} {mae:8.4f} {r2:8.4f}")

print("\n" + "=" * 65)
print("PER-STATION 2025 METRICS — RAINFALL")
print("=" * 65)
print(f"  {'Station':<20} {'Actual Mean':>12} {'Predicted':>12} {'MAE':>10} {'R²':>8}")
print("  " + "-" * 64) 

for station, grp in df_2025.groupby("station_name"):
    sub = grp[["precip_actual_mm", "precip_predicted_mm"]].dropna()
    if len(sub) < 2:
        continue
    mae = mean_absolute_error(sub["precip_actual_mm"], sub["precip_predicted_mm"])
    r2  = r2_score(sub["precip_actual_mm"], sub["precip_predicted_mm"]) if len(sub) > 2 else float("nan")
    print(f"  {station:<20} {sub['precip_actual_mm'].mean():12.2f} "
          f"{sub['precip_predicted_mm'].mean():12.2f} {mae:10.4f} {r2:8.4f}")

# ─── SAVE OUTPUT ──────────────────────────────────────────────────
output_cols = [
    "station_name", "year", "month",
    "temp_actual_C", "temp_raw_om_C", "temp_predicted_C", "temp_error_C",
    "precip_actual_mm", "precip_raw_om_mm", "precip_predicted_mm", "precip_error_mm"
]
df_2025[output_cols].to_csv(OUTPUT_FILE, index=False)

print(f"\n✅ Saved: {OUTPUT_FILE}")
print("   Columns: station | month | actual | raw_om | predicted | error")
