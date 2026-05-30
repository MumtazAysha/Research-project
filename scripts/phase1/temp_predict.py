# temp_predict_country.py
# Predicts annual average temperature for all Sri Lanka grid cells + generates map

import pandas as pd
import numpy as np
import joblib
import folium
import warnings
warnings.filterwarnings('ignore')

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE       = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\weather_data'
TEMP_MODEL = BASE + r'\temp_model.pkl'
GRID_FILE = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\metadata\grid_coordinates_all.csv'
OUT_CSV    = BASE + r'\temp_grid_predictions.csv'
OUT_HTML   = BASE + r'\temp_map_srilanka.html'

YEAR = 2025

# ── Load ──────────────────────────────────────────────────────────────────────
temp_pkg   = joblib.load(TEMP_MODEL)
temp_model = temp_pkg['model']

grid = pd.read_csv(GRID_FILE)
print(f"Grid loaded: {len(grid)} cells")
print(f"Columns: {grid.columns.tolist()}")

# ── Predict Annual Average Temperature ───────────────────────────────────────
# ── Predict Annual Average Temperature ───────────────────────────────────────
results = []
for _, row in grid.iterrows():
    monthly_temps = []
    for month in range(1, 13):
        X = pd.DataFrame([[row['centroid_lat'], row['centroid_lon'], 0, month, YEAR]],
                          columns=['lat', 'lon', 'elevation', 'month', 'year'])
        T = temp_model.predict(X)[0]
        monthly_temps.append(T)

    results.append({
        'grid_id'      : row['grid_id'],
        'lat'          : row['centroid_lat'],
        'lon'          : row['centroid_lon'],
        'elevation'    : 0,
        'district'     : 'Unknown',
        'province'     : 'Unknown',
        'annual_avg_T' : round(np.mean(monthly_temps), 2),
        'max_month_T'  : round(max(monthly_temps), 2),
        'min_month_T'  : round(min(monthly_temps), 2),
    })

df = pd.DataFrame(results)
df.to_csv(OUT_CSV, index=False)
print(f"\n✅ Predictions saved: {OUT_CSV}")
print(df[['district', 'annual_avg_T']].groupby('district').mean().round(2))

# ── Classify ──────────────────────────────────────────────────────────────────
def classify_temp(t):
    if t >= 30:   return 'Very Hot',  '#FF0000'
    elif t >= 28: return 'Hot',        '#FF6600'
    elif t >= 25: return 'Warm',       '#FFA500'
    elif t >= 22: return 'Moderate',   '#FFD700'
    elif t >= 18: return 'Cool',       '#90EE90'
    else:         return 'Cold',       '#00BFFF'

df['category'], df['color'] = zip(*df['annual_avg_T'].apply(classify_temp))

# ── Map ───────────────────────────────────────────────────────────────────────
m = folium.Map(location=[7.8731, 80.7718], zoom_start=7, tiles='CartoDB positron')

for _, row in df.iterrows():
    cat, color = classify_temp(row['annual_avg_T'])
    folium.Rectangle(
        bounds=[[row['lat']-0.05, row['lon']-0.05],
                [row['lat']+0.05, row['lon']+0.05]],
        color=color, fill=True, fill_color=color, fill_opacity=0.7,
        popup=folium.Popup(
            f"<b>📍 {row['district']}</b><br>"
            f"Lat: {row['lat']:.4f}, Lon: {row['lon']:.4f}<br>"
            f"<b>Avg Temp:</b> {row['annual_avg_T']} °C<br>"
            f"<b>Category:</b> {cat}",
            max_width=200
        )
    ).add_to(m)

legend_html = """
<div style="position:fixed;bottom:40px;left:40px;z-index:9999;
     background:white;padding:15px;border-radius:8px;border:2px solid grey;font-size:13px;">
    <b>🌡 Annual Avg Temperature (°C)</b><br><br>
    <i style="background:#FF0000;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Very Hot  ≥ 30°C<br>
    <i style="background:#FF6600;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Hot       ≥ 28°C<br>
    <i style="background:#FFA500;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Warm      ≥ 25°C<br>
    <i style="background:#FFD700;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Moderate  ≥ 22°C<br>
    <i style="background:#90EE90;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Cool      ≥ 18°C<br>
    <i style="background:#00BFFF;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Cold      < 18°C<br>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))
m.save(OUT_HTML)
print(f"✅ Map saved: {OUT_HTML}")
