'''Create Hydro Resource Map showing mini and major hydro plants
on the 10km x 10km grid with blue color scheme and LOCATION NAMES'''
import pandas as pd
import geopandas as gpd
import folium
from pathlib import Path
from shapely.geometry import Point

print("="*70)
print("CREATING HYDRO RESOURCE MAP WITH LOCATION NAMES")
print("="*70)

# Load hydro plant data
print("Loading hydro plant data...")
hydro_df = pd.read_csv("hydro_plants_cleaned.csv")

major_hydro = hydro_df[hydro_df["Type"] == "Major"].copy()
mini_hydro = hydro_df[hydro_df["Type"] == "Mini"].copy()

print(f"✓ Loaded {len(major_hydro)} major hydro plants")
print(f"✓ Loaded {len(mini_hydro)} mini hydro plants")

# Load grid data with location names
print("Loading grid data with location names...")
grid_gdf = gpd.read_file("data/bronze/metadata/grid_cells_all.geojson")

# Try to load coordinates with location names
try:
    coords_df = pd.read_csv("data/bronze/metadata/grid_coordinates_with_exact_locations.csv")
    print("✓ Loaded grid coordinates with location names")
except:
    try:
        coords_df = pd.read_csv("data/bronze/metadata/grid_with_real_solar_data.csv")
        print("✓ Loaded grid coordinates from solar data file")
    except:
        coords_df = pd.read_csv("data/bronze/metadata/grid_coordinates_all.csv")
        print("✓ Loaded basic grid coordinates")

# Merge grid with coordinates/location data
grid_gdf = grid_gdf.merge(coords_df, on="grid_id", how="left")

print(f"✓ Loaded {len(grid_gdf)} grid cells")

# Calculate centroids if not present
if 'centroid_lat' not in grid_gdf.columns:
    print("Calculating centroids from geometry...")
    grid_gdf['centroid_lat'] = grid_gdf.geometry.centroid.y
    grid_gdf['centroid_lon'] = grid_gdf.geometry.centroid.x

# Add location_name column if not present
if 'location_name' not in grid_gdf.columns:
    grid_gdf['location_name'] = 'Unknown'

# Add district column if not present
if 'district' not in grid_gdf.columns:
    grid_gdf['district'] = 'Unknown'

print(f"✓ Centroids and location names ready")

# Convert hydro plants to GeoDataFrames
mini_gdf = gpd.GeoDataFrame(
    mini_hydro,
    geometry=[Point(lon, lat) for lat, lon in zip(mini_hydro["Latitude"], mini_hydro["Longitude"])],
    crs="EPSG:4326"
)

major_gdf = gpd.GeoDataFrame(
    major_hydro,
    geometry=[Point(lon, lat) for lat, lon in zip(major_hydro["Latitude"], major_hydro["Longitude"])],
    crs="EPSG:4326"
)

# Spatial join: Find which grid cells contain hydro plants
print("Identifying grid cells with hydro plants...")
grid_with_mini = gpd.sjoin(grid_gdf, mini_gdf, how="inner", predicate="contains")
grid_with_major = gpd.sjoin(grid_gdf, major_gdf, how="inner", predicate="contains")

# Mark grid cells that have hydro plants
grid_gdf["has_mini_hydro"] = grid_gdf["grid_id"].isin(grid_with_mini["grid_id"])
grid_gdf["has_major_hydro"] = grid_gdf["grid_id"].isin(grid_with_major["grid_id"])
grid_gdf["has_any_hydro"] = grid_gdf["has_mini_hydro"] | grid_gdf["has_major_hydro"]

print(f"✓ Grid cells with mini hydro: {grid_gdf['has_mini_hydro'].sum()}")
print(f"✓ Grid cells with major hydro: {grid_gdf['has_major_hydro'].sum()}")
print(f"✓ Grid cells with any hydro: {grid_gdf['has_any_hydro'].sum()}")

# Create map
print("Creating interactive map...")
center_lat = grid_gdf["centroid_lat"].mean()
center_lon = grid_gdf["centroid_lon"].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles="OpenStreetMap")

# Blue color scheme for hydro
hydro_colors = {
    "both": "#003366",
    "major": "#0055AA",
    "mini": "#66B3FF",
    "none": "#F5F5F5"
}

