"""
Advanced resource classification using distance-based interpolation
Mimics how the SLSEA maps were actually created
"""
import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# ============ SOLAR RESOURCE SEED POINTS (from map analysis) ============
solar_seed_points = [
    # Excellent zones (RED on map - 2,042-2,106 kWh/m²)
    {'lat': 9.75, 'lon': 80.05, 'ghi': 2090, 'name': 'Jaffna'},
    {'lat': 9.30, 'lon': 80.40, 'ghi': 2085, 'name': 'Kilinochchi'},
    {'lat': 9.00, 'lon': 79.85, 'ghi': 2095, 'name': 'Mannar'},
    {'lat': 8.50, 'lon': 81.20, 'ghi': 2070, 'name': 'Trincomalee'},
    {'lat': 7.80, 'lon': 81.70, 'ghi': 2060, 'name': 'Batticaloa'},
    {'lat': 7.20, 'lon': 81.75, 'ghi': 2055, 'name': 'Ampara coast'},
    {'lat': 6.15, 'lon': 81.15, 'ghi': 2080, 'name': 'Hambantota'},
    
    # Very Good zones (ORANGE - 2,002-2,039)
    {'lat': 8.15, 'lon': 79.85, 'ghi': 2020, 'name': 'Puttalam'},
    
    # Good zones (YELLOW - 1,904-1,966)
    {'lat': 8.30, 'lon': 80.40, 'ghi': 1935, 'name': 'Anuradhapura'},
    {'lat': 6.05, 'lon': 80.25, 'ghi': 1920, 'name': 'Galle'},
    {'lat': 5.95, 'lon': 80.55, 'ghi': 1915, 'name': 'Matara'},
    
    # Moderate zones (LIGHT GREEN - 1,830-1,903)
    {'lat': 7.30, 'lon': 80.60, 'ghi': 1865, 'name': 'Kandy periphery'},
    
    # Low zones (CYAN/BLUE - <1,766)
    {'lat': 6.95, 'lon': 80.70, 'ghi': 1600, 'name': 'Nuwara Eliya'},
]

# ============ WIND RESOURCE SEED POINTS ============
wind_seed_points = [
    # Excellent zones (RED - >9.0 m/s)
    {'lat': 9.00, 'lon': 79.80, 'speed': 9.3, 'name': 'Mannar core'},
    {'lat': 8.15, 'lon': 79.82, 'speed': 9.1, 'name': 'Puttalam peak'},
    
    # Very Good zones (ORANGE - 8.0-8.5)
    {'lat': 9.65, 'lon': 80.10, 'speed': 8.3, 'name': 'Jaffna'},
    {'lat': 9.15, 'lon': 79.90, 'speed': 8.4, 'name': 'Mannar extended'},
    
    # Good zones (YELLOW - 7.0-7.5)
    {'lat': 8.05, 'lon': 79.90, 'speed': 7.3, 'name': 'Puttalam coast'},
    {'lat': 9.35, 'lon': 80.35, 'speed': 7.1, 'name': 'Kilinochchi'},
    {'lat': 6.25, 'lon': 81.10, 'speed': 7.8, 'name': 'Hambantota'},
    
    # Moderate zones (CYAN - 5.0-6.0)
    {'lat': 8.40, 'lon': 81.25, 'speed': 5.5, 'name': 'Trincomalee'},
    {'lat': 8.20, 'lon': 80.50, 'speed': 5.2, 'name': 'Anuradhapura'},
    
    # Low zones (BLUE - <5.0)
    {'lat': 7.00, 'lon': 80.65, 'speed': 3.8, 'name': 'Central highlands'},
    {'lat': 6.05, 'lon': 80.25, 'speed': 4.3, 'name': 'Southern coast'},
]

# ============ OFFSHORE WIND SEED POINTS ============
offshore_seed_points = [
    # Excellent (RED - >9.0)
    {'lat': 9.50, 'lon': 79.70, 'speed': 9.5, 'name': 'North offshore'},
    {'lat': 9.00, 'lon': 79.60, 'speed': 9.4, 'name': 'NW offshore'},
    
    # Very Good (ORANGE - 8.0-9.0)
    {'lat': 7.50, 'lon': 79.70, 'speed': 8.6, 'name': 'West offshore'},
    
    # Good (YELLOW - 7.0-8.0)
    {'lat': 8.00, 'lon': 81.80, 'speed': 7.5, 'name': 'East offshore'},
    
    # Moderate (GREEN - 5.0-7.0)
    {'lat': 6.00, 'lon': 80.50, 'speed': 6.2, 'name': 'South offshore'},
]

