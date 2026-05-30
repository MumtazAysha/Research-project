"""
Solar heat map with location names for each grid
"""

import pandas as pd
import geopandas as gpd
import folium
from pathlib import Path

print("="*70)
print("CREATING SOLAR HEAT MAP WITH LOCATION NAMES")
print("="*70)

# -------------------------------------------------------------------
# 1. Load grid location names
# -------------------------------------------------------------------

# Option 1: If you have a CSV with grid_id and location names
try:
    grid_locations = pd.read_csv("data/bronze/metadata/grid_coordinates_with_exact_locations.csv")
    print(f"\n✓ Loaded location names for {len(grid_locations)} grids")
except:
    print("\n⚠ Location names file not found, using reverse geocoding...")
    grid_locations = None

# -------------------------------------------------------------------
# 2. Load other datasets
# -------------------------------------------------------------------

grid_gdf = gpd.read_file("data/bronze/metadata/grid_cells_all.geojson")
print(f"✓ Loaded {len(grid_gdf)} grid cells")

# Merge location names if available
if grid_locations is not None and 'location_name' in grid_locations.columns:
    grid_gdf = grid_gdf.merge(
        grid_locations[['grid_id', 'location_name']], 
        on='grid_id', 
        how='left'
    )
    print(f"✓ Added location names to grids")
else:
    # Use reverse geocoding to get location names
    from geopy.geocoders import Nominatim
    from time import sleep
    
    geolocator = Nominatim(user_agent="sri_lanka_solar_map")
    
    location_names = []
    print("\nGetting location names (this takes a few minutes)...")
    
    for idx, row in grid_gdf.iterrows():
        try:
            location = geolocator.reverse(
                f"{row['centroid_lat']}, {row['centroid_lon']}", 
                language='en'
            )
            if location:
                address = location.raw.get('address', {})
                name = (address.get('village') or 
                       address.get('town') or 
                       address.get('city') or 
                       address.get('county') or 
                       address.get('state_district') or 
                       'Unknown')
                location_names.append(name)
            else:
                location_names.append('Unknown')
            sleep(1.1)  # Rate limit
        except:
            location_names.append('Unknown')
        
        if (idx + 1) % 50 == 0:
            print(f"  Processed {idx + 1}/{len(grid_gdf)} grids...")
    
    grid_gdf['location_name'] = location_names
    
    # Save for future use
    grid_gdf[['grid_id', 'location_name', 'centroid_lat', 'centroid_lon']].to_csv(
        "data/bronze/metadata/grid_coordinates_with_exact_locations.csv",
        index=False
    )
    print(f"✓ Saved location names to CSV")

# Fill any missing location names
grid_gdf['location_name'] = grid_gdf['location_name'].fillna('Unknown')

solar_df = pd.read_csv("data/bronze/metadata/grid_with_real_solar_data.csv")
print(f"✓ Loaded solar data for {len(solar_df)} grids")

rain_all = pd.read_csv(
    "data/raw/stations/Copy of Met Stations Rainfall stations all from the begining.xlsx.csv",
    on_bad_lines="skip"
)
print(f"✓ Loaded {len(rain_all)} rainfall stations")

# -------------------------------------------------------------------
# 2. All 24 Met stations (hardcoded)
# -------------------------------------------------------------------

met_stations_data = [
    {"station_name": "BANDARAWELA", "lat": 6.8309042, "lon": 80.9862597, "elevation": 1225.0},
    {"station_name": "JAFFNA", "lat": 9.6938245, "lon": 80.0329471, "elevation": 3.0},
    {"station_name": "MULLATIVE", "lat": 9.2708048, "lon": 80.8192548, "elevation": 3.0},
    {"station_name": "MANNAR", "lat": 8.98, "lon": 79.92, "elevation": 4.0},
    {"station_name": "VAVUNIYA", "lat": 8.7603122, "lon": 80.4966419, "elevation": 98.0},
    {"station_name": "TRINCOMALEE", "lat": 8.6439, "lon": 81.195, "elevation": 24.0},
    {"station_name": "ANURADHAPURA", "lat": 8.335, "lon": 80.415, "elevation": 92.0},
    {"station_name": "MAHA ILLUPPALLAMA", "lat": 8.1172811, "lon": 80.4741199, "elevation": 117.0},
    {"station_name": "PUTTALAM", "lat": 8.03, "lon": 79.83, "elevation": 2.0},
    {"station_name": "BATTICALOA", "lat": 7.72, "lon": 81.7, "elevation": 8.0},
    {"station_name": "KURUNEGALA", "lat": 7.4794462, "lon": 80.3534561, "elevation": 116.0},
    {"station_name": "KATUGASTOTA", "lat": 7.33, "lon": 80.63, "elevation": 417.0},
    {"station_name": "KATUNAYAKA", "lat": 7.17, "lon": 79.88, "elevation": 8.0},
    {"station_name": "COLOMBO", "lat": 6.9048995, "lon": 79.8720599, "elevation": 7.0},
    {"station_name": "NUWARA ELIYA", "lat": 6.97, "lon": 80.78, "elevation": 1894.0},
    {"station_name": "BADULLA", "lat": 6.98, "lon": 81.05, "elevation": 670.0},
    {"station_name": "RATNAPURA", "lat": 6.6772721, "lon": 80.4013733, "elevation": 86.0},
    {"station_name": "GALLE", "lat": 6.0297239, "lon": 80.214594, "elevation": 12.0},
    {"station_name": "HAMBANTOTA", "lat": 6.1224829, "lon": 81.1287286, "elevation": 16.0},
    {"station_name": "POTTUVIL", "lat": 6.88, "lon": 81.83, "elevation": 4.0},
    {"station_name": "MATTALA", "lat": 6.3, "lon": 81.13, "elevation": 61.0},
    {"station_name": "MONARAGALA", "lat": 6.8355124, "lon": 81.3156141, "elevation": 165.0},
    {"station_name": "POLONNARUWA", "lat": 7.87, "lon": 81.05, "elevation": 43.0},
    {"station_name": "RATMALANA", "lat": 6.82108, "lon": 79.88861, "elevation": 5.0},
]

