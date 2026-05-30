# solar_predict_grid.py
# Predicts solar specific yield for TRAINED PROVINCES ONLY
# Trained on: Western Province + Uva Province
# When more data is available, add province to TRAINED_PROVINCES list

import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings('ignore')

# ── File Paths ────────────────────────────────────────────────────────────────
BASE         = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\weather_data'
META         = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\metadata'
SOLAR_MODEL  = BASE + r'\solar_model.pkl'
TEMP_MODEL   = BASE + r'\temp_model.pkl'
RAIN_MODEL   = BASE + r'\rain_model.pkl'
GRID_FILE    = META + r'\grid_coordinates_with_elevation.csv'
COMPLETE     = META + r'\grid_coordinates_complete.csv'
OUTPUT_FILE  = BASE + r'\solar_grid_predictions.csv'
ANNUAL_FILE  = BASE + r'\solar_grid_predictions_annual.csv'

YEAR = 2024   # representative year for baseline potential

# ── Trained Provinces ─────────────────────────────────────────────────────────
# ADD more provinces here when historical generation data becomes available
TRAINED_PROVINCES = ['Western Province', 'Uva Province']

# ── Load ──────────────────────────────────────────────────────────────────────
def load_data():
    print('Loading models and grid data...')
    solar_model = joblib.load(SOLAR_MODEL)['model']
    temp_model  = joblib.load(TEMP_MODEL)['model']
    rain_model  = joblib.load(RAIN_MODEL)['model']

    grid = pd.read_csv(GRID_FILE)
    meta = pd.read_csv(COMPLETE, usecols=[
               'grid_id','location_name','district','province','cell_type'
           ])

    # ── Filter grid to trained provinces only ─────────────────────────────────
    trained_grid_ids = meta[
        meta['province'].isin(TRAINED_PROVINCES) & (meta['cell_type'] == 'land')
    ]['grid_id'].unique()
    grid = grid[grid['grid_id'].isin(trained_grid_ids)].reset_index(drop=True)
    # ──────────────────────────────────────────────────────────────────────────

    print(f'  Trained provinces    : {TRAINED_PROVINCES}')
    print(f'  Grid cells (filtered): {len(grid)}')
    print(f'  All models loaded    : ✅')
    return solar_model, temp_model, rain_model, grid, meta

# ── Build full grid × month DataFrame (vectorized) ───────────────────────────
def build_grid_months(grid):
    print('\nBuilding grid × month combinations...')
    months = pd.DataFrame({'month': range(1, 13)})
    months['key'] = 1
    grid['key']   = 1
    df = grid.merge(months, on='key').drop('key', axis=1)
    df = df.rename(columns={'centroid_lat': 'lat', 'centroid_lon': 'lon'})
    print(f'  Total rows           : {len(df)} ({len(grid)} cells × 12 months)')
    return df

# ── Predict weather + solar yield (fully vectorized — fast!) ─────────────────
def predict_all(df, temp_model, rain_model, solar_model):
    print('\nPredicting weather and solar yield (vectorized)...')

    X_weather = df[['lat','lon','elevation','month']].copy()
    X_weather['year'] = YEAR

    df['T_corrected']  = temp_model.predict(X_weather)
    df['RF_corrected'] = np.maximum(0, rain_model.predict(X_weather))
    print(f'  T range              : {df["T_corrected"].min():.2f} – {df["T_corrected"].max():.2f} °C')
    print(f'  RF range             : {df["RF_corrected"].min():.2f} – {df["RF_corrected"].max():.2f} mm')

    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

    X_solar = pd.DataFrame({
        'lat'         : df['lat'],
        'lon'         : df['lon'],
        'plant_elev'  : df['elevation'],
        'month_sin'   : df['month_sin'],
        'month_cos'   : df['month_cos'],
        'T_corrected' : df['T_corrected'],
        'RF_corrected': df['RF_corrected'],
    })

    df['specific_yield_kWh_kWp'] = np.maximum(0, solar_model.predict(X_solar))
    print(f'  Yield range          : {df["specific_yield_kWh_kWp"].min():.2f} – '
          f'{df["specific_yield_kWh_kWp"].max():.2f} kWh/kWp/month')
    return df

# ── Annual Summary ────────────────────────────────────────────────────────────
def annual_summary(df, meta):
    print('\nBuilding annual summary...')

    annual = (df.groupby(['grid_id','lat','lon'])
                ['specific_yield_kWh_kWp']
                .sum()
                .reset_index()
                .rename(columns={'specific_yield_kWh_kWp': 'annual_yield_kWh_kWp'}))

    annual = annual.merge(meta, on='grid_id', how='left')

    # Land cells only (already filtered, but kept as safeguard)
    annual = annual[annual['cell_type'] == 'land'].reset_index(drop=True)

    annual['solar_potential'] = pd.cut(
        annual['annual_yield_kWh_kWp'],
        bins  =[0, 840, 1020, 1140, 1320, 99999],
        labels=['Very Low','Low','Medium','High','Very High']
    )

    print(f'\n  Land grid cells      : {len(annual)}')
    print(f'  Provinces covered    : {sorted(annual["province"].unique().tolist())}')
    print('\n  ── Potential Distribution ──────────────────────')
    print(annual['solar_potential'].value_counts().sort_index().to_string())

    print('\n  ── Top 10 Land Grid Cells by Annual Yield ──────')
    top10 = (annual.nlargest(10, 'annual_yield_kWh_kWp')
                   [['grid_id','location_name','district',
                     'province','annual_yield_kWh_kWp','solar_potential']])
    print(top10.to_string(index=False))

    print('\n  ── Bottom 5 Land Grid Cells ────────────────────')
    bot5 = (annual.nsmallest(5, 'annual_yield_kWh_kWp')
                  [['grid_id','location_name','district',
                    'province','annual_yield_kWh_kWp','solar_potential']])
    print(bot5.to_string(index=False))

    return annual

# ── Save ──────────────────────────────────────────────────────────────────────
def save(df, annual):
    df.to_csv(OUTPUT_FILE, index=False)
    annual.to_csv(ANNUAL_FILE, index=False)
    print(f'\n  Monthly predictions → {OUTPUT_FILE}')
    print(f'  Annual summary      → {ANNUAL_FILE}')

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('═'*60)
    print('     ☀  SOLAR GRID POTENTIAL PREDICTOR  ☀')
    print('═'*60)

    solar_model, temp_model, rain_model, grid, meta = load_data()
    df     = build_grid_months(grid)
    df     = predict_all(df, temp_model, rain_model, solar_model)
    annual = annual_summary(df, meta)
    save(df, annual)

    print('\nDone! ✅')
