# rain_predict_country.py
# Predicts annual total rainfall for all Sri Lanka grid cells + generates map

import pandas as pd
import numpy as np
import joblib
import folium
import warnings
warnings.filterwarnings('ignore')

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE       = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\weather_data'
RAIN_MODEL = BASE + r'\rain_model.pkl'
GRID_FILE = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\metadata\grid_coordinates_all.csv'
OUT_CSV    = BASE + r'\rain_grid_predictions.csv'
OUT_HTML   = BASE + r'\rain_map_srilanka.html'

YEAR = 2025

# ── Load ──────────────────────────────────────────────────────────────────────
rain_pkg   = joblib.load(RAIN_MODEL)
rain_model = rain_pkg['model']

grid = pd.read_csv(GRID_FILE)
print(f"Grid loaded: {len(grid)} cells")

# ── Predict Annual Total Rainfall ─────────────────────────────────────────────
# ── Predict Annual Total Rainfall ─────────────────────────────────────────────
results = []
for _, row in grid.iterrows():
    monthly_rf = []
    for month in range(1, 13):
        X = pd.DataFrame([[row['centroid_lat'], row['centroid_lon'], 0, month, YEAR]],
                          columns=['lat', 'lon', 'elevation', 'month', 'year'])
        RF = max(0, rain_model.predict(X)[0])
        monthly_rf.append(RF)

    results.append({
        'grid_id'        : row['grid_id'],
        'lat'            : row['centroid_lat'],
        'lon'            : row['centroid_lon'],
        'elevation'      : 0,
        'district'       : 'Unknown',
        'province'       : 'Unknown',
        'annual_total_RF': round(sum(monthly_rf), 2),
        'wettest_month'  : np.argmax(monthly_rf) + 1,
        'driest_month'   : np.argmin(monthly_rf) + 1,
    })


df = pd.DataFrame(results)
df.to_csv(OUT_CSV, index=False)
print(f"\n✅ Predictions saved: {OUT_CSV}")
print(df[['district', 'annual_total_RF']].groupby('district').mean().round(2))

# ── Classify ──────────────────────────────────────────────────────────────────
def classify_rain(rf):
    if rf >= 4000:   return 'Very Wet',  '#00008B'
    elif rf >= 3000: return 'Wet',        '#1E90FF'
    elif rf >= 2000: return 'Moderate',   '#87CEEB'
    elif rf >= 1000: return 'Dry',        '#FFD700'
    else:            return 'Very Dry',   '#FF8C00'

df['category'], df['color'] = zip(*df['annual_total_RF'].apply(classify_rain))

# ── Map ───────────────────────────────────────────────────────────────────────
m = folium.Map(location=[7.8731, 80.7718], zoom_start=7, tiles='CartoDB positron')

for _, row in df.iterrows():
    cat, color = classify_rain(row['annual_total_RF'])
    folium.Rectangle(
        bounds=[[row['lat']-0.05, row['lon']-0.05],
                [row['lat']+0.05, row['lon']+0.05]],
        color=color, fill=True, fill_color=color, fill_opacity=0.7,
        popup=folium.Popup(
            f"<b>📍 {row['district']}</b><br>"
            f"Lat: {row['lat']:.4f}, Lon: {row['lon']:.4f}<br>"
            f"<b>Annual Rainfall:</b> {row['annual_total_RF']} mm<br>"
            f"<b>Category:</b> {cat}",
            max_width=200
        )
    ).add_to(m)

legend_html = """
<div style="position:fixed;bottom:40px;left:40px;z-index:9999;
     background:white;padding:15px;border-radius:8px;border:2px solid grey;font-size:13px;">
    <b>🌧 Annual Total Rainfall (mm)</b><br><br>
    <i style="background:#00008B;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Very Wet  ≥ 4000mm<br>
    <i style="background:#1E90FF;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Wet       ≥ 3000mm<br>
    <i style="background:#87CEEB;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Moderate  ≥ 2000mm<br>
    <i style="background:#FFD700;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Dry       ≥ 1000mm<br>
    <i style="background:#FF8C00;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Very Dry  < 1000mm<br>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))
m.save(OUT_HTML)
print(f"✅ Map saved: {OUT_HTML}")
