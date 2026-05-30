import pandas as pd
import numpy as np

print("="*80)
print("STEP 3: FEATURE ENGINEERING FOR TIME SERIES PREDICTION")
print("="*80)

# Load the daily dataset
station = "43415"
df = pd.read_csv(f'data/processed/solar_daily_{station}_2019_2025.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

print(f"📥 Loaded {len(df):,} daily records\n")

# ============================================================================
# 1. TIME-BASED FEATURES
# ============================================================================
print("📅 Creating time-based features...")

df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day_of_year'] = df['date'].dt.dayofyear
df['day_of_week'] = df['date'].dt.dayofweek
df['quarter'] = df['date'].dt.quarter

# Cyclical encoding for seasonal patterns
df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
df['day_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
df['day_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365)

print(f"   ✅ Added 10 time features")

# ============================================================================
# 2. LAG FEATURES (Previous days' values)
# ============================================================================
print("\n⏰ Creating lag features...")

lag_days = [1, 2, 3, 7, 14, 30]  # Look back 1d, 2d, 3d, 1w, 2w, 1m

for lag in lag_days:
    df[f'solar_lag_{lag}d'] = df['solar_radiation'].shift(lag)
    df[f'cloud_lag_{lag}d'] = df['cloud_cover'].shift(lag)
    
print(f"   ✅ Added {len(lag_days)*2} lag features")

# ============================================================================
# 3. ROLLING WINDOW FEATURES (Trends)
# ============================================================================
print("\n📊 Creating rolling window features...")

windows = [7, 14, 30]  # 1 week, 2 weeks, 1 month

for window in windows:
    df[f'solar_rolling_{window}d'] = df['solar_radiation'].rolling(window).mean()
    df[f'solar_rolling_std_{window}d'] = df['solar_radiation'].rolling(window).std()
    df[f'cloud_rolling_{window}d'] = df['cloud_cover'].rolling(window).mean()
    df[f'precip_rolling_{window}d'] = df['precipitation'].rolling(window).sum()

print(f"   ✅ Added {len(windows)*4} rolling features")

# ============================================================================
# 4. WEATHER INTERACTION FEATURES
# ============================================================================
print("\n🌦️  Creating weather interaction features...")

df['temp_range'] = df['temp_max'] - df['temp_min']
df['cloud_precip_interaction'] = df['cloud_cover'] * df['precipitation']
df['humidity_temp_interaction'] = df['humidity'] * df['temp_mean']

print(f"   ✅ Added 3 interaction features")

# ============================================================================
# 5. SEASONAL MONSOON INDICATORS (Sri Lanka specific!)
# ============================================================================
print("\n🌧️  Creating Sri Lankan monsoon season features...")

def get_monsoon_season(month):
    if month in [5, 6, 7, 8, 9]:  # Southwest Monsoon (Yala)
        return 1
    elif month in [10, 11, 12, 1, 2]:  # Northeast Monsoon (Maha)
        return 2
    else:  # Inter-monsoon
        return 0

df['monsoon_season'] = df['month'].apply(get_monsoon_season)
df['is_southwest_monsoon'] = (df['monsoon_season'] == 1).astype(int)
df['is_northeast_monsoon'] = (df['monsoon_season'] == 2).astype(int)

print(f"   ✅ Added 3 monsoon features")

# ============================================================================
# REMOVE ROWS WITH NaN (from lag/rolling features)
# ============================================================================
print(f"\n🧹 Cleaning data...")
print(f"   Before: {len(df):,} rows")

df_clean = df.dropna().reset_index(drop=True)

print(f"   After: {len(df_clean):,} rows")
print(f"   Removed: {len(df) - len(df_clean)} rows (early dates with no lag data)")

# ============================================================================
# SAVE ENGINEERED DATASET
# ============================================================================
output_file = f'data/processed/solar_features_{station}_2019_2025.csv'
df_clean.to_csv(output_file, index=False)

print(f"\n💾 Saved to: {output_file}")
print(f"\n📊 FEATURE SUMMARY:")
print(f"   Total features: {len(df_clean.columns) - 2}")  # Exclude date + target
print(f"   Date range: {df_clean['date'].min()} to {df_clean['date'].max()}")
print(f"   Total rows: {len(df_clean):,}")

print(f"\n🎯 TARGET VARIABLE: solar_radiation")
print(f"\n📋 FEATURE CATEGORIES:")
print(f"   • Time features: 10")
print(f"   • Lag features: 12")
print(f"   • Rolling window features: 12")
print(f"   • Weather interactions: 3")
print(f"   • Monsoon features: 3")
print(f"   • Base weather features: 7")
print(f"   TOTAL: ~47 features")

print(f"\n✅ FEATURE ENGINEERING COMPLETE!")
print(f"💡 Next: Split data and train ML model!")

# Show sample
print(f"\n📋 SAMPLE FEATURES:")
print(df_clean[['date', 'solar_radiation', 'solar_lag_1d', 'solar_rolling_7d', 
                'cloud_cover', 'month', 'is_southwest_monsoon']].head(10))
