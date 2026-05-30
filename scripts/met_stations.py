"""
Complete Weather Station Coverage Map
All 24 Met Stations with Red Pins (Always Visible)
Rainfall Stations: Clustered purple/blue circles
"""
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from pathlib import Path
from shapely.geometry import Point

print("="*70)
print("LOADING ALL WEATHER STATIONS")
print("="*70)

# Manually define the 24 Met Stations (extracted from CSV)
met_stations_data = [
    {"name": "BANDARAWELA", "latitude": 6.8309042, "longitude": 80.9862597, "elevation": 1225.0},
    {"name": "JAFFNA", "latitude": 9.6938245, "longitude": 80.0329471, "elevation": 3.0},
    {"name": "MULLATIVE", "latitude": 9.2708048, "longitude": 80.8192548, "elevation": 3.0},
    {"name": "MANNAR", "latitude": 8.98, "longitude": 79.92, "elevation": 4.0},
    {"name": "VAVUNIYA", "latitude": 8.7603122, "longitude": 80.4966419, "elevation": 98.0},
    {"name": "TRINCOMALEE", "latitude": 8.6439, "longitude": 81.195, "elevation": 24.0},
    {"name": "ANURADHAPURA", "latitude": 8.335, "longitude": 80.415, "elevation": 92.0},
    {"name": "MAHA ILLUPPALLAMA", "latitude": 8.1172811, "longitude": 80.4741199, "elevation": 117.0},
    {"name": "PUTTALAM", "latitude": 8.03, "longitude": 79.83, "elevation": 2.0},
    {"name": "BATTICALOA", "latitude": 7.72, "longitude": 81.7, "elevation": 8.0},
    {"name": "KURUNEGALA", "latitude": 7.4794462, "longitude": 80.3534561, "elevation": 116.0},
    {"name": "KATUGASTOTA", "latitude": 7.33, "longitude": 80.63, "elevation": 417.0},
    {"name": "KATUNAYAKA", "latitude": 7.17, "longitude": 79.88, "elevation": 8.0},
    {"name": "COLOMBO", "latitude": 6.9048995, "longitude": 79.8720599, "elevation": 7.0},
    {"name": "NUWARA ELIYA", "latitude": 6.97, "longitude": 80.78, "elevation": 1894.0},
    {"name": "BADULLA", "latitude": 6.98, "longitude": 81.05, "elevation": 670.0},
    {"name": "RATNAPURA", "latitude": 6.6772721, "longitude": 80.4013733, "elevation": 86.0},
    {"name": "GALLE", "latitude": 6.0297239, "longitude": 80.214594, "elevation": 12.0},
    {"name": "HAMBANTOTA", "latitude": 6.1224829, "longitude": 81.1287286, "elevation": 16.0},
    {"name": "POTTUVIL", "latitude": 6.88, "longitude": 81.83, "elevation": 4.0},
    {"name": "MATTALA", "latitude": 6.3, "longitude": 81.13, "elevation": 61.0},
    {"name": "MONARAGALA", "latitude": 6.8355124, "longitude": 81.3156141, "elevation": 165.0},
    {"name": "POLONNARUWA", "latitude": 7.87, "longitude": 81.05, "elevation": 43.0},
    {"name": "RATMALANA", "latitude": 6.82108, "longitude": 79.88861, "elevation": 5.0},
]

met_df = pd.DataFrame(met_stations_data)
met_df['type'] = 'met'
print(f"✓ Met Stations (Red pins): {len(met_df)}")
print(f"\nAll 24 Met Stations:")
for i, name in enumerate(met_df['name'], 1):
    print(f"  {i}. {name}")

# Load Old Rainfall Stations
rainfall_old_df = pd.read_csv("data/raw/stations/Copy of Met Stations Rainfall stations all from the begining.xlsx.csv",
                                usecols=['Name', 'Lon', 'Lat', 'elevation'],
                                on_bad_lines='skip')