def classify_solar_interpolated(lat, lon):
    """Classify solar using distance-weighted interpolation"""
    
    # Calculate weighted average based on inverse distance
    total_weight = 0
    weighted_ghi = 0
    
    for seed in solar_seed_points:
        dist = haversine_distance(lat, lon, seed['lat'], seed['lon'])
        
        # Inverse distance weighting (closer = more influence)
        # Add small value to avoid division by zero
        weight = 1 / (dist + 0.1) ** 2
        
        total_weight += weight
        weighted_ghi += seed['ghi'] * weight
    
    # Calculate interpolated GHI
    ghi = weighted_ghi / total_weight
    
    # Classify based on GHI value
    if ghi >= 2042:
        return "Excellent", int(ghi), "2,042-2,106 kWh/m²"
    elif ghi >= 2002:
        return "Very Good", int(ghi), "2,002-2,039 kWh/m²"
    elif ghi >= 1904:
        return "Good", int(ghi), "1,904-1,966 kWh/m²"
    elif ghi >= 1830:
        return "Moderate", int(ghi), "1,830-1,903 kWh/m²"
    elif ghi >= 1766:
        return "Low", int(ghi), "1,766-1,829 kWh/m²"
    else:
        return "Very Low", int(ghi), "<1,766 kWh/m²"

def classify_wind_interpolated(lat, lon):
    """Classify wind using distance-weighted interpolation"""
    
    total_weight = 0
    weighted_speed = 0
    
    for seed in wind_seed_points:
        dist = haversine_distance(lat, lon, seed['lat'], seed['lon'])
        weight = 1 / (dist + 0.1) ** 2
        
        total_weight += weight
        weighted_speed += seed['speed'] * weight
    
    speed = weighted_speed / total_weight
    
    # Classify based on wind speed
    if speed >= 9.0:
        return "Excellent", round(speed, 1), ">9.0 m/s"
    elif speed >= 8.0:
        return "Very Good", round(speed, 1), "8.0-8.5 m/s"
    elif speed >= 7.0:
        return "Good", round(speed, 1), "7.0-7.5 m/s"
    elif speed >= 6.0:
        return "Moderate", round(speed, 1), "6.0-7.0 m/s"
    elif speed >= 5.0:
        return "Low-Moderate", round(speed, 1), "5.0-6.0 m/s"
    else:
        return "Low", round(speed, 1), "<5.0 m/s"

def classify_offshore_interpolated(lat, lon, cell_type):
    """Classify offshore wind using interpolation"""
    
    if cell_type not in ['ocean', 'coastal']:
        return "N/A", 0, "Not applicable (land)"
    
    total_weight = 0
    weighted_speed = 0
    
    for seed in offshore_seed_points:
        dist = haversine_distance(lat, lon, seed['lat'], seed['lon'])
        weight = 1 / (dist + 0.1) ** 2
        
        total_weight += weight
        weighted_speed += seed['speed'] * weight
    
    speed = weighted_speed / total_weight
    
    if speed >= 9.0:
        return "Excellent", round(speed, 1), ">9.0 m/s"
    elif speed >= 8.0:
        return "Very Good", round(speed, 1), "8.0-9.0 m/s"
    elif speed >= 7.0:
        return "Good", round(speed, 1), "7.0-8.0 m/s"
    elif speed >= 6.0:
        return "Moderate", round(speed, 1), "6.0-7.0 m/s"
    else:
        return "Low", round(speed, 1), "<6.0 m/s"

def classify_hydro_resource(lat, lon, district):
    """Hydro classification by district"""
    
    if pd.isna(district) or district == 'Unknown' or district == 'N/A' or district == 'Ocean':
        return "N/A", 0, "No data"
    
    hydro_potential = {
        'Ratnapura': ('Excellent', 272),
        'Nuwara Eliya': ('Excellent', 240),
        'Badulla': ('Excellent', 214),
        'Kandy': ('Very Good', 128),
        'Kegalle': ('Very Good', 70),
        'Matale': ('Good', 50),
        'Ampara': ('Good', 41),
        'Monaragala': ('Good', 41),
        'Anuradhapura': ('Good', 41),
        'Hambantota': ('Good', 50),
        'Kalutara': ('Moderate', 22),
        'Galle': ('Moderate', 21),
        'Matara': ('Moderate', 27),
        'Kurunegala': ('Moderate', 30),
        'Polonnaruwa': ('Moderate', 25),
        'Trincomalee': ('Low', 10),
        'Batticaloa': ('Low', 15),
        'Puttalam': ('Low', 8),
        'Gampaha': ('Low', 5),
        'Colombo': ('Low', 0),
        'Jaffna': ('Low', 0),
        'Kilinochchi': ('Low', 0),
        'Mannar': ('Low', 0),
        'Mullaitivu': ('Low', 0),
        'Vavuniya': ('Low', 5),
    }
    
    district_str = str(district).lower()
    
    for dist_name, (rating, mw) in hydro_potential.items():
        if dist_name.lower() in district_str:
            return rating, mw, f"{mw} MW potential"
    
    return "Low", 0, "Negligible potential"

