# save as test_predict.py in your project root
import pandas as pd
import numpy as np
import joblib

TEMP_MODEL = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\weather_data\temp_model.pkl'

pkg = joblib.load(TEMP_MODEL)
model = pkg['model']

print("Features the model was trained on:")
print(pkg['features'])
print()

# Predict for Vavuniya
lat, lon, elev = 8.7514, 80.4971, 98
results = []
for month in range(1, 13):
    ms = np.sin(2 * np.pi * month / 12)
    mc = np.cos(2 * np.pi * month / 12)
    X = pd.DataFrame([[lat, lon, elev, ms, mc, 2027,
                       lat*ms, lat*mc, lon*ms, lon*mc, elev*ms, elev*mc]],
                     columns=['lat','lon','elevation','month_sin','month_cos','year',
                              'lat_x_sin','lat_x_cos','lon_x_sin','lon_x_cos',
                              'elev_x_sin','elev_x_cos'])
    T = model.predict(X)[0]
    results.append(f"Month {month:2d}: {T:.2f}°C")

for r in results:
    print(r)
