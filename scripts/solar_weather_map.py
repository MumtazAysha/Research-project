"""
Create solar resource map with:
1. Solar resource grids (Moderate-Excellent)
2. Major Met stations (📍 red pins - all parameters)
3. Active rainfall stations (🔵 blue circles - recent data)
4. Inactive rainfall stations (🟣 purple circles - historical data)
"""

import pandas as pd
import geopandas as gpd
import folium
from pathlib import Path

print("="*70)
print("CREATING SOLAR RESOURCE MAP WITH WEATHER STATIONS")
print("="*70)

# ============================================================================
# Load Data
# ============================================================================

# Grid cells
grid_gdf = gpd.read_file("data/bronze/metadata/grid_cells_all.geojson")
print(f"\n✓ Loaded {len(grid_gdf)} grid cells")

# Solar resource data
solar_data = pd.read_csv("data/bronze/metadata/grid_with_real_solar_data.csv")
print(f"✓ Loaded solar data")

# Weather stations in solar zones
solar_stations = pd.read_csv("data/bronze/metadata/solar_resource_weather_stations.csv")
print(f"✓ Loaded {len(solar_stations)} weather stations in solar zones")

# Rainfall stations with begin/end dates
try:
    rainfall_stations = pd.read_csv("data/raw/stations/Copy of Met Stations Rainfall stations all from the begining.xlsx.csv",
                                     on_bad_lines='skip')
    print(f"✓ Loaded {len(rainfall_stations)} rainfall stations")
    
    # Standardize columns
    rainfall_stations = rainfall_stations.rename(columns={
        'Lon': 'lon',
        'Lat': 'lat',
        'id': 'station_id',
        'begindate': 'begin_date',
        'enddate': 'end_date'
    })
    
    # Clean coordinates
    rainfall_stations['lat'] = pd.to_numeric(rainfall_stations['lat'], errors='coerce')
    rainfall_stations['lon'] = pd.to_numeric(rainfall_stations['lon'], errors='coerce')
    rainfall_stations = rainfall_stations.dropna(subset=['lat', 'lon'])
    
    # Determine if station is active (has recent data)
    # If end_date is 12319999 or >= 2023, it's active (blue)
    # Otherwise it's old/inactive (purple)
    def is_active(end_date):
        end_str = str(end_date)
        if '12319999' in end_str or '31129999' in end_str:  # Still active
            return True
        # Try to parse year
        try:
            # Format might be: MMDDYYYY or DDMMYYYY
            if len(end_str) >= 4:
                year = int(end_str[-4:])
                return year >= 2023
        except:
            pass
        return False
    
    rainfall_stations['is_active'] = rainfall_stations['end_date'].apply(is_active)
    
    active_count = rainfall_stations['is_active'].sum()
    inactive_count = len(rainfall_stations) - active_count
    
    print(f"  Active (blue): {active_count}")
    print(f"  Inactive (purple): {inactive_count}")
    
except Exception as e:
    print(f"  Warning: Could not load rainfall stations: {e}")
    rainfall_stations = pd.DataFrame()
    active_count = 0
    inactive_count = 0

# Major Met stations with parameters
try:
    major_stations = pd.read_csv("data/raw/stations/Copy of Met Stations Met Stations & Parameters.xlsx.csv", 
                                  on_bad_lines='skip')
    print(f"✓ Loaded {len(major_stations)} major Met stations")
    
    # Standardize column names
    column_map = {}
    for col in major_stations.columns:
        col_lower = str(col).lower().strip()
        if 'lon' in col_lower:
            column_map[col] = 'lon'
        elif 'lat' in col_lower:
            column_map[col] = 'lat'
        elif col_lower in ['id', 'stationid', 'station_id']:
            column_map[col] = 'station_id'
        elif 'name' in col_lower:
            column_map[col] = 'Name'
        elif 'elevation' in col_lower:
            column_map[col] = 'elevation'
        elif 'parameter' in col_lower and 'daily' in col_lower:
            column_map[col] = 'parameters_daily'
        elif 'parameter' in col_lower and ('hourly' in col_lower or '3' in col_lower):
            column_map[col] = 'parameters_hourly'
        elif 'observation' in col_lower or 'obsevation' in col_lower:
            column_map[col] = 'observation_times'
    
    major_stations = major_stations.rename(columns=column_map)
    
    if 'lat' in major_stations.columns and 'lon' in major_stations.columns:
        major_stations['lat'] = pd.to_numeric(major_stations['lat'], errors='coerce')
        major_stations['lon'] = pd.to_numeric(major_stations['lon'], errors='coerce')
        major_stations = major_stations.dropna(subset=['lat', 'lon'])
        print(f"  Valid coordinates: {len(major_stations)}")
    else:
        major_stations = pd.DataFrame()
        