rainfall_old_df = rainfall_old_df.rename(columns={'Name': 'name', 'Lon': 'longitude', 'Lat': 'latitude'})
rainfall_old_df['longitude'] = pd.to_numeric(rainfall_old_df['longitude'], errors='coerce')
rainfall_old_df['latitude'] = pd.to_numeric(rainfall_old_df['latitude'], errors='coerce')
rainfall_old_df = rainfall_old_df.dropna(subset=['longitude', 'latitude'])
rainfall_old_df['type'] = 'rainfall_old'
print(f"✓ Old Rainfall Stations (Purple): {len(rainfall_old_df)}")

# Load New Rainfall Stations
rainfall_new_df = pd.read_csv("data/raw/stations/Copy of Met Stations Rainfall Stations & Parameters 2023-2025.xlsx.csv",
                                usecols=['station_name', 'longitude', 'latitude'],
                                on_bad_lines='skip')
rainfall_new_df = rainfall_new_df.rename(columns={'station_name': 'name'})
rainfall_new_df['longitude'] = pd.to_numeric(rainfall_new_df['longitude'], errors='coerce')
rainfall_new_df['latitude'] = pd.to_numeric(rainfall_new_df['latitude'], errors='coerce')
rainfall_new_df = rainfall_new_df.dropna(subset=['longitude', 'latitude'])
rainfall_new_df['elevation'] = 0
rainfall_new_df['type'] = 'rainfall_new'
print(f"✓ New Rainfall Stations (Blue): {len(rainfall_new_df)}")

# Combine all stations
all_stations = pd.concat([met_df, rainfall_old_df, rainfall_new_df], ignore_index=True)
print(f"\n✓ TOTAL STATIONS: {len(all_stations)}")

# Load grid
print("\nLoading grid data...")
grid_gdf = gpd.read_file("data/bronze/metadata/grid_cells_all.geojson")
try:
    coords_df = pd.read_csv("data/bronze/metadata/grid_coordinates_with_exact_locations.csv")
    grid_gdf = grid_gdf.merge(coords_df, on="grid_id", how="left")
except:
    pass

if 'centroid_lat' not in grid_gdf.columns:
    grid_gdf['centroid_lat'] = grid_gdf.geometry.centroid.y
    grid_gdf['centroid_lon'] = grid_gdf.geometry.centroid.x

if 'location_name' not in grid_gdf.columns:
    grid_gdf['location_name'] = 'Unknown'

print(f"✓ Grid cells: {len(grid_gdf)}")

# Create GeoDataFrame for stations
stations_gdf = gpd.GeoDataFrame(
    all_stations,
    geometry=[Point(lon, lat) for lon, lat in zip(all_stations["longitude"], all_stations["latitude"])],
    crs="EPSG:4326"
)

# Spatial join
print("\nPerforming spatial join...")
stations_in_grid = gpd.sjoin(stations_gdf, grid_gdf, how="left", predicate="within")
grid_with_stations = gpd.sjoin(grid_gdf, stations_gdf, how="inner", predicate="contains")

# Count stations by type in each grid
grid_counts = grid_with_stations.groupby(['grid_id', 'type']).size().unstack(fill_value=0)
grid_gdf = grid_gdf.merge(grid_counts, left_on='grid_id', right_index=True, how='left').fillna(0)

for col in ['met', 'rainfall_old', 'rainfall_new']:
    if col not in grid_gdf.columns:
        grid_gdf[col] = 0

grid_gdf['has_station'] = grid_gdf[['met', 'rainfall_old', 'rainfall_new']].sum(axis=1) > 0
grid_gdf['total_stations'] = grid_gdf[['met', 'rainfall_old', 'rainfall_new']].sum(axis=1).astype(int)
grid_gdf['met'] = grid_gdf['met'].astype(int)
grid_gdf['rainfall_old'] = grid_gdf['rainfall_old'].astype(int)
grid_gdf['rainfall_new'] = grid_gdf['rainfall_new'].astype(int)

print(f"\n{'='*70}")
print("COVERAGE STATISTICS")
print("="*70)
print(f"Total stations: {len(all_stations)}")
print(f"  - Met: {len(met_df)} (all 24 loaded!)")
print(f"  - Rainfall Old: {len(rainfall_old_df)}")
print(f"  - Rainfall New: {len(rainfall_new_df)}")
print(f"\nGrid cells with stations: {grid_gdf['has_station'].sum()} / {len(grid_gdf)}")
print(f"Grid cells with Met stations: {(grid_gdf['met'] > 0).sum()}")