met_main = pd.DataFrame(met_stations_data)
print(f"✓ Loaded ALL {len(met_main)} Met stations")

# -------------------------------------------------------------------
# 3. Prepare solar heat map
# -------------------------------------------------------------------

good_ratings = ["Excellent", "Very Good", "Good", "Moderate"]  
solar_good = solar_df[solar_df["solar_rating"].isin(good_ratings)].copy()
print(f"\nSolar Moderate–Excellent grids: {len(solar_good)}")

solar_grids = grid_gdf.merge(
    solar_good[["grid_id", "real_ghi", "solar_rating"]],
    on="grid_id",
    how="inner"
)
print(f"✓ Solar grids with geometry: {len(solar_grids)}")

solar_colors = {
    "Excellent": "#FF4500",
    "Very Good": "#FF8C00",
    "Good": "#FFD700",
    "Moderate": "#FFFF99",
}

# -------------------------------------------------------------------
# 4. Prepare rainfall stations
# -------------------------------------------------------------------

rain_all = rain_all.rename(columns={
    "id": "station_id",
    "Name": "station_name",
    "Lon": "lon",
    "Lat": "lat",
    "district": "district",
    "begindate": "begin_date",
    "enddate": "end_date"
})

rain_all["lat"] = pd.to_numeric(rain_all["lat"], errors="coerce")
rain_all["lon"] = pd.to_numeric(rain_all["lon"], errors="coerce")
rain_all = rain_all.dropna(subset=["lat", "lon"])
print(f"\nRainfall stations with valid coords: {len(rain_all)}")

def is_active(end_date):
    s = str(end_date).strip()
    if "9999" in s:
        return True
    try:
        if "/" in s:
            year = int(s.split("/")[-1])
        elif "-" in s:
            parts = s.split("-")
            year = int(parts[-1]) if len(parts[-1]) == 4 else int(parts[0])
        elif len(s) >= 4:
            year = int(s[-4:])
        else:
            return False
        return year >= 2023
    except:
        return False

rain_all["is_active"] = rain_all["end_date"].apply(is_active)
active_count = rain_all["is_active"].sum()
inactive_count = len(rain_all) - active_count
print(f"Active rainfall stations: {active_count}")
print(f"Historical rainfall stations: {inactive_count}")

# -------------------------------------------------------------------
# 5. Create map
# -------------------------------------------------------------------

m = folium.Map(
    location=[7.5, 80.7],
    zoom_start=8,
    tiles="OpenStreetMap"
    )

# -------------------------------------------------------------------
# 6. Add solar heat map WITH LOCATION NAMES
# -------------------------------------------------------------------

print("\nAdding solar heat map grids with location names...")

for _, row in solar_grids.iterrows():
    color = solar_colors.get(row["solar_rating"], "#DDCE32")
    location_name = row.get('location_name', 'Unknown')
    
    popup_html = f"""
    <div style='font-family: Arial; min-width: 240px;'>
        <h4 style='margin: 0; color: {color};'>📍 {location_name}</h4>
        <hr style='margin: 5px 0;'>
        <b>Grid ID:</b> {row['grid_id']}<br>
        <b>Solar rating:</b> {row['solar_rating']}<br>
        <b>GHI:</b> {row['real_ghi']:.1f} kWh/m²/year<br>
        <b>Center:</b> {row['centroid_lat']:.3f}°N, {row['centroid_lon']:.3f}°E<br>
    </div> 
    """
    
    folium.GeoJson(
        row["geometry"],
        style_function=lambda x, color=color: {
            "fillColor": color,
            "color": "black",
            "weight": 0.3,
            "fillOpacity": 0.55
        },
        tooltip=f"{location_name} | {row['solar_rating']}",
        popup=folium.Popup(popup_html, max_width=280)
    ).add_to(m)

