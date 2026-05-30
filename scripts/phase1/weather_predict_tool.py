# weather_predict_tool.py
# Predicts monthly temperature and rainfall for a given location and year

import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings('ignore')

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE       = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\weather_data'
TEMP_MODEL = BASE + r'\temp_model.pkl'
RAIN_MODEL = BASE + r'\rain_model.pkl'

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
    'kalutara'      : (6.5854,  79.9607,   5),
    'gampaha'       : (7.0917,  80.0000,  11),
    'kilinochchi'   : (9.3803,  80.4000,  10),
    'mullaitivu'    : (9.2671,  80.8128,   5),
    'mannar'        : (8.9810,  79.9044,   5),
    'nuwara eliya'  : (6.9497,  80.7891,1868),
    'kalmunai'      : (7.4167,  81.8333,   5),
}

MONTHS = ['Jan','Feb','Mar','Apr','May','Jun',
          'Jul','Aug','Sep','Oct','Nov','Dec']

# ── Load Models ───────────────────────────────────────────────────────────────
def load_models():
    temp_pkg  = joblib.load(TEMP_MODEL)
    rain_pkg  = joblib.load(RAIN_MODEL)
    return temp_pkg['model'], rain_pkg['model']

# ── Get Location ──────────────────────────────────────────────────────────────
def get_location():
    print('\n  Enter city/district name OR lat,lon')
    print('  Known cities:', ', '.join(sorted(CITIES.keys())))
    inp = input('\n  Location: ').strip().lower()

    if ',' in inp:
        parts = inp.split(',')
        lat, lon = float(parts[0]), float(parts[1])
        elev = 0
        name = f'({lat:.4f}, {lon:.4f})'
    elif inp in CITIES:
        lat, lon, elev = CITIES[inp]
        name = inp.title()
    else:
        print(f'  ⚠ City not found. Enter coordinates manually.')
        lat  = float(input('  Latitude  : '))
        lon  = float(input('  Longitude : '))
        elev = float(input('  Elevation (m), press 0 if unknown: '))
        name = f'({lat:.4f}, {lon:.4f})'

    return lat, lon, elev, name

# ── Predict ───────────────────────────────────────────────────────────────────
def predict(lat, lon, elev, year, temp_model, rain_model):
    results = []
    for month in range(1, 13):
        X = pd.DataFrame([[lat, lon, elev, month, year]],
                          columns=['lat', 'lon', 'elevation', 'month', 'year'])

        T  = temp_model.predict(X)[0]
        RF = max(0, rain_model.predict(X)[0])

        results.append({
            'Month'         : MONTHS[month - 1],
            'Temperature (°C)': round(T, 2),
            'Rainfall (mm)' : round(RF, 2),
        })

    return pd.DataFrame(results)

# ── Display ───────────────────────────────────────────────────────────────────
def display(df, name, year):
    annual_rf   = df['Rainfall (mm)'].sum()
    avg_temp    = df['Temperature (°C)'].mean()
    hottest     = df.loc[df['Temperature (°C)'].idxmax(), 'Month']
    coolest     = df.loc[df['Temperature (°C)'].idxmin(), 'Month']
    wettest     = df.loc[df['Rainfall (mm)'].idxmax(), 'Month']
    driest      = df.loc[df['Rainfall (mm)'].idxmin(), 'Month']

    print(f'\n  {"─"*55}')
    print(f'  📍 Location     : {name}')
    print(f'  📅 Year         : {year}')
    print(f'  {"─"*55}')
    print(f'\n  {"Month":<6} {"Temperature (°C)":>18} {"Rainfall (mm)":>15}')
    print(f'  {"─"*42}')
    for _, row in df.iterrows():
        print(f'  {row["Month"]:<6} {row["Temperature (°C)"]:>18} {row["Rainfall (mm)"]:>15}')
    print(f'  {"─"*42}')
    print(f'  {"Annual Avg Temp":<30} {avg_temp:>8.2f} °C')
    print(f'  {"Annual Total Rainfall":<30} {annual_rf:>8.1f} mm')
    print(f'  Hottest month   : {hottest}')
    print(f'  Coolest month   : {coolest}')
    print(f'  Wettest month   : {wettest}')
    print(f'  Driest month    : {driest}')
    print(f'  {"─"*55}\n')

    # Save
    out = BASE + r'\weather_prediction_output.csv'
    df['Location'] = name
    df['Year']     = year
    df.to_csv(out, index=False)
    print(f'  Results saved to {out}')

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('═'*57)
    print('    🌡  TEMPERATURE & RAINFALL PREDICTOR  🌧')
    print('═'*57)

    temp_model, rain_model = load_models()

    lat, lon, elev, name = get_location()
    year = int(input('  Year to predict   : '))

    print('\n  Running prediction...')
    df = predict(lat, lon, elev, year, temp_model, rain_model)
    display(df, name, year)

    again = input('  Predict another location? (y/n): ').strip().lower()
    while again == 'y':
        lat, lon, elev, name = get_location()
        year = int(input('  Year to predict   : '))
        df = predict(lat, lon, elev, year, temp_model, rain_model)
        display(df, name, year)
        again = input('  Predict another location? (y/n): ').strip().lower()

    print('\n  Thank you! ✅')
