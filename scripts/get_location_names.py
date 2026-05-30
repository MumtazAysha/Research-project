"""
Get exact location names using Google Maps Geocoding API
Much more accurate than Nominatim for Sri Lanka
"""
import pandas as pd
import googlemaps
from tqdm import tqdm
import time

# ⚠️ REPLACE THIS WITH YOUR GOOGLE MAPS API KEY
GOOGLE_API_KEY = "AIzaSyD07sbzMiYSXoTsByLl4M8Z-fqovp_mrlE"  # Get from: https://console.cloud.google.com/

def get_exact_location_google(lat, lon, gmaps_client):
    """Get detailed location using Google Maps"""
    
    try:
        # Reverse geocode
        results = gmaps_client.reverse_geocode((lat, lon), language='en')
        
        if not results:
            return None
        
        # Get the most specific result (first one is usually most detailed)
        result = results[0]
        address_components = result.get('address_components', [])
        formatted_address = result.get('formatted_address', 'Unknown')
        
        # Extract components
        location_info = {
            'neighborhood': None,
            'locality': None,
            'sublocality': None,
            'city': None,
            'district': None,
            'province': None,
            'postal_code': None
        }
        
        for component in address_components:
            types = component.get('types', [])
            name = component.get('long_name', '')
            
            if 'neighborhood' in types:
                location_info['neighborhood'] = name
            elif 'sublocality' in types or 'sublocality_level_1' in types:
                location_info['sublocality'] = name
            elif 'locality' in types:
                location_info['locality'] = name
            elif 'administrative_area_level_2' in types:
                location_info['district'] = name
            elif 'administrative_area_level_1' in types:
                location_info['province'] = name
            elif 'postal_code' in types:
                location_info['postal_code'] = name
        
        # Determine most specific location name
        location_name = (
            location_info['neighborhood'] or
            location_info['sublocality'] or
            location_info['locality'] or
            location_info['district'] or
            'Unknown'
        )
        
        return {
            'location_name': location_name,
            'locality': location_info['locality'] or 'Unknown',
            'district': location_info['district'] or 'Unknown',
            'province': location_info['province'] or 'Unknown',
            'postal_code': location_info['postal_code'] or 'N/A',
            'formatted_address': formatted_address
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# Load coordinates
coords = pd.read_csv('data/bronze/metadata/grid_coordinates_all.csv')

print("="*70)
print("GETTING EXACT LOCATIONS USING GOOGLE MAPS GEOCODING API")
print("="*70)
print(f"Total cells to geocode: {len(coords)}")
print("Estimated cost: $0 (within free tier)\n")

# Initialize Google Maps client
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

# Add location columns
coords['location_name'] = ''
coords['locality'] = ''
coords['district'] = ''
coords['province'] = ''
coords['postal_code'] = ''
coords['formatted_address'] = ''

# Process each cell
successful = 0
failed = 0

for idx, row in tqdm(coords.iterrows(), total=len(coords), desc="Geocoding"):
    lat = row['centroid_lat']
    lon = row['centroid_lon']
    cell_type = row['cell_type']
    
    # Skip ocean cells or process them differently
    if cell_type == 'ocean':
        coords.at[idx, 'location_name'] = 'Indian Ocean'
        coords.at[idx, 'locality'] = 'Ocean'
        coords.at[idx, 'district'] = 'N/A'
        coords.at[idx, 'province'] = 'N/A'
        coords.at[idx, 'formatted_address'] = 'Indian Ocean'
        continue
    
    # Get location from Google
    location_info = get_exact_location_google(lat, lon, gmaps)
    
    if location_info:
        coords.at[idx, 'location_name'] = location_info['location_name']
        coords.at[idx, 'locality'] = location_info['locality']
        coords.at[idx, 'district'] = location_info['district']
        coords.at[idx, 'province'] = location_info['province']
        coords.at[idx, 'postal_code'] = location_info['postal_code']
        coords.at[idx, 'formatted_address'] = location_info['formatted_address']
        successful += 1
    else:
        coords.at[idx, 'location_name'] = 'Unknown'
        coords.at[idx, 'district'] = 'Unknown'
        failed += 1
    
    # Small delay to respect rate limits (not strictly necessary with API key)
    time.sleep(0.1)

# Save results
output_file = 'data/bronze/metadata/grid_coordinates_with_exact_locations.csv'
coords.to_csv(output_file, index=False)

print("\n" + "="*70)
print("GEOCODING COMPLETE")
print("="*70)
print(f"✓ Successful: {successful}")
print(f"✗ Failed: {failed}")
print(f"✓ Saved to: {output_file}\n")

# Show statistics
print("Location Name Distribution:")
print(coords['location_name'].value_counts().head(20))

print("\n" + "="*70)
print("SAMPLE RESULTS (First 30 Land/Coastal Cells)")
print("="*70)
sample = coords[coords['cell_type'].isin(['land', 'coastal'])].head(30)
print(sample[['grid_id', 'location_name', 'locality', 'district', 'province']].to_string(index=False))