except Exception as e:
    print(f"  Warning: Could not load major stations: {e}")
    major_stations = pd.DataFrame()

# ============================================================================
# Process Solar Data
# ============================================================================

solar_good_ratings = ['Excellent', 'Very Good', 'Good', 'Moderate']
solar_filtered = solar_data[solar_data['solar_rating'].isin(solar_good_ratings)].copy()

solar_grids = grid_gdf.merge(
    solar_filtered[['grid_id', 'real_ghi', 'solar_rating']], 
    on='grid_id', 
    how='inner'
)

print(f"\nSolar Moderate-Excellent grids: {len(solar_grids)}")

# ============================================================================
# Create Map
# ============================================================================

center_lat = 7.8731
center_lon = 80.7718

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=8,
    tiles='OpenStreetMap'
)

# Solar color scheme
solar_colors = {
    'Excellent': '#FF4500',
    'Very Good': '#FF8C00',
    'Good': '#FFD700',
    'Moderate': '#FFFF99',
}

# ============================================================================
# Add Solar Grids
# ============================================================================

print("\nAdding solar grids...")
for idx, row in solar_grids.iterrows():
    color = solar_colors.get(row['solar_rating'], '#CCCCCC')
    
    popup_html = f"""
    <div style='font-family: Arial; min-width: 200px;'>
        <h4 style='margin: 0; color: {color};'>☀️ Solar Resource Grid</h4>
        <hr style='margin: 5px 0;'>
        <b>Grid ID:</b> {row['grid_id']}<br>
        <b>Solar Rating:</b> <span style='color: {color}; font-weight: bold;'>{row['solar_rating']}</span><br>
        <b>GHI:</b> {row['real_ghi']} kWh/m²/year<br>
        <b>Center:</b> {row['centroid_lat']:.3f}°N, {row['centroid_lon']:.3f}°E<br>
    </div>
    """
    
    folium.GeoJson(
        row['geometry'],
        style_function=lambda x, color=color: {
            'fillColor': color,
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.5
        },
        tooltip=f"{row['grid_id']}: {row['solar_rating']}",
        popup=folium.Popup(popup_html, max_width=300)
    ).add_to(m)

# ============================================================================
# Add Rainfall Stations (Blue = Active, Purple = Inactive)
# ============================================================================

if len(rainfall_stations) > 0:
    print("Adding rainfall stations (blue=active, purple=old)...")
    
    for idx, row in rainfall_stations.iterrows():
        # Skip major Met stations (will be added separately)
        if len(major_stations) > 0 and 'station_id' in major_stations.columns:
            if row.get('station_id') in major_stations['station_id'].values:
                continue
        
        # Determine color based on activity
        if row['is_active']:
            color = '#2196F3'  # Blue for active
            fill_color = '#64B5F6'
            status = 'Active (Recent Data)'
            icon = '🔵'
        else:
            color = '#9C27B0'  # Purple for old
            fill_color = '#BA68C8'
            status = 'Inactive (Historical)'
            icon = '🟣'
        
        # Get begin/end dates
        begin_date = str(row.get('begin_date', 'Unknown'))
        end_date = str(row.get('end_date', 'Unknown'))
        
        popup_html = f"""
        <div style='font-family: Arial; min-width: 250px;'>
            <h4 style='margin: 0; color: {color};'>{icon} Rainfall Station</h4>
            <hr style='margin: 5px 0;'>
            <b>ID:</b> {row.get('station_id', 'N/A')}<br>
            <b>District:</b> {row.get('district', 'N/A')}<br>
            <b>Location:</b> {row['lat']:.4f}°N, {row['lon']:.4f}°E<br>
            <b>Elevation:</b> {row.get('elevation', 'N/A')} m<br>
            <hr style='margin: 5px 0;'>
            <b>Status:</b> <span style='color: {color}; font-weight: bold;'>{status}</span><br>
            <b>Data Period:</b><br>
            • Start: {begin_date}<br>
            • End: {end_date}<br>
            <hr style='margin: 5px 0;'>
            <b>Parameters:</b> Daily Rainfall
        </div>
        """
        
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=4,
            color=color,
            fill=True,
            fillColor=fill_color,
            fillOpacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"Rainfall: {row.get('station_id', 'Unknown')} ({status})"
        ).add_to(m)
    
    print(f"  Added {len(rainfall_stations)} rainfall stations")
