"""
Phase 0 — Step 5: Build Correction Equations
  - Temperature  : Linear Regression
  - Rainfall     : Log-linear Regression

Independent variables: OM_value, latitude, longitude, elevation, month
Train : 19 stations | 2010–2024
Spatial  test : 5 held-out stations (all years)
Temporal test : All 24 stations | 2025 only
Output: correction_equations_summary.txt + saved models
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score
import joblib

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ─── PATHS ────────────────────────────────────────────────────────
INPUT_FILE   = "../../data/gold/merged_openmeteo_vs_observed.csv"
MODELS_DIR   = "../../data/gold/models"
SUMMARY_FILE = "../../data/gold/correction_equations_summary.txt"

os.makedirs(MODELS_DIR, exist_ok=True)

print("=" * 65)
print("PHASE 0 — STEP 5: Building Correction Equations")
print("=" * 65)

df = pd.read_csv(INPUT_FILE)
print(f"\n📂 Loaded: {len(df):,} rows | {df['station_name'].nunique()} stations")
print(f"   Year range : {df['year'].min()} – {df['year'].max()}")

# ─── SPLITS ───────────────────────────────────────────────────────
TEST_STATIONS = [
    "JAFFNA",        # North
    "BATTICALOA",    # East
    "HAMBANTOTA",    # South
    "COLOMBO",       # West
    "NUWARA_ELIYA",  # Central highlands
]

# Spatial split
train_df         = df[~df["station_name"].isin(TEST_STATIONS)].copy()
test_spatial_df  = df[ df["station_name"].isin(TEST_STATIONS)].copy()

# ✅ Temporal split — exclude 2025 from training
train_df         = train_df[train_df["year"] <= 2024].copy()
test_temporal_df = df[df["year"] == 2025].copy()   # all 24 stations, 2025 only

print(f"\n   Train          : {train_df['station_name'].nunique()} stations | "
      f"years {train_df['year'].min()}–{train_df['year'].max()} | {len(train_df):,} rows")
print(f"   Spatial test   : {test_spatial_df['station_name'].nunique()} stations | {len(test_spatial_df):,} rows")
print(f"   Temporal test  : all stations | year 2025 | {len(test_temporal_df):,} rows")

FEATURES = ["latitude", "longitude", "elevation", "month"]

# ─── MODELS (Temperature & Rainfall only) ─────────────────────────
# (label, om_col, obs_col, use_log)
MODELS = [
    ("Temperature", "temp_om_C",    "temp_mean_obs_C", False),
    ("Rainfall",    "precip_om_mm", "precip_obs_mm",   True),
]

summary_lines = []
summary_lines.append("=" * 65)
summary_lines.append("CORRECTION EQUATIONS SUMMARY")
summary_lines.append("Sri Lanka — 24 Met Stations")
summary_lines.append("Train: 19 stations | 2010–2024")
summary_lines.append("Spatial test : 5 stations | 2010–2024")
summary_lines.append("Temporal test: 24 stations | 2025")
summary_lines.append("=" * 65)

print("\n" + "─" * 65)

for label, om_col, obs_col, use_log in MODELS:
    print(f"\n📐 Building: {label}")

    cols_needed = FEATURES + [om_col, obs_col, "year", "station_name"]
    feature_names = FEATURES + [om_col]

    train_sub        = train_df[cols_needed].dropna().copy()
    test_spatial_sub = test_spatial_df[cols_needed].dropna().copy()
    test_temp_sub    = test_temporal_df[cols_needed].dropna().copy()

    print(f"   Training samples        : {len(train_sub):,}")
    print(f"   Spatial test samples    : {len(test_spatial_sub):,}")
    print(f"   Temporal test samples   : {len(test_temp_sub):,}")

    if len(train_sub) < 10:
        print(f"   ⚠️  Not enough training data — skipping")
        continue

    X_train          = train_sub[feature_names].copy()
    X_test_spatial   = test_spatial_sub[feature_names].copy()
    X_test_temporal  = test_temp_sub[feature_names].copy()

    if use_log:
        y_train         = np.log1p(train_sub[obs_col].clip(lower=0))
        y_test_spatial  = np.log1p(test_spatial_sub[obs_col].clip(lower=0))
        y_test_temporal = np.log1p(test_temp_sub[obs_col].clip(lower=0))
        X_train[om_col]         = np.log1p(X_train[om_col].clip(lower=0))
        X_test_spatial[om_col]  = np.log1p(X_test_spatial[om_col].clip(lower=0))
        X_test_temporal[om_col] = np.log1p(X_test_temporal[om_col].clip(lower=0))
    else:
        y_train         = train_sub[obs_col]
        y_test_spatial  = test_spatial_sub[obs_col]
        y_test_temporal = test_temp_sub[obs_col]

    # ─── Train ────────────────────────────────────────────────────
    model = LinearRegression()
    model.fit(X_train, y_train)
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="r2")

    # ─── Evaluate: Spatial test ───────────────────────────────────
    y_pred_spatial = model.predict(X_test_spatial)
    if use_log:
        y_eval_spatial      = np.expm1(y_test_spatial)
        y_pred_spatial_bt   = np.expm1(y_pred_spatial)
    else:
        y_eval_spatial      = y_test_spatial
        y_pred_spatial_bt   = y_pred_spatial

    mae_s  = mean_absolute_error(y_eval_spatial, y_pred_spatial_bt)
    rmse_s = np.sqrt(mean_squared_error(y_eval_spatial, y_pred_spatial_bt))
    r2_s   = r2_score(y_eval_spatial, y_pred_spatial_bt)

    # ─── Evaluate: Temporal test (2025) ───────────────────────────
    y_pred_temporal = model.predict(X_test_temporal)
    if use_log:
        y_eval_temporal     = np.expm1(y_test_temporal)
        y_pred_temporal_bt  = np.expm1(y_pred_temporal)
    else:
        y_eval_temporal     = y_test_temporal
        y_pred_temporal_bt  = y_pred_temporal

    mae_t  = mean_absolute_error(y_eval_temporal, y_pred_temporal_bt)
    rmse_t = np.sqrt(mean_squared_error(y_eval_temporal, y_pred_temporal_bt))
    r2_t   = r2_score(y_eval_temporal, y_pred_temporal_bt)

    # ─── Print results ────────────────────────────────────────────
    print(f"\n   Train CV R²         : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"\n   📍 Spatial  Test R² : {r2_s:.4f}  |  MAE: {mae_s:.4f}  |  RMSE: {rmse_s:.4f}")
    print(f"   📅 Temporal Test R² : {r2_t:.4f}  |  MAE: {mae_t:.4f}  |  RMSE: {rmse_t:.4f}")

    # ─── Print equation ───────────────────────────────────────────
    transform     = "log(" if use_log else ""
    transform_end = "+1)"  if use_log else ""
    coefs = dict(zip(feature_names, model.coef_))

    print(f"\n   Equation:")
    print(f"   {transform}{obs_col}{transform_end} =")
    print(f"     {model.intercept_:.6f}")
    for fname, coef in coefs.items():
        print(f"     + ({coef:.6f}) × {fname}")

    # ─── Save model ───────────────────────────────────────────────
    model_path = os.path.join(MODELS_DIR, f"model_{label.replace(' ','_').lower()}.pkl")
    joblib.dump({
        "model":      model,
        "features":   feature_names,
        "use_log":    use_log,
        "om_col":     om_col,
        "obs_col":    obs_col,
        "model_type": "Linear",
        "train_years": "2010-2024",
        "train_stations": "19 (excl. 5 test stations)"
    }, model_path)
    print(f"\n   💾 Model saved: {model_path}")

    # ─── Summary lines ────────────────────────────────────────────
    summary_lines.append(f"\n{'─'*65}")
    summary_lines.append(f"VARIABLE: {label}")
    summary_lines.append(f"{'─'*65}")
    summary_lines.append(f"Model type       : Linear Regression")
    summary_lines.append(f"Log transform    : {'Yes (log1p/expm1)' if use_log else 'No'}")
    summary_lines.append(f"Training rows    : {len(train_sub):,}")
    summary_lines.append(f"Train CV R2      : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    summary_lines.append(f"Spatial  Test R2 : {r2_s:.4f}  |  MAE: {mae_s:.4f}  |  RMSE: {rmse_s:.4f}")
    summary_lines.append(f"Temporal Test R2 : {r2_t:.4f}  |  MAE: {mae_t:.4f}  |  RMSE: {rmse_t:.4f}")
    summary_lines.append(f"\nEquation:")
    summary_lines.append(f"  {transform}{obs_col}{transform_end} =")
    summary_lines.append(f"    intercept : {model.intercept_:.6f}")
    for fname, coef in coefs.items():
        summary_lines.append(f"    {fname:20s}: {coef:+.6f}")

with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(summary_lines))

print("\n" + "=" * 65)
print("ALL CORRECTION EQUATIONS BUILT")
print("=" * 65)
print(f"\n📁 Summary : {SUMMARY_FILE}")
print(f"📁 Models  : {MODELS_DIR}/")
print("\n📋 Next step: Apply correction equations to any Sri Lanka location")
