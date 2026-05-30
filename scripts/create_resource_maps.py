"""
Create WIND resource map only
"""
import pandas as pd
import geopandas as gpd
import folium
from pathlib import Path

# Load data
print("Loading wind resource data...")
coords = pd.read_csv('data/bronze/metadata/grid_with_energy_resources.csv')
grid_gdf = gpd.read_file('data/bronze/metadata/grid_cells_all.geojson')

# Merge
grid_gdf = grid_gdf.merge(
    coords[['grid_id', 'location_name', 'district', 'wind_rating', 'wind_speed', 'wind_range']],
    on='grid_id',
    how='left'
)

print(f"Creating wind resource map for {len(grid_gdf)} grid cells...")

# Wind color scheme
wind_colors = {
    'Excellent': '#8B0000',      # Dark Red
    'Very Good': '#FF6347',      # Orange-Red  
    'Good': '#FFD700',           # Gold
    'Moderate': '#B0E0E6',       # Powder Blue
    'Low-Moderate': '#E0FFFF',   # Light Cyan
    'Low': '#F0F8FF',            # Alice Blue
    'N/A': '#F0F0F0'
}

center_lat = grid_gdf['centroid_lat'].mean()
center_lon = grid_gdf['centroid_lon'].mean()

# Create wind map
m_wind = folium.Map(location=[center_lat, center_lon], zoom_start=8)

for idx, row in grid_gdf.iterrows():
    color = wind_colors.get(row['wind_rating'], '#CCCCCC')
    
    popup_html = f"""
    <div style="font-family: Arial; min-width: 250px;">
        <h4 style="margin: 0; color: #0000CD;">Wind Resource (100m)</h4>
        <hr style="margin: 5px 0;">
        <b>Location:</b> {row['location_name']}<br>
        <b>Grid:</b> {row['grid_id']}<br>
        <b>District:</b> {row['district']}<br>
        <hr style="margin: 5px 0;">
        <b>Wind Rating:</b> <span style="color: {color}; font-weight: bold;">{row['wind_rating']}</span><br>
        <b>Wind Speed:</b> {row['wind_speed']} m/s (100m)<br>
        <b>Range:</b> {row['wind_range']}<br>
    </div>
    """
    
    folium.GeoJson(
        row['geometry'],
        style_function=lambda x, color=color: {
            'fillColor': color,
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.7
        },
        tooltip=f"<b>{row['location_name']}</b><br>Wind: {row['wind_rating']}<br>Speed: {row['wind_speed']} m/s",
        popup=folium.Popup(popup_html, max_width=300)
    ).add_to(m_wind)

# Legend
legend_html = '''
<div style="position: fixed; bottom: 50px; right: 50px; width: 200px; 
            background-color: white; z-index: 9999; font-size: 14px;
            border: 2px solid grey; border-radius: 5px; padding: 15px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
    <p style="margin: 0 0 10px 0; font-weight: bold; font-size: 16px;">
        Wind Resource Potential (100m)
    </p>
    <p style="margin: 5px 0;"><span style="color: #8B0000; font-size: 20px;">■</span> Excellent (>9.0 m/s)</p>
    <p style="margin: 5px 0;"><span style="color: #FF6347; font-size: 20px;">■</span> Very Good (8.0-8.5)</p>
    <p style="margin: 5px 0;"><span style="color: #FFD700; font-size: 20px;">■</span> Good (7.0-7.5)</p>
    <p style="margin: 5px 0;"><span style="color: #B0E0E6; font-size: 20px;">■</span> Moderate (6.0-7.0)</p>
    <p style="margin: 5px 0;"><span style="color: #E0FFFF; font-size: 20px;">■</span> Low-Moderate (5.0-6.0)</p>
    <p style="margin: 5px 0;"><span style="color: #F0F8FF; font-size: 20px;">■</span> Low (<5.0)</p>
</div>
'''
m_wind.get_root().html.add_child(folium.Element(legend_html))

# Save
output_path = 'outputs/figures/grids/wind_resource_map.html'
Path(output_path).parent.mkdir(parents=True, exist_ok=True)
m_wind.save(output_path)

print(f"\n✓ Wind map saved: {output_path}")
print("\n" + "="*70)
print("Wind Resource Distribution:")
print(coords['wind_rating'].value_counts())
print("="*70)