# Create map
print("\nCreating interactive map...")
m = folium.Map(location=[7.5, 80.7], zoom_start=8, tiles="OpenStreetMap")

# Color scheme
def get_color(total):
    if total == 0: return "#F5F5F5", 0.15
    elif total <= 2: return "#FFE5CC", 0.4
    elif total <= 5: return "#FFCC99", 0.5
    elif total <= 10: return "#FF9966", 0.6
    else: return "#FF6633", 0.7

# Add grid
print("Adding grid cells...")
for idx, row in grid_gdf.iterrows():
    color, opacity = get_color(row['total_stations'])
    folium.GeoJson(
        row["geometry"],
        style_function=lambda x, col=color, op=opacity: {
            "fillColor": col, "color": "#999", "weight": 0.5, "fillOpacity": op
        },
        tooltip=f"{row.get('location_name', 'Unknown')} | {int(row['total_stations'])} stations",
        popup=folium.Popup(
            f"<div style='font-family: Arial;'>"
            f"<h4 style='margin: 0; color: #FF6633;'>{row.get('location_name', 'Unknown')}</h4>"
            f"<hr style='margin: 5px 0;'>"
            f"<b>Grid ID:</b> {row['grid_id']}<br>"
            f"<b>Met Stations:</b> {int(row['met'])}<br>"
            f"<b>Rainfall (Old):</b> {int(row['rainfall_old'])}<br>"
            f"<b>Rainfall (New):</b> {int(row['rainfall_new'])}<br>"
            f"<b>Total:</b> {int(row['total_stations'])}"
            f"</div>",
            max_width=300
        )
    ).add_to(m)

# Create clusters for rainfall, but NOT for Met stations
rain_old_cluster = MarkerCluster(name='🟣 Rainfall Old', show=True)
rain_new_cluster = MarkerCluster(name='🔵 Rainfall New', show=True)

# Add rainfall stations (clustered)
for idx, row in stations_gdf[stations_gdf['type'] == 'rainfall_old'].iterrows():
    folium.CircleMarker(
        [row.geometry.y, row.geometry.x], radius=3, color='purple', fill=True,
        fillColor='purple', fillOpacity=0.6, 
        popup=f"<b>{row['name']}</b><br>Rainfall (Historical)",
        tooltip=row['name']
    ).add_to(rain_old_cluster)

for idx, row in stations_gdf[stations_gdf['type'] == 'rainfall_new'].iterrows():
    folium.CircleMarker(
        [row.geometry.y, row.geometry.x], radius=3, color='blue', fill=True,
        fillColor='blue', fillOpacity=0.6,
        popup=f"<b>{row['name']}</b><br>Rainfall (2023-2025)",
        tooltip=row['name']
    ).add_to(rain_new_cluster)

# Add clusters to map first
rain_old_cluster.add_to(m)
rain_new_cluster.add_to(m)

# Add Met stations LAST and with higher z-index so they appear ON TOP
print(f"Adding {len(met_df)} Met stations as red pins (ON TOP)...")
met_layer = folium.FeatureGroup(name='🔴 Met Stations (24)', show=True)

met_stations_gdf = stations_gdf[stations_gdf['type'] == 'met']
for idx, row in met_stations_gdf.iterrows():
    folium.Marker(
        [row.geometry.y, row.geometry.x],
        popup=folium.Popup(
            f"<div style='font-family: Arial; min-width: 220px;'>"
            f"<h4 style='margin: 0; color: #DC143C;'>🌡️ {row['name']}</h4>"
            f"<hr style='margin: 5px 0;'>"
            f"<b>Type:</b> Meteorological Station<br>"
            f"<b>Latitude:</b> {row['latitude']:.5f}°N<br>"
            f"<b>Longitude:</b> {row['longitude']:.5f}°E<br>"
            f"<b>Elevation:</b> {row['elevation']:.0f} m"
            f"</div>",
            max_width=320
        ),
        tooltip=f"🌡️ {row['name']}",
        icon=folium.Icon(color='red', icon='cloud', prefix='fa', icon_color='white'),
        z_index_offset=1000  # High z-index to appear on top
    ).add_to(met_layer)