else:
    print("No rainfall stations data available")

# ============================================================================
# Add Major Met Stations (Large Red Pins with Parameters)
# ============================================================================

if len(major_stations) > 0:
    print("Adding major Met stations with parameters...")
    
    for idx, row in major_stations.iterrows():
        # Get parameters (handle NaN)
        params_daily = str(row.get('parameters_daily', 'N/A'))
        params_hourly = str(row.get('parameters_hourly', 'N/A'))
        obs_times = str(row.get('observation_times', 'N/A'))
        elevation = row.get('elevation', 'N/A')
        
        # Format parameters nicely
        if params_daily != 'nan' and params_daily != 'N/A':
            params_daily_list = params_daily.replace(',', '<br>   • ')
        else:
            params_daily_list = 'N/A'
        
        if params_hourly != 'nan' and params_hourly != 'N/A':
            params_hourly_list = params_hourly.replace(',', '<br>   • ')
        else:
            params_hourly_list = 'N/A'
        
        popup_html = f"""
        <div style='font-family: Arial; min-width: 350px; max-width: 400px;'>
            <h3 style='margin: 0; color: #D32F2F; background: #FFEBEE; padding: 8px; border-radius: 4px;'>
                📍 {row.get('Name', 'Unknown Station')}
            </h3>
            <hr style='margin: 8px 0;'>
            
            <table style='width: 100%; font-size: 13px;'>
                <tr>
                    <td style='padding: 4px; font-weight: bold; width: 40%;'>Station ID:</td>
                    <td style='padding: 4px;'>{row.get('station_id', 'N/A')}</td>
                </tr>
                <tr>
                    <td style='padding: 4px; font-weight: bold;'>Coordinates:</td>
                    <td style='padding: 4px;'>{row['lat']:.4f}°N, {row['lon']:.4f}°E</td>
                </tr>
                <tr>
                    <td style='padding: 4px; font-weight: bold;'>Elevation:</td>
                    <td style='padding: 4px;'>{elevation} m</td>
                </tr>
            </table>
            
            <hr style='margin: 8px 0;'>
            
            <div style='background: #E3F2FD; padding: 8px; border-radius: 4px; margin-bottom: 8px;'>
                <p style='margin: 0 0 4px 0; font-weight: bold; color: #1976D2;'>📊 Daily/Monthly Parameters:</p>
                <p style='margin: 0; font-size: 12px; line-height: 1.6;'>
                    • {params_daily_list}
                </p>
            </div>
            
            <div style='background: #FFF3E0; padding: 8px; border-radius: 4px; margin-bottom: 8px;'>
                <p style='margin: 0 0 4px 0; font-weight: bold; color: #F57C00;'>⏱️ 3-Hourly Parameters:</p>
                <p style='margin: 0; font-size: 12px; line-height: 1.6;'>
                    • {params_hourly_list}
                </p>
            </div>
            
            <div style='background: #F3E5F5; padding: 8px; border-radius: 4px;'>
                <p style='margin: 0 0 4px 0; font-weight: bold; color: #7B1FA2;'>🕐 Observation Times (UTC):</p>
                <p style='margin: 0; font-size: 12px;'>{obs_times}</p>
            </div>
            
            <hr style='margin: 8px 0;'>
            <p style='margin: 0; font-size: 11px; color: #666; text-align: center;'>
                Major Meteorological Station
            </p>
        </div>
        """
        
        # Custom icon for major stations
        icon_html = f"""
        <div style='font-size: 24px; color: #D32F2F; text-shadow: 1px 1px 2px black;'>
            📍
        </div>
        """
        
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=folium.Popup(popup_html, max_width=420),
            tooltip=f"<b>{row.get('Name', 'Met Station')}</b><br>Major Met Station<br>Click for parameters",
            icon=folium.DivIcon(html=icon_html)
        ).add_to(m)
    
    print(f"  Added {len(major_stations)} major Met stations")