# ============ MAIN PROCESSING ============
print("Loading grid data...")
coords = pd.read_csv('data/bronze/metadata/grid_coordinates_with_exact_locations.csv')

print(f"Classifying {len(coords)} grid cells using ADVANCED INTERPOLATION...")
print("This method mimics how GIS creates heat maps!\n")

resources = []

for idx, row in coords.iterrows():
    lat = row['centroid_lat']
    lon = row['centroid_lon']
    cell_type = row['cell_type']
    district = row['district']
    
    # Interpolated classifications
    solar_rating, solar_ghi, solar_range = classify_solar_interpolated(lat, lon)
    wind_rating, wind_speed, wind_range = classify_wind_interpolated(lat, lon)
    offshore_rating, offshore_speed, offshore_range = classify_offshore_interpolated(lat, lon, cell_type)
    hydro_rating, hydro_mw, hydro_desc = classify_hydro_resource(lat, lon, district)
    
    # Recommendations
    recommendations = []
    if solar_rating in ['Excellent', 'Very Good']:
        recommendations.append('Solar')
    if wind_rating in ['Excellent', 'Very Good']:
        recommendations.append('Wind')
    if offshore_rating in ['Excellent', 'Very Good'] and cell_type in ['ocean', 'coastal']:
        recommendations.append('Offshore Wind')
    if hydro_rating in ['Excellent', 'Very Good']:
        recommendations.append('Hydro')
    
    if not recommendations:
        if solar_rating == 'Good':
            recommendations.append('Solar')
        elif wind_rating == 'Good':
            recommendations.append('Wind')
        else:
            recommendations.append('Solar (Default)')
    
    recommended = ' + '.join(recommendations)
    
    resources.append({
        'grid_id': row['grid_id'],
        'solar_rating': solar_rating,
        'solar_ghi': solar_ghi,
        'solar_range': solar_range,
        'wind_rating': wind_rating,
        'wind_speed': wind_speed,
        'wind_range': wind_range,
        'offshore_wind_rating': offshore_rating,
        'offshore_wind_speed': offshore_speed,
        'offshore_wind_range': offshore_range,
        'hydro_rating': hydro_rating,
        'hydro_mw': hydro_mw,
        'hydro_potential': hydro_desc,
        'recommended_energy': recommended
    })
    
    if (idx + 1) % 100 == 0:
        print(f"  Processed {idx + 1}/{len(coords)} cells...")

# Save
resources_df = pd.DataFrame(resources)
final_df = coords.merge(resources_df, on='grid_id', how='left')

output_file = 'data/bronze/metadata/grid_with_energy_resources.csv'
final_df.to_csv(output_file, index=False)

print(f"\n✓ ADVANCED classification complete!")
print(f"✓ Saved to: {output_file}")

# Statistics
print("\n" + "="*70)
print("INTERPOLATED RESOURCE SUMMARY")
print("="*70)

print("\nSolar Resource Distribution:")
print(final_df['solar_rating'].value_counts())

print("\nWind Resource Distribution:")
print(final_df['wind_rating'].value_counts())

print("\nTop Recommended Energy Types:")
print(final_df['recommended_energy'].value_counts().head(10))

print("\n" + "="*70)
print("KEY LOCATIONS VERIFICATION:")
print("="*70)

# Verify known locations
for name in ['Jaffna', 'Mannar', 'Kilinochchi', 'Hambantota', 'Puttalam', 'Trincomalee']:
    cells = final_df[final_df['location_name'].str.contains(name, case=False, na=False)]
    if len(cells) > 0:
        sample = cells.iloc[0]
        print(f"\n{name}:")
        print(f"  Solar: {sample['solar_rating']} ({sample['solar_ghi']} kWh/m²)")
        print(f"  Wind: {sample['wind_rating']} ({sample['wind_speed']} m/s)")

print("\n" + "="*70) 