met_layer.add_to(m)

# Legend
legend_html = f"""
<div style="position: fixed; bottom: 50px; right: 50px; width: 300px;
            background-color: white; z-index: 9999; font-size: 14px;
            border: 2px solid #FF6633; border-radius: 5px; padding: 15px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
    <p style="margin: 0 0 10px 0; font-weight: bold; font-size: 16px; color: #FF6633;">
        🌤️ Weather Stations Coverage
    </p>
    <p style="margin: 8px 0;">
        <i class="fa fa-map-marker" style="color: red; font-size: 18px;"></i> 
        <b>Met Stations (24)</b><br>
        <span style="font-size: 11px; color: #666; margin-left: 24px;">✓ All 24 loaded - Red pins on top</span>
    </p>
    <p style="margin: 8px 0;">
        <span style="color: purple; font-size: 20px;">●</span> 
        <b>Rainfall Old ({len(rainfall_old_df)})</b><br>
        <span style="font-size: 11px; color: #666; margin-left: 24px;">Purple circles - Clustered</span>
    </p>
    <p style="margin: 8px 0;">
        <span style="color: blue; font-size: 20px;">●</span> 
        <b>Rainfall New ({len(rainfall_new_df)})</b><br>
        <span style="font-size: 11px; color: #666; margin-left: 24px;">Blue circles - Clustered</span>
    </p>
    <hr style="margin: 10px 0;">
    <p style="margin: 5px 0; font-size: 12px;">
        <b>Total Stations:</b> {len(all_stations)}<br>
        <b>Grid Coverage:</b> {grid_gdf['has_station'].sum()}/{len(grid_gdf)} cells<br>
        <b>Grid Size:</b> 10km × 10km
    </p>
    <hr style="margin: 10px 0;">
    <p style="margin: 0; font-size: 11px; color: #666;">
        💡 Red pins show all 24 Met stations<br>
        💡 Zoom in to see individual markers
    </p>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Title
title_html = """
<div style="position: fixed; top: 10px; left: 50px; width: 680px;
            background-color: white; z-index: 9999; font-size: 18px;
            border: 2px solid #FF6633; border-radius: 5px; padding: 10px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
    <p style="margin: 0; font-weight: bold; color: #FF6633;">
        Sri Lanka Weather Stations Grid Coverage Map - All 24 Met Stations ✓
    </p>
    <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">
        Met stations (24 red pins) | Rainfall stations (purple/blue circles) | 10km × 10km grid
    </p>
</div>
"""
m.get_root().html.add_child(folium.Element(title_html))

folium.LayerControl(position='topright').add_to(m)

# Save outputs
output_path = Path("outputs/figures/grids/complete_stations_coverage.html")
output_path.parent.mkdir(parents=True, exist_ok=True)
m.save(str(output_path))

report_path = Path("outputs/reports/stations_grid_report.csv")
report_path.parent.mkdir(parents=True, exist_ok=True)
stations_in_grid.to_csv(report_path, index=False)

grid_summary_path = Path("outputs/reports/grid_summary.csv")
grid_gdf[['grid_id', 'location_name', 'met', 'rainfall_old', 'rainfall_new', 'total_stations']].to_csv(grid_summary_path, index=False)

met_list_path = Path("outputs/reports/met_stations_list.csv")
met_df[['name', 'latitude', 'longitude', 'elevation']].to_csv(met_list_path, index=False)

print(f"\n{'='*70}")
print("✓ SUCCESS! ALL 24 MET STATIONS LOADED")
print("="*70)
print(f"✓ Interactive map: {output_path}")
print(f"✓ Station details: {report_path}")
print(f"✓ Grid summary: {grid_summary_path}")
print(f"✓ Met stations list: {met_list_path}")
print("="*70)
print(f"\n🎉 ALL 24 MET STATIONS NOW VISIBLE AS RED PINS!")
print(f"   Red pins appear ON TOP with z-index offset")
print(f"   Open {output_path} in your browser to view.")