# Add all grid cells
print("Adding grid cells to map...")
for idx, row in grid_gdf.iterrows():
    if row["has_mini_hydro"] and row["has_major_hydro"]:
        color = hydro_colors["both"]
        hydro_type = "Mini + Major Hydro"
        opacity = 0.7
    elif row["has_major_hydro"]:
        color = hydro_colors["major"]
        hydro_type = "Major Hydro"
        opacity = 0.7
    elif row["has_mini_hydro"]:
        color = hydro_colors["mini"]
        hydro_type = "Mini Hydro"
        opacity = 0.6
    else:
        color = hydro_colors["none"]
        hydro_type = "No Hydro"
        opacity = 0.2

    location_name = row.get('location_name', 'Unknown')
    district = row.get('district', 'Unknown')

    folium.GeoJson(
        row["geometry"],
        style_function=lambda x, col=color, op=opacity: {
            "fillColor": col,
            "color": "#0066CC",
            "weight": 0.5,
            "fillOpacity": op
        },
        tooltip=f"{location_name} | {hydro_type}",
        popup=folium.Popup(
            f"<div style='font-family: Arial; min-width: 250px;'>"
            f"<h4 style='margin: 0; color: #003366;'>Hydro Resource</h4>"
            f"<hr style='margin: 5px 0;'>"
            f"<b>Location:</b> {location_name}<br>"
            f"<b>District:</b> {district}<br>"
            f"<b>Grid ID:</b> {row['grid_id']}<br>"
            f"<hr style='margin: 5px 0;'>"
            f"<b>Type:</b> {hydro_type}<br>"
            f"<b>Coordinates:</b> {row['centroid_lat']:.4f}°N, {row['centroid_lon']:.4f}°E"
            f"</div>",
            max_width=300
        )
    ).add_to(m)

# Add mini hydro plant markers
print("Adding mini hydro plant markers...")
for idx, plant in mini_gdf.iterrows():
    folium.CircleMarker(
        location=[plant.geometry.y, plant.geometry.x],
        radius=4,
        color="#0066FF",
        fill=True,
        fillColor="#3399FF",
        fillOpacity=0.9,
        weight=2,
        popup=folium.Popup(
            f"<div style='font-family: Arial; min-width: 250px;'>"
            f"<h4 style='margin: 0; color: #0066FF;'>Mini Hydro Plant</h4>"
            f"<hr style='margin: 5px 0;'>"
            f"<b>{plant['Name']}</b><br>"
            f"<b>Capacity:</b> {plant['Capacity_MW']} MW<br>"
            f"<b>Coordinates:</b> {plant['Latitude']:.5f}°N, {plant['Longitude']:.5f}°E"
            f"</div>",
            max_width=300
        ),
        tooltip=f"{plant['Name']} ({plant['Capacity_MW']} MW)"
    ).add_to(m)

# Add major hydro plant markers
print("Adding major hydro plant markers...")
for idx, plant in major_gdf.iterrows():
    folium.CircleMarker(
        location=[plant.geometry.y, plant.geometry.x],
        radius=8,
        color="#001A33",
        fill=True,
        fillColor="#003366",
        fillOpacity=1.0,
        weight=3,
        popup=folium.Popup(
            f"<div style='font-family: Arial; min-width: 250px;'>"
            f"<h4 style='margin: 0; color: #003366;'>Major Hydro Plant</h4>"
            f"<hr style='margin: 5px 0;'>"
            f"<b>{plant['Name']}</b><br>"
            f"<b>Capacity:</b> {plant['Capacity_MW']} MW<br>"
            f"<b>Coordinates:</b> {plant['Latitude']:.5f}°N, {plant['Longitude']:.5f}°E"
            f"</div>",
            max_width=300
        ),
        tooltip=f"{plant['Name']} ({plant['Capacity_MW']} MW)"
    ).add_to(m)

# Add legend and title
legend_html = """
<div style="position: fixed; bottom: 50px; right: 50px; width: 220px;
            background-color: white; z-index: 9999; font-size: 14px;
            border: 2px solid #0066CC; border-radius: 5px; padding: 15px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
    <p style="margin: 0 0 10px 0; font-weight: bold; font-size: 16px; color: #003366;">
        Hydro Resources
    </p>
    <p style="margin: 5px 0;">
        <span style="color: #003366; font-size: 20px;">●</span> Mini + Major
    </p>
    <p style="margin: 5px 0;">
        <span style="color: #0055AA; font-size: 20px;">●</span> Major Only
    </p>
    <p style="margin: 5px 0;">
        <span style="color: #66B3FF; font-size: 20px;">●</span> Mini Only
    </p>
    <p style="margin: 5px 0;">
        <span style="color: #F5F5F5; font-size: 18px;">○</span> No Hydro
    </p>
    <hr style="margin: 10px 0;">
    <p style="margin: 0; font-size: 11px;">
        Grid: 10km × 10km<br>
        Major: 15 | Mini: 189
    </p>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

title_html = """
<div style="position: fixed; top: 10px; left: 50px; width: 520px;
            background-color: white; z-index: 9999; font-size: 18px;
            border: 2px solid #0066CC; border-radius: 5px; padding: 10px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
    <p style="margin: 0; font-weight: bold; color: #003366;">
        Sri Lanka Hydro Power Resource Map
    </p>
    <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">
        Location Names | Major & Mini Hydro Plants
    </p>
</div>
"""
m.get_root().html.add_child(folium.Element(title_html))

# Save
output_path = Path("outputs/figures/grids/hydro_resource_map.html")
output_path.parent.mkdir(parents=True, exist_ok=True)
m.save(str(output_path))

print("="*70)
print("✓ HYDRO RESOURCE MAP CREATED SUCCESSFULLY!")
print(f"✓ Saved to: {output_path}")
print("="*70)