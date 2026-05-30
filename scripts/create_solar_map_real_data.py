"""
Create solar resource map using REAL GHI data from Global Solar Atlas
WITH latitude/longitude grid lines
"""
import pandas as pd
import geopandas as gpd
import folium
from pathlib import Path

# Load data with REAL solar values
print("Loading real solar data...")
coords = pd.read_csv('data/bronze/metadata/grid_with_real_solar_data.csv')
grid_gdf = gpd.read_file('data/bronze/metadata/grid_cells_all.geojson')

# Merge
grid_gdf = grid_gdf.merge(
    coords[['grid_id', 'location_name', 'district', 'real_ghi', 'solar_rating', 'solar_range']], 
    on='grid_id', 
    how='left'
)

print(f"Creating solar map with REAL data for {len(grid_gdf)} grid cells...")

# Color scheme matching SLSEA report
solar_colors = {
    'Excellent': '#FF4500',      # Red-Orange (>2,042)
    'Very Good': '#FF8C00',      # Dark Orange (2,002-2,039)
    'Good': '#FFD700',           # Gold (1,904-1,966)
    'Moderate': '#FFFF99',       # Light Yellow (1,830-1,903)
    'Low': '#E0E0E0',            # Light Gray (1,766-1,829)
    'Very Low': '#C0C0C0'        # Gray (<1,766)
}

center_lat = grid_gdf['centroid_lat'].mean()
center_lon = grid_gdf['centroid_lon'].mean()

# Create map
m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles='OpenStreetMap')

# ============ ADD LAT/LON GRID LINES ============
# Define lat/lon ranges for Sri Lanka
lat_lines = [6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]
lon_lines = [79.5, 80.0, 80.5, 81.0, 81.5, 82.0]

# Add latitude lines (horizontal)
for lat in lat_lines:
    folium.PolyLine(
        locations=[[lat, 79.4], [lat, 82.1]],
        color='gray',
        weight=1,
        opacity=0.5,
        dash_array='5, 5'
    ).add_to(m)
    
    # Add latitude label
    folium.Marker(
        location=[lat, 79.35],
        icon=folium.DivIcon(html=f'''
            <div style="font-size: 10px; color: gray; font-weight: bold; white-space: nowrap;">
                {lat}°N
            </div>
        ''')
    ).add_to(m)

# Add longitude lines (vertical)
for lon in lon_lines:
    folium.PolyLine(
        locations=[[5.8, lon], [10.1, lon]],
        color='gray',
        weight=1,
        opacity=0.5,
        dash_array='5, 5'
    ).add_to(m)
    
    # Add longitude label
    folium.Marker(
        location=[5.75, lon],
        icon=folium.DivIcon(html=f'''
            <div style="font-size: 10px; color: gray; font-weight: bold; white-space: nowrap;">
                {lon}°E
            </div>
        ''')
    ).add_to(m)

# ============ ADD GRID CELLS WITH SOLAR DATA ============
for idx, row in grid_gdf.iterrows():
    color = solar_colors.get(row['solar_rating'], '#CCCCCC')
    
    popup_html = f"""
    <div style="font-family: Arial; min-width: 280px;">
        <h4 style="margin: 0; color: #FF4500;">☀️ Solar Resource (Real Data)</h4>
        <hr style="margin: 5px 0;">
        <b>Location:</b> {row['location_name']}<br>
        <b>Grid ID:</b> {row['grid_id']}<br>
        <b>District:</b> {row['district']}<br>
        <b>Coordinates:</b> {row['centroid_lat']:.3f}°N, {row['centroid_lon']:.3f}°E<br>
        <hr style="margin: 5px 0;">
        <b>Rating:</b> <span style="color: {color}; font-weight: bold; font-size: 16px;">{row['solar_rating']}</span><br>
        <b>GHI:</b> <span style="font-weight: bold;">{row['real_ghi']} kWh/m²/year</span><br>
        <b>Range:</b> {row['solar_range']}<br>
        <hr style="margin: 5px 0;">
        <small>Data source: Global Solar Atlas</small>
    </div>
    """
    
    tooltip = f"<b>{row['location_name']}</b><br>{row['centroid_lat']:.2f}°N, {row['centroid_lon']:.2f}°E<br>GHI: {row['real_ghi']} kWh/m²<br>{row['solar_rating']}"
    
    folium.GeoJson(
        row['geometry'],
        style_function=lambda x, color=color: {
            'fillColor': color,
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.7
        },
        tooltip=tooltip,
        popup=folium.Popup(popup_html, max_width=350)
    ).add_to(m)

# Add legend
legend_html = '''
<div style="position: fixed; bottom: 50px; right: 50px; width: 220px; 
            background-color: white; z-index: 9999; font-size: 14px;
            border: 2px solid grey; border-radius: 5px; padding: 15px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
    <p style="margin: 0 0 10px 0; font-weight: bold; font-size: 16px;">
        ☀️ Solar Resource (Real Data)
    </p>
    <p style="margin: 5px 0;"><span style="color: #FF4500; font-size: 20px;">■</span> Excellent (≥2,042 kWh/m²)</p>
    <p style="margin: 5px 0;"><span style="color: #FF8C00; font-size: 20px;">■</span> Very Good (2,002-2,039)</p>
    <p style="margin: 5px 0;"><span style="color: #FFD700; font-size: 20px;">■</span> Good (1,904-1,966)</p>
    <p style="margin: 5px 0;"><span style="color: #FFFF99; font-size: 20px;">■</span> Moderate (1,830-1,903)</p>
    <p style="margin: 5px 0;"><span style="color: #E0E0E0; font-size: 20px;">■</span> Low (1,766-1,829)</p>
    <p style="margin: 5px 0;"><span style="color: #C0C0C0; font-size: 20px;">■</span> Very Low (<1,766)</p>
    <hr style="margin: 10px 0;">
    <p style="margin: 0; font-size: 11px;">
        <b>Data:</b> Global Solar Atlas<br>
        <b>Total Cells:</b> 1,242<br>
        <b>Grid Size:</b> 10km × 10km
    </p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Add title
title_html = '''
<div style="position: fixed; top: 10px; left: 50px; width: 520px; 
            background-color: white; z-index: 9999; font-size: 18px;
            border: 2px solid #FF4500; border-radius: 5px; padding: 10px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
    <p style="margin: 0; font-weight: bold; color: #FF4500;">
        ☀️ Sri Lanka Solar Resource Map - Real GHI Data
    </p>
    <p style="margin: 5px 0 0 0; font-size: 12px; color: #7F8C8D;">
        Global Solar Atlas Data • 10km Grid with Lat/Lon Reference Lines
    </p>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Save map
output_path = 'outputs/figures/grids/solar_resource_map_REAL_DATA.html'
Path(output_path).parent.mkdir(parents=True, exist_ok=True)
m.save(output_path)

print(f"\n✓ Solar resource map created with lat/lon grid!")
print(f"✓ Saved to: {output_path}")
print(f"\nMap features:")
print(f"  • Real GHI data from Global Solar Atlas")
print(f"  • Latitude/longitude reference grid lines")
print(f"  • Coordinate labels on edges")
print(f"  • {len(grid_gdf)} grid cells (10km × 10km)")
print(f"  • Color-coded by solar potential")
print(f"  • Interactive tooltips showing coordinates")
print(f"\n🌞 Open the file in your browser to view!")
print("="*70)