# -------------------------------------------------------------------
# 7. Add rainfall stations (circles)
# -------------------------------------------------------------------
print("Adding rainfall stations...")

for _, row in rain_all.iterrows():
    if row["is_active"]:
        color = "#2196F3"
        fill = "#64B5F6"
        status = "Active"
    else:
        color = "#9C27B0"
        fill = "#BA68C8"
        status = "Historical"

    popup_html = f"""
    <div style='font-family: Arial; min-width: 230px;'>
        <h4 style='margin: 0; color: {color};'>🌧️ {row['station_name']}</h4>
        <hr style='margin: 5px 0;'>
        <b>Status:</b> {status}<br>
        <b>Location:</b> {row['lat']:.4f}°N, {row['lon']:.4f}°E
    </div>
    """

    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=4,
        color=color,
        fill=True,
        fillColor=fill,
        fillOpacity=0.85,
        popup=folium.Popup(popup_html, max_width=260),
        tooltip=f"{row['station_name']} – {status}"
    ).add_to(m)

# -------------------------------------------------------------------
# 8. Add Met stations as RED PINS
# -------------------------------------------------------------------

print(f"Adding {len(met_main)} Met stations as red pins...")

met_layer = folium.FeatureGroup(name='🔴 Met Stations (24)', show=True)

for _, row in met_main.iterrows():
    popup_html = f"""
    <div style='font-family: Arial; min-width: 280px;'>
        <h3 style='margin: 0; color: #DC143C; background: #FFEBEE; padding: 8px; border-radius: 4px;'>
            🌡️ {row['station_name']}
        </h3>
        <hr style='margin: 8px 0;'>
        <b>Type:</b> Meteorological Station<br>
        <b>Latitude:</b> {row['lat']:.5f}°N<br>
        <b>Longitude:</b> {row['lon']:.5f}°E<br>
        <b>Elevation:</b> {row['elevation']:.0f} m
    </div>
    """

    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=folium.Popup(popup_html, max_width=320),
        tooltip=f"🌡️ {row['station_name']}",
        icon=folium.Icon(color='red', icon='cloud', prefix='fa', icon_color='white'),
        z_index_offset=1000
    ).add_to(met_layer)

met_layer.add_to(m)

# -------------------------------------------------------------------
# 9. Legend and title
# -------------------------------------------------------------------

legend_html = f"""
<div style='position: fixed; bottom: 50px; right: 40px; width: 320px;
     background-color: white; z-index: 9999; font-size: 13px;
     border: 2px solid #FF4500; border-radius: 5px; padding: 10px;
     box-shadow: 2px 2px 6px rgba(0,0,0,0.3);'>
  <h4 style='margin: 0 0 8px 0; color:#FF4500;'>Solar & Weather Network</h4>
  <b>Solar grids (10×10 km)</b><br>
  <span style='background:#FF4500; padding:2px 6px;'>■</span> Excellent<br>
  <span style='background:#FF8C00; padding:2px 6px;'>■</span> Very good<br>
  <span style='background:#FFD700; padding:2px 6px;'>■</span> Good<br>
  <span style='background:#FFFF99; padding:2px 6px;'>■</span> Moderate<br>
  <hr style='margin:6px 0;'>
  <b>Stations</b><br>
  <i class="fa fa-map-marker" style="color:red; font-size:16px;"></i> <b>Met (24)</b><br>
  <span style='color:#2196F3; font-size:14px;'>●</span> Active rainfall ({active_count})<br>
  <span style='color:#9C27B0; font-size:14px;'>●</span> Historical rainfall ({inactive_count})<br>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

title_html = """
<div style='position: fixed; top: 10px; left: 40px; width: 700px;
     background-color: white; z-index: 9999; font-size: 16px;
     border: 2px solid #FF4500; border-radius: 5px; padding: 8px 10px;
     box-shadow: 2px 2px 6px rgba(0,0,0,0.3);'>
  <b style='color:#FF4500;'>Sri Lanka – Solar Resource & Weather Network</b><br>
  <span style='font-size:12px; color:#555;'>
    Solar grids with location names + All 24 Met stations (red pins) + Rainfall network
  </span>
</div>
"""
m.get_root().html.add_child(folium.Element(title_html))

folium.LayerControl(position='topright').add_to(m)

# -------------------------------------------------------------------
# 10. Save
# -------------------------------------------------------------------

out_path = "outputs/figures/grids/solar_weather_overlay.html"
Path(out_path).parent.mkdir(parents=True, exist_ok=True)
m.save(out_path)

print("\n" + "="*70)
print("✓ MAP CREATED WITH LOCATION NAMES!")
print("="*70)
print(f"\nSaved to: {out_path}")
print(f"  Solar grids: {len(solar_grids)} (with location names)")
print(f"  Rainfall: {len(rain_all)} (active {active_count}, historical {inactive_count})")
print(f"  Met stations: {len(met_main)} ✓")
print("\n📍 Now shows location names like 'Barandana' in grid popups!")


