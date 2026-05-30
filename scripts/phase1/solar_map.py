# solar_map.py
# Generates an interactive choropleth map of solar generation across grid cells

import pandas as pd
import folium
import numpy as np
import os

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE         = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\weather_data'
GRID_FILE    = BASE + r'\solar_grid_predictions_annual.csv'
OUTPUT_HTML  = BASE + r'\solar_potential_map.html'

# ── Load Grid Predictions ─────────────────────────────────────────────────────
df = pd.read_csv(GRID_FILE)
print(f"Loaded {len(df)} grid cells")
print(df.columns.tolist())

# ── Classify Solar Potential ──────────────────────────────────────────────────
def classify(kwh):
    if kwh >= 1600:   return 'Excellent',  '#FF4500'
    elif kwh >= 1400: return 'High',        '#FF8C00'
    elif kwh >= 1200: return 'Moderate',    '#FFD700'
    elif kwh >= 1000: return 'Low',         '#ADFF2F'
    else:             return 'Very Low',    '#90EE90'

df['category'], df['color'] = zip(*df['annual_yield_kWh_kWp'].apply(classify))
# ── Create Map ────────────────────────────────────────────────────────────────
m = folium.Map(location=[7.5, 80.7], zoom_start=8, tiles='CartoDB positron')

# Add grid cell markers
for _, row in df.iterrows():
    category, color = classify(row['annual_yield_kWh_kWp'])
    folium.Rectangle(
        bounds=[
            [row['lat'] - 0.05, row['lon'] - 0.05],
            [row['lat'] + 0.05, row['lon'] + 0.05]
        ],
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(
            f"""
            <b>📍 Grid Cell</b><br>
            Lat: {row['lat']:.4f}, Lon: {row['lon']:.4f}<br>
            f'<b>Annual Yield:</b> {row["annual_yield_kWh_kWp"]:.1f} kWh/kWp<br>
            <b>Category:</b> {category}
            """,
            max_width=200
        )
    ).add_to(m)

# ── Legend ────────────────────────────────────────────────────────────────────
legend_html = """
<div style="position: fixed; bottom: 40px; left: 40px; z-index:9999;
     background-color:white; padding:15px; border-radius:8px;
     border:2px solid grey; font-size:13px;">
    <b>☀ Solar Potential (kWh/kWp)</b><br><br>
    <i style="background:#FF4500;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Excellent  ≥ 1600<br>
    <i style="background:#FF8C00;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> High       ≥ 1400<br>
    <i style="background:#FFD700;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Moderate   ≥ 1200<br>
    <i style="background:#ADFF2F;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Low        ≥ 1000<br>
    <i style="background:#90EE90;width:15px;height:15px;display:inline-block;margin-right:8px;"></i> Very Low   < 1000<br>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# ── Save ──────────────────────────────────────────────────────────────────────
m.save(OUTPUT_HTML)
print(f"\n✅ Map saved to:\n   {OUTPUT_HTML}")
print(f"   Open in any browser to view the interactive map!")
