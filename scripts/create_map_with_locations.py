"""
Create interactive map showing grid cells with location names
"""
import pandas as pd
import geopandas as gpd
import folium
from pathlib import Path 

# Load grid data with locations
coords = pd.read_csv('data/bronze/metadata/grid_coordinates_with_exact_locations.csv')
grid_gdf = gpd.read_file('data/bronze/metadata/grid_cells_all.geojson')

# Merge location names into grid GeoDataFrame
grid_gdf = grid_gdf.merge(
    coords[['grid_id', 'location_name', 'locality', 'district', 'province']], 
    on='grid_id', 
    how='left'
)

print(f"Creating map with {len(grid_gdf)} grid cells and location names...")

# Calculate center
center_lat = grid_gdf['centroid_lat'].mean()
center_lon = grid_gdf['centroid_lon'].mean()

# Create map
m = folium.Map(location=[center_lat, center_lon], zoom_start=8)

# Color scheme
color_map = {
    'land': '#90EE90',      # Light green
    'ocean': '#ADD8E6',     # Light blue
    'coastal': '#FFD580',   # Light orange
    'unknown': 'gray'
}

# Add grid cells with location names
for idx, row in grid_gdf.iterrows():
    cell_color = color_map.get(row['cell_type'], 'gray')
    
    # Create popup with detailed info
    popup_html = f"""
    <div style="font-family: Arial; min-width: 200px;">
        <h4 style="margin: 0; color: #2C3E50;">{row['grid_id']}</h4>
        <hr style="margin: 5px 0;">
        <b>Location:</b> {row['location_name']}<br>
        <b>District:</b> {row['district']}<br>
        <b>Province:</b> {row['province']}<br>
        <b>Type:</b> {row['cell_type'].capitalize()}<br>
        <b>Area:</b> {row['area_km2']:.2f} km²<br>
        <hr style="margin: 5px 0;">
        <b>Coordinates:</b><br>
        Lat: {row['centroid_lat']:.4f}°N<br>
        Lon: {row['centroid_lon']:.4f}°E
    </div>
    """
    
    # Tooltip (shows on hover)
    tooltip_text = f"<b>{row['location_name']}</b><br>{row['grid_id']}"
    
    # Add grid cell polygon
    folium.GeoJson(
        row['geometry'],
        style_function=lambda x, color=cell_color: {
            'fillColor': color,
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.4
        },
        tooltip=tooltip_text,
        popup=folium.Popup(popup_html, max_width=300)
    ).add_to(m)
    
    # Add location name as text label (for land and coastal cells)
    if row['cell_type'] in ['land', 'coastal'] and row['location_name'] != 'Unknown':
        folium.Marker(
            location=[row['centroid_lat'], row['centroid_lon']],
            icon=folium.DivIcon(html=f"""
                <div style="
                    font-size: 8px; 
                    color: black;
                    font-weight: bold;
                    text-align: center;
                    white-space: nowrap;
                    text-shadow: 1px 1px 1px white, -1px -1px 1px white;
                ">
                    {row['location_name'][:15]}
                </div>
            """)
        ).add_to(m)

# Add legend
legend_html = '''
<div style="
    position: fixed; 
    bottom: 50px; 
    right: 50px; 
    width: 180px; 
    background-color: white; 
    z-index: 9999; 
    font-size: 14px;
    border: 2px solid grey; 
    border-radius: 5px; 
    padding: 15px;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
">
    <p style="margin: 0 0 10px 0; font-weight: bold; font-size: 16px;">
        Sri Lanka Weather Grid
    </p>
    <p style="margin: 5px 0;">
        <span style="color: #90EE90; font-size: 20px;">■</span> Land
    </p>
    <p style="margin: 5px 0;">
        <span style="color: #FFD580; font-size: 20px;">■</span> Coastal
    </p>
    <p style="margin: 5px 0;">
        <span style="color: #ADD8E6; font-size: 20px;">■</span> Ocean
    </p>
    <hr style="margin: 10px 0;">
    <p style="margin: 5px 0; font-size: 12px;">
        <b>Total Cells:</b> {total_cells}<br>
        <b>Cell Size:</b> 10km × 10km
    </p>
</div>
'''.format(total_cells=len(grid_gdf))

m.get_root().html.add_child(folium.Element(legend_html))

# Add title
title_html = '''
<div style="
    position: fixed; 
    top: 10px; 
    left: 50px; 
    width: 400px; 
    background-color: white; 
    z-index: 9999; 
    font-size: 18px;
    border: 2px solid #2C3E50; 
    border-radius: 5px; 
    padding: 10px;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
">
    <p style="margin: 0; font-weight: bold; color: #2C3E50;">
        🗺️ Sri Lanka 10km × 10km Weather Grid with Locations
    </p>
    <p style="margin: 5px 0 0 0; font-size: 12px; color: #7F8C8D;">
        Hover over cells to see location names • Click for details
    </p>
</div>
'''

m.get_root().html.add_child(folium.Element(title_html))

# Save map
output_path = 'outputs/figures/grids/sri_lanka_grid_with_locations.html'
Path(output_path).parent.mkdir(parents=True, exist_ok=True)
m.save(output_path)

print(f"\n✓ Map created successfully!")
print(f"✓ Saved to: {output_path}")
print(f"\nMap features:")
print(f"  • {len(grid_gdf)} grid cells")
print(f"  • Location names displayed")
print(f"  • Color-coded by cell type")
print(f"  • Hover for quick info")
print(f"  • Click for detailed popup")
print(f"\nOpen the file in your browser to view!")
