# rain_model.py
# Trains a rainfall prediction model using corrected historical weather data
# Saves rain_model.pkl for use in solar_predict_tool.py

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib
import warnings
warnings.filterwarnings('ignore')

# ── File Paths ────────────────────────────────────────────────────────────────
WEATHER_FILE = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\weather_data\corrected_historical_2010_2025.csv'
MODEL_FILE   = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\weather_data\rain_model.pkl'

# ── Features & Target ─────────────────────────────────────────────────────────
# ✅ CHANGE 1: replaced 'month' with 'month_sin', 'month_cos'
FEATURES = [
    'lat', 'lon', 'elevation',
    'month_sin', 'month_cos', 'year',
    'lat_x_sin', 'lat_x_cos',
    'lon_x_sin', 'lon_x_cos',
    'elev_x_sin', 'elev_x_cos'
]
TARGET   = 'RF_corrected'

# ── Load Data ─────────────────────────────────────────────────────────────────
def load_data():
    print('Loading weather data...')
    df = pd.read_csv(WEATHER_FILE)
    # ✅ CHANGE 2: add cyclical encoding before dropna
    df['month_sin']  = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos']  = np.cos(2 * np.pi * df['month'] / 12)
    df['lat_x_sin']  = df['lat']       * df['month_sin']
    df['lat_x_cos']  = df['lat']       * df['month_cos']
    df['lon_x_sin']  = df['lon']       * df['month_sin']
    df['lon_x_cos']  = df['lon']       * df['month_cos']
    df['elev_x_sin'] = df['elevation'] * df['month_sin']
    df['elev_x_cos'] = df['elevation'] * df['month_cos']
    df = df.dropna(subset=FEATURES + [TARGET])
    print(f'  Rows loaded       : {len(df)}')
    print(f'  Grid cells        : {df["grid_id"].nunique()}')
    print(f'  Years             : {df["year"].min()} – {df["year"].max()}')
    print(f'  RF_corrected range: {df[TARGET].min():.2f} – {df[TARGET].max():.2f} mm')
    return df

# ── Train Model ───────────────────────────────────────────────────────────────
def train_model(df):
    print('\nTraining rainfall prediction models...')

    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ── Model 1: Linear Regression ────────────────────────────────────────────
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    r2_lr  = round(r2_score(y_test, lr.predict(X_test)), 4)
    mae_lr = round(mean_absolute_error(y_test, lr.predict(X_test)), 4)
    print(f'  Linear Regression     : R²={r2_lr}  MAE={mae_lr}mm')

    # ── Model 2: Polynomial deg 2 ─────────────────────────────────────────────
    poly = Pipeline([
        ('poly', PolynomialFeatures(degree=2, include_bias=False)),
        ('lr',   LinearRegression())
    ])
    poly.fit(X_train, y_train)
    r2_poly  = round(r2_score(y_test, poly.predict(X_test)), 4)
    mae_poly = round(mean_absolute_error(y_test, poly.predict(X_test)), 4)
    print(f'  Polynomial (deg 2)    : R²={r2_poly}  MAE={mae_poly}mm')

    # ── Model 3: Random Forest ────────────────────────────────────────────────
    rf = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1, max_depth=20)
    rf.fit(X_train, y_train)
    r2_rf  = round(r2_score(y_test, rf.predict(X_test)), 4)
    mae_rf = round(mean_absolute_error(y_test, rf.predict(X_test)), 4)
    print(f'  Random Forest         : R²={r2_rf}  MAE={mae_rf}mm')

    # ── Model 4: Gradient Boosting ────────────────────────────────────────────
    gb = GradientBoostingRegressor(n_estimators=100, random_state=42)
    gb.fit(X_train, y_train)
    r2_gb  = round(r2_score(y_test, gb.predict(X_test)), 4)
    mae_gb = round(mean_absolute_error(y_test, gb.predict(X_test)), 4)
    print(f'  Gradient Boosting     : R²={r2_gb}  MAE={mae_gb}mm')

    # ── R² Summary ────────────────────────────────────────────────────────────
    print('\n  ── R² Summary ───────────────────────────────')
    print(f'  Linear Regression     : {r2_lr}')
    print(f'  Polynomial (deg 2)    : {r2_poly}')
    print(f'  Random Forest         : {r2_rf}')
    print(f'  Gradient Boosting     : {r2_gb}')

    candidates = [
        (r2_lr,   'Linear Regression',  lr),
        (r2_poly, 'Polynomial deg 2',   poly),
        (r2_rf,   'Random Forest',      rf),
        (r2_gb,   'Gradient Boosting',  gb),
    ]
    best_r2, best_name, best_model = max(candidates, key=lambda x: x[0])
    print(f'  Best model            : {best_name} (R²={best_r2}) ★')
    print('  ─────────────────────────────────────────────')

    # ── Save Best Model ───────────────────────────────────────────────────────
    # ✅ CHANGE 3: FEATURES now contains month_sin/month_cos — saved correctly
    joblib.dump({
        'model'   : best_model,
        'features': FEATURES,
        'name'    : best_name
    }, MODEL_FILE)
    print(f'\n  Model saved to {MODEL_FILE}')

    return best_model, best_name

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    df = load_data()
    train_model(df)
    print('\nDone! ✅')

