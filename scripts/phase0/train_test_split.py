import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os

print("="*80)
print("STEP 4: TRAIN SOLAR RADIATION PREDICTION MODEL")
print("="*80)

# Load engineered features
station = "43415"
df = pd.read_csv(f'data/processed/solar_features_{station}_2019_2025.csv')
df['date'] = pd.to_datetime(df['date'])

print(f"📥 Loaded {len(df):,} records with {len(df.columns)-2} features\n")

# ============================================================================
# 1. TEMPORAL TRAIN/TEST SPLIT (Important for time series!)
# ============================================================================
print("📅 Splitting data temporally...")

# Train: 2019-2023 (5 years)
# Test: 2024 (1 year)  
# Validation: 2025 (1 year)

train_df = df[df['date'] < '2024-01-01'].copy()
test_df = df[(df['date'] >= '2024-01-01') & (df['date'] < '2025-01-01')].copy()
val_df = df[df['date'] >= '2025-01-01'].copy()

print(f"   📚 Train: {len(train_df):,} days (2019-2023)")
print(f"   🧪 Test: {len(test_df):,} days (2024)")
print(f"   ✅ Validation: {len(val_df):,} days (2025)")

# ============================================================================
# 2. PREPARE FEATURES & TARGET
# ============================================================================
print("\n🎯 Preparing features and target...")

# Remove non-feature columns
feature_cols = [col for col in df.columns if col not in ['date', 'solar_radiation']]

X_train = train_df[feature_cols]
y_train = train_df['solar_radiation']

X_test = test_df[feature_cols]
y_test = test_df['solar_radiation']

X_val = val_df[feature_cols]
y_val = val_df['solar_radiation']

print(f"   Features: {len(feature_cols)}")
print(f"   Target: solar_radiation (kWh/m²/day)")

# ============================================================================
# 3. TRAIN RANDOM FOREST MODEL
# ============================================================================
print("\n🌲 Training Random Forest model...")

model = RandomForestRegressor(
    n_estimators=100,        # Number of trees
    max_depth=15,            # Prevent overfitting
    min_samples_split=10,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1,               # Use all CPU cores
    verbose=1
)

model.fit(X_train, y_train)

print(f"\n✅ Model trained!")

# ============================================================================
# 4. EVALUATE ON TEST SET (2024)
# ============================================================================
print("\n📊 EVALUATING ON 2024 TEST DATA...")

y_pred_test = model.predict(X_test)

rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
mae_test = mean_absolute_error(y_test, y_pred_test)
r2_test = r2_score(y_test, y_pred_test)

print(f"\n   RMSE: {rmse_test:.4f} kWh/m²/day")
print(f"   MAE:  {mae_test:.4f} kWh/m²/day")
print(f"   R²:   {r2_test:.4f}")

# ============================================================================
# 5. EVALUATE ON VALIDATION SET (2025)
# ============================================================================
print("\n📊 EVALUATING ON 2025 VALIDATION DATA...")

y_pred_val = model.predict(X_val)

rmse_val = np.sqrt(mean_squared_error(y_val, y_pred_val))
mae_val = mean_absolute_error(y_val, y_pred_val)
r2_val = r2_score(y_val, y_pred_val)

print(f"\n   RMSE: {rmse_val:.4f} kWh/m²/day")
print(f"   MAE:  {mae_val:.4f} kWh/m²/day")
print(f"   R²:   {r2_val:.4f}")

# ============================================================================
# 6. FEATURE IMPORTANCE
# ============================================================================
print("\n🔍 TOP 10 MOST IMPORTANT FEATURES:")

feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(feature_importance.head(10).to_string(index=False))

# ============================================================================
# 7. SAMPLE PREDICTIONS vs ACTUAL
# ============================================================================
print("\n📋 SAMPLE PREDICTIONS (2025 - First 10 days):")

results_df = val_df[['date', 'solar_radiation']].copy()
results_df['predicted'] = y_pred_val
results_df['error'] = results_df['solar_radiation'] - results_df['predicted']
results_df['error_pct'] = (results_df['error'] / results_df['solar_radiation'] * 100).abs()

print(results_df[['date', 'solar_radiation', 'predicted', 'error', 'error_pct']].head(10).to_string(index=False))

# ============================================================================
# 8. SAVE MODEL & RESULTS
# ============================================================================
print("\n💾 Saving model and results...")

# Save trained model
model_dir = 'models'
os.makedirs(model_dir, exist_ok=True)
model_path = f'{model_dir}/solar_model_{station}.pkl'
joblib.dump(model, model_path)
print(f"   ✅ Model saved to: {model_path}")

# Save feature list (needed for predictions)
feature_list_path = f'{model_dir}/feature_list_{station}.txt'
with open(feature_list_path, 'w') as f:
    f.write('\n'.join(feature_cols))
print(f"   ✅ Feature list saved to: {feature_list_path}")

# Save feature importance
importance_path = f'data/processed/feature_importance_{station}.csv'
feature_importance.to_csv(importance_path, index=False)
print(f"   ✅ Feature importance saved to: {importance_path}")

# Save predictions
predictions_path = f'data/processed/predictions_{station}_2025.csv'
results_df.to_csv(predictions_path, index=False)
print(f"   ✅ Predictions saved to: {predictions_path}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("✅ MODEL TRAINING COMPLETE!")
print("="*80)
print(f"\n📊 PERFORMANCE SUMMARY:")
print(f"   Test 2024:  R² = {r2_test:.4f}, RMSE = {rmse_test:.4f} kWh/m²/day")
print(f"   Val 2025:   R² = {r2_val:.4f}, RMSE = {rmse_val:.4f} kWh/m²/day")

print(f"\n💡 INTERPRETATION:")
if r2_val > 0.85:
    print(f"   EXCELLENT! Model explains {r2_val*100:.1f}% of solar radiation variance")
elif r2_val > 0.75:
    print(f"   GOOD! Model explains {r2_val*100:.1f}% of solar radiation variance")
else:
    print(f"   FAIR. Model explains {r2_val*100:.1f}% of variance. Consider more features.")

print(f"\n🚀 NEXT STEPS:")
print(f"   1. Review feature importance to understand predictions")
print(f"   2. Apply model to 949 grid points for national map")
print(f"   3. Calculate solar power potential (kWh) from radiation")
