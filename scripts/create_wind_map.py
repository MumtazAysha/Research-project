"""
Create interactive wind resource map for Sri Lanka
"""
import pandas as pd
import geopandas as gpd
import folium
from pathlib import Path


print("Creating wind resource map...")


# Load data
coords = pd.read_csv('data/bronze/metadata/grid_with_wind_data.csv')
grid_gdf = gpd.read_file('data/bronze/metadata/grid_cells_all.geojson')


# Merge
grid_gdf = grid_gdf.merge(
    coords[['grid_id', 'location_name', 'district', 'wind_speed_100m', 'wind_rating', 'wind_range', 'wind_power_density']], 
    on='grid_id', 
    how='left'
)


print(f"Creating wind map for {len(grid_gdf)} grid cells...")


# Wind resource color scheme - DISTINCT colors
wind_colors = {
    'Excellent': '#8B0000',      # Dark Red/Maroon (≥9.0 m/s)
    'Very Good': '#FF6347',      # Tomato/Orange-Red (7.5-9.0)
    'Good': '#FF8C00',           # Dark Orange (6.5-7.5)
    'Moderate': '#FFD700',       # Gold (5.5-6.5)
    'Fair': '#FFFF99',           # Pale Yellow (4.0-5.5)
    'Poor': '#D3D3D3',           # Light Gray (<4.0)
    'No Data': '#FFFFFF'         # White
}


center_lat = grid_gdf['centroid_lat'].mean()
center_lon = grid_gdf['centroid_lon'].mean()


# Create map
m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles='OpenStreetMap')


# Add grid cells
for idx, row in grid_gdf.iterrows():
    # Get cell_type safely
    cell_type = row.get('cell_type', 'unknown')
    if pd.isna(cell_type):
        cell_type = 'unknown'
    
    # Handle missing wind data
    if pd.isna(row['wind_speed_100m']):
        color = wind_colors['No Data']
        wind_speed_display = 'N/A'
        wind_rating_display = 'No Data'
        wind_range_display = 'N/A'
        power_density_display = 'N/A'
    else:
        color = wind_colors.get(row['wind_rating'], '#CCCCCC')
        wind_speed_display = f"{row['wind_speed_100m']:.2f} m/s"
        wind_rating_display = row['wind_rating']
        wind_range_display = row['wind_range']
        power_density_display = f"{row['wind_power_density']:.1f} W/m²"
    
    # Popup content
    popup_html = f"""
    <div style="font-family: Arial; min-width: 280px;">
        <h4 style="margin: 0; color: #8B0000;">💨 Wind Resource (Global Wind Atlas)</h4>
        <hr style="margin: 5px 0;">
        <b>Location:</b> {row['location_name']}<br>
        <b>Grid ID:</b> {row['grid_id']}<br>
        <b>District:</b> {row['district']}<br>
        <b>Cell Type:</b> <span style="text-transform: capitalize;">{cell_type}</span><br>
        <b>Coordinates:</b> {row['centroid_lat']:.3f}°N, {row['centroid_lon']:.3f}°E<br>
        <hr style="margin: 5px 0;">
        <b>Rating:</b> <span style="color: {color}; font-weight: bold; font-size: 16px;">{wind_rating_display}</span><br>
        <b>Wind Speed (100m):</b> <span style="font-weight: bold;">{wind_speed_display}</span><br>
        <b>Range:</b> {wind_range_display}<br>
        <b>Power Density:</b> {power_density_display}<br>
        <hr style="margin: 5px 0;">
        <small>Data source: Global Wind Atlas 3.0</small>
    </div>
    """
    
    # Tooltip
    tooltip = f"<b>{row['location_name']}</b><br>Type: {cell_type.capitalize()}<br>Wind: {wind_speed_display}<br>{wind_rating_display}"
    
    # Add to map
    folium.GeoJson(
        row['geometry'],
        style_function=lambda x, color=color: {
            'fillColor': color,
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.85
        },
        tooltip=tooltip,
        popup=folium.Popup(popup_html, max_width=350)
    ).add_to(m)


# Add legend
legend_html = '''
<div style="position: fixed; bottom: 50px; right: 50px; width: 240px; 
            background-color: white; z-index: 9999; font-size: 14px;
            border: 2px solid grey; border-radius: 5px; padding: 15px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
    <p style="margin: 0 0 10px 0; font-weight: bold; font-size: 16px;">
        💨 Wind Resource (100m height)
    </p>
    <p style="margin: 5px 0;"><span style="color: #8B0000; font-size: 20px;">■</span> Excellent (≥8.5 m/s)</p>
    <p style="margin: 5px 0;"><span style="color: #FF4500; font-size: 20px;">■</span> Very Good (7.5-8.5)</p>
    <p style="margin: 5px 0;"><span style="color: #FFA500; font-size: 20px;">■</span> Good (6.5-7.5)</p>
    <p style="margin: 5px 0;"><span style="color: #FFD700; font-size: 20px;">■</span> Moderate (5.5-6.5)</p>
    <p style="margin: 5px 0;"><span style="color: #FFFFE0; font-size: 20px;">■</span> Fair (4.0-5.5)</p>
    <p style="margin: 5px 0;"><span style="color: #E8E8E8; font-size: 20px;">■</span> Poor (<4.0 m/s)</p>
    <hr style="margin: 10px 0;">
    <p style="margin: 0; font-size: 11px;">
        <b>Data:</b> Global Wind Atlas 3.0<br>
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
            border: 2px solid #8B0000; border-radius: 5px; padding: 10px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
    <p style="margin: 0; font-weight: bold; color: #8B0000;">
        💨 Sri Lanka Wind Resource Map - 100m Height
    </p>
    <p style="margin: 5px 0 0 0; font-size: 12px; color: #7F8C8D;">
        Global Wind Atlas Data • Mean Wind Speed at Turbine Height
    </p>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))


# Save map
output_path = 'outputs/figures/grids/wind_resource_map.html'
Path(output_path).parent.mkdir(parents=True, exist_ok=True)
m.save(output_path)


print(f"\n✓ Wind resource map created!")
print(f"✓ Saved to: {output_path}")
print("\n💨 Open the file in your browser to view!")
print("="*70)


