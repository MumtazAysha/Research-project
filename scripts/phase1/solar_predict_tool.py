# solar_predict_tool.py
# Chains temp_model + rain_model + solar_model to predict monthly power generation
# User inputs: location (lat/lon or city), capacity (kWp), year

import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings('ignore')

# ── Model Paths ───────────────────────────────────────────────────────────────
BASE         = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\weather_data'
TEMP_MODEL   = BASE + r'\temp_model.pkl'
RAIN_MODEL   = BASE + r'\rain_model.pkl'
SOLAR_MODEL  = BASE + r'\solar_model.pkl'
WEATHER_FILE = BASE + r'\corrected_historical_2010_2025.csv'

# ── Sri Lanka City Coordinates ────────────────────────────────────────────────
CITIES = {
    'colombo'       : (6.9271,  79.8612,   8),
    'kandy'         : (7.2906,  80.6337, 488),
    'galle'         : (6.0535,  80.2210,   4),
    'jaffna'        : (9.6615,  80.0255,  10),
    'trincomalee'   : (8.5874,  81.2152,   7),
    'batticaloa'    : (7.7170,  81.7000,   5),
    'anuradhapura'  : (8.3114,  80.4037,  81),
    'polonnaruwa'   : (7.9403,  81.0188,  59),
    'badulla'       : (6.9934,  81.0550, 678),
    'nuwara eliya'  : (6.9497,  80.7891,1868),
    'ratnapura'     : (6.6828,  80.3992,  34),
    'kurunegala'    : (7.4818,  80.3609, 116),
    'matara'        : (5.9549,  80.5550,   4),
    'hambantota'    : (6.1241,  81.1185,   7),
    'puttalam'      : (8.0362,  79.8283,   3),
    'vavuniya'      : (8.7514,  80.4971,  98),
    'ampara'        : (7.2980,  81.6724,  21),
    'monaragala'    : (6.8728,  81.3484, 136),
    'matale'        : (7.4675,  80.6234, 369),
    'kegalle'       : (7.2513,  80.3464, 120),
}

MONTHS = ['Jan','Feb','Mar','Apr','May','Jun',
          'Jul','Aug','Sep','Oct','Nov','Dec']

# ── Load Models ───────────────────────────────────────────────────────────────
def load_models():
    temp_pkg  = joblib.load(TEMP_MODEL)
    rain_pkg  = joblib.load(RAIN_MODEL)
    solar_pkg = joblib.load(SOLAR_MODEL)
    return (
        temp_pkg['model'],
        rain_pkg['model'],
        solar_pkg['model'],
        solar_pkg['features']
    )

# ── Get Elevation from nearest grid cell ──────────────────────────────────────
def get_elevation(lat, lon):
    df = pd.read_csv(WEATHER_FILE, usecols=['lat','lon','elevation'])
    df = df.drop_duplicates()
    df['dist'] = np.sqrt((df['lat'] - lat)**2 + (df['lon'] - lon)**2)
    return df.loc[df['dist'].idxmin(), 'elevation']

# ── Get Location ──────────────────────────────────────────────────────────────
def get_location():
    print('\n  Enter city name OR lat,lon')
    print('  Known cities:', ', '.join(sorted(CITIES.keys())))
    inp = input('\n  Location: ').strip().lower()

    if ',' in inp:
        parts = inp.split(',')
        lat, lon = float(parts[0]), float(parts[1])
        elev = get_elevation(lat, lon)
        name = f'({lat:.4f}, {lon:.4f})'
    elif inp in CITIES:
        lat, lon, elev = CITIES[inp]
        name = inp.title()
    else:
        print(f'  ⚠ City not found. Enter coordinates manually.')
        lat  = float(input('  Latitude  : '))
        lon  = float(input('  Longitude : '))
        elev = get_elevation(lat, lon)
        name = f'({lat:.4f}, {lon:.4f})'

    return lat, lon, elev, name