else:
    print("No major Met stations to add")

# ============================================================================
# Add Legend
# ============================================================================

legend_html = f"""
<div style='position: fixed; bottom: 50px; right: 50px; width: 320px; 
     background-color: white; z-index: 9999; font-size: 14px;
     border: 2px solid #FF4500; border-radius: 5px; padding: 10px;
     box-shadow: 2px 2px 6px rgba(0,0,0,0.3);'>
    
    <h4 style='margin: 0 0 10px 0; color: #FF4500;'>☀️ Solar Resource Map</h4>
    
    <p style='margin: 5px 0; font-size: 12px;'><b>Grid Cells (10km × 10km)</b></p>
    <p style='margin: 2px 0;'>
        <span style='background: #FF4500; padding: 3px 8px;'>■</span> Excellent
    </p>
    <p style='margin: 2px 0;'>
        <span style='background: #FF8C00; padding: 3px 8px;'>■</span> Very Good
    </p>
    <p style='margin: 2px 0;'>
        <span style='background: #FFD700; padding: 3px 8px;'>■</span> Good
    </p>
    <p style='margin: 2px 0;'>
        <span style='background: #FFFF99; padding: 3px 8px;'>■</span> Moderate
    </p>
    
    <hr style='margin: 10px 0;'>
    
    <p style='margin: 5px 0; font-size: 12px;'><b>Weather Stations</b></p>
    <p style='margin: 2px 0;'>
        <span style='color: #D32F2F; font-size: 20px;'>📍</span> Major Met ({len(major_stations)}) - All parameters
    </p>
    <p style='margin: 2px 0;'>
        <span style='color: #2196F3; font-size: 16px;'>●</span> Active Rainfall ({active_count}) - 2023+
    </p>
    <p style='margin: 2px 0;'>
        <span style='color: #9C27B0; font-size: 16px;'>●</span> Old Rainfall ({inactive_count}) - Historical
    </p>
    
    <hr style='margin: 10px 0;'>
    
    <p style='margin: 0; font-size: 11px; color: #666;'>
        Click stations for details<br>
        Major stations show all parameters
    </p>
</div>
"""

m.get_root().html.add_child(folium.Element(legend_html))

# Add title
title_html = f"""
<div style='position: fixed; top: 10px; left: 50px; width: 650px;
     background-color: white; z-index: 9999; font-size: 18px;
     border: 2px solid #FF4500; border-radius: 5px; padding: 10px;
     box-shadow: 2px 2px 6px rgba(0,0,0,0.3);'>
    <p style='margin: 0; font-weight: bold; color: #FF4500;'>
        ☀️ Sri Lanka Solar Resource Map - Complete Weather Station Network
    </p>
    <p style='margin: 5px 0 0 0; font-size: 12px; color: #7F8C8D;'>
        📍 {len(major_stations)} Major Met • 🔵 {active_count} Active Rainfall • 🟣 {inactive_count} Old Rainfall • {len(solar_grids)} Solar Grids
    </p>
</div>
"""

m.get_root().html.add_child(folium.Element(title_html))

folium.LayerControl().add_to(m)

# ============================================================================
# Save
# ============================================================================

output_path = "outputs/figures/grids/solar_weather_complete_map.html"
Path(output_path).parent.mkdir(parents=True, exist_ok=True)
m.save(output_path)

print("\n" + "="*70)
print("✓ MAP CREATED SUCCESSFULLY!")
print("="*70)
print(f"\nSaved to: {output_path}")
print(f"\nMap includes:")
print(f"  • {len(solar_grids)} solar grids (color-coded)")
print(f"  • 📍 {len(major_stations)} major Met stations (red pins - all parameters)")
print(f"  • 🔵 {active_count} active rainfall stations (blue circles - 2023+)")
print(f"  • 🟣 {inactive_count} old rainfall stations (purple circles - historical)")
print(f"\nStation types:")
print(f"  📍 Major Met: Temperature, Wind, Pressure, RH, Rainfall, etc.")
print(f"  🔵 Active: Recent rainfall data (still operational)")
print(f"  🟣 Old: Historical rainfall data (discontinued)")
print(f"\nOpen in browser to explore!")