# ── Predict ───────────────────────────────────────────────────────────────────
def predict(lat, lon, elev, capacity_kwp, year, temp_model, rain_model, solar_model, solar_features):
    results = []
    for month in range(1, 13):
        X_weather = pd.DataFrame([[lat, lon, elev, month, year]],
                                  columns=['lat','lon','elevation','month','year'])

        T_pred  = temp_model.predict(X_weather)[0]
        RF_pred = max(0, rain_model.predict(X_weather)[0])

        # ── Match exactly what solar_model.pkl expects ────────────────────────
        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)

        solar_input = pd.DataFrame([[lat, lon, elev, month_sin, month_cos, T_pred, RF_pred]],
                                    columns=['lat', 'lon', 'plant_elev', 'month_sin', 'month_cos',
                                             'T_corrected', 'RF_corrected'])

        yield_kwh_per_kwp = max(0, solar_model.predict(solar_input)[0])
        total_kwh = yield_kwh_per_kwp * capacity_kwp

        results.append({
            'Month'             : MONTHS[month - 1],
            'T_predicted (°C)'  : round(T_pred, 2),
            'RF_predicted (mm)' : round(RF_pred, 2),
            'Yield (kWh/kWp)'   : round(yield_kwh_per_kwp, 2),
            'Generation (kWh)'  : round(total_kwh, 2),
        })

    return pd.DataFrame(results)

# ── Display Results ───────────────────────────────────────────────────────────
def display(df, name, capacity_kwp, year):
    annual = df['Generation (kWh)'].sum()
    best   = df.loc[df['Generation (kWh)'].idxmax(), 'Month']
    worst  = df.loc[df['Generation (kWh)'].idxmin(), 'Month']

    print(f'\n  {"─"*60}')
    print(f'  📍 Location   : {name}')
    print(f'  ⚡ Capacity   : {capacity_kwp} kWp')
    print(f'  📅 Year       : {year}')
    print(f'  {"─"*60}')
    print(f'\n  {"Month":<6} {"T (°C)":>8} {"RF (mm)":>10} {"kWh/kWp":>10} {"Generation":>13}')
    print(f'  {"─"*52}')
    for _, row in df.iterrows():
        print(f'  {row["Month"]:<6} {row["T_predicted (°C)"]:>8} {row["RF_predicted (mm)"]:>10} '
              f'{row["Yield (kWh/kWp)"]:>10} {row["Generation (kWh)"]:>10} kWh')
    print(f'  {"─"*52}')
    print(f'  {"ANNUAL TOTAL":<30} {annual:>10.1f} kWh')
    print(f'  Best month    : {best}')
    print(f'  Worst month   : {worst}')
    print(f'  {"─"*60}\n')

    # Save output
    out = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\weather_data\solar_prediction_output.csv'
    df['Location'] = name
    df['Capacity_kWp'] = capacity_kwp
    df['Year'] = year
    df.to_csv(out, index=False)
    print(f'  Results saved to {out}')

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('═'*62)
    print('       ☀  SOLAR POWER GENERATION PREDICTOR  ☀')
    print('═'*62)

    temp_model, rain_model, solar_model, solar_features = load_models()

    lat, lon, elev, name = get_location()
    capacity_kwp = float(input('  Capacity (kWp)    : '))
    year         = int(input('  Year to predict   : '))

    print('\n  Running prediction...')
    df = predict(lat, lon, elev, capacity_kwp, year,
                 temp_model, rain_model, solar_model, solar_features)

    display(df, name, capacity_kwp, year)

    again = input('  Predict another location? (y/n): ').strip().lower()
    while again == 'y':
        lat, lon, elev, name = get_location()
        capacity_kwp = float(input('  Capacity (kWp)    : '))
        year         = int(input('  Year to predict   : '))
        df = predict(lat, lon, elev, capacity_kwp, year,
                     temp_model, rain_model, solar_model, solar_features)
        display(df, name, capacity_kwp, year)
        again = input('  Predict another location? (y/n): ').strip().lower()

    print('\n  Thank you! ✅')
