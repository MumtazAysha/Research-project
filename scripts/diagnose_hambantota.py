"""
Diagnostic script to check actual wind speed values in Hambantota region
"""
import rasterio
import numpy as np
from pathlib import Path

print("="*70)
print("ANALYZING HAMBANTOTA REGION WIND SPEEDS")
print("="*70)

# File is in project root
project_root = Path(__file__).parent.parent
tif_path = project_root / 'LKA_wind-speed_100m (2).tif'

if not tif_path.exists():
    # Try alternate name
    tif_path = project_root / 'LKA_wind-speed_100m-2.tif'

if not tif_path.exists():
    print(f"\n❌ ERROR: Could not find wind TIF file at: {project_root}")
    print("\nFiles in project root:")
    import os
    for item in os.listdir(project_root):
        if item.endswith('.tif'):
            print(f"  - {item}")
    exit(1)

print(f"\n✓ Using file: {tif_path}")
print("="*70)

with rasterio.open(str(tif_path)) as src:
    print(f"\nTIF File Info:")
    print(f"  CRS: {src.crs}")
    print(f"  Bounds: {src.bounds}")
    print(f"  NoData value: {src.nodata}")
    
    # Hambantota region test points (circled area)
    test_points = [
        (81.1, 6.1, "Hambantota West"),
        (81.2, 6.2, "Hambantota Central"),
        (81.3, 6.3, "Hambantota East"),
        (81.4, 6.4, "Hambantota North"),
        (80.9, 6.15, "Hambantota Southwest"),
    ]
    
    print(f"\n{'Location':<25} {'Lon':<10} {'Lat':<10} {'Wind Speed'}")
    print("-"*70)
    
    for lon, lat, name in test_points:
        try:
            value = list(src.sample([(lon, lat)]))[0][0]
            
            if value < 0 or value > 50:
                wind_speed = "NoData"
            else:
                wind_speed = f"{value:.2f} m/s"
            
            print(f"{name:<25} {lon:<10.2f} {lat:<10.2f} {wind_speed}")
            
        except Exception as e:
            print(f"{name:<25} {lon:<10.2f} {lat:<10.2f} ERROR")
    
    # Regional statistics for Hambantota
    print(f"\n{'='*70}")
    print("HAMBANTOTA REGION ANALYSIS (Circled Area)")
    print("="*70)
    
    try:
        window = rasterio.windows.from_bounds(
            left=80.8, bottom=6.0, right=81.5, top=6.5,
            transform=src.transform
        )
        
        data = src.read(1, window=window)
        valid_data = data[(data >= 0) & (data < 50)]
        
        if len(valid_data) > 0:
            mean_speed = valid_data.mean()
            
            print(f"\nStatistics:")
            print(f"  Valid pixels: {len(valid_data)}")
            print(f"  Min: {valid_data.min():.2f} m/s")
            print(f"  Max: {valid_data.max():.2f} m/s")
            print(f"  Mean: {mean_speed:.2f} m/s ⭐")
            print(f"  Median: {np.median(valid_data):.2f} m/s")
            
            print(f"\nDistribution:")
            total = len(valid_data)
            print(f"  < 4.0 m/s:  {np.sum(valid_data < 4.0):>5} ({np.sum(valid_data < 4.0)/total*100:>5.1f}%)")
            print(f"  4.0-5.5:    {np.sum((valid_data >= 4.0) & (valid_data < 5.5)):>5} ({np.sum((valid_data >= 4.0) & (valid_data < 5.5))/total*100:>5.1f}%)")
            print(f"  5.5-6.5:    {np.sum((valid_data >= 5.5) & (valid_data < 6.5)):>5} ({np.sum((valid_data >= 5.5) & (valid_data < 6.5))/total*100:>5.1f}%)")
            print(f"  6.5-7.5:    {np.sum((valid_data >= 6.5) & (valid_data < 7.5)):>5} ({np.sum((valid_data >= 6.5) & (valid_data < 7.5))/total*100:>5.1f}%)")
            print(f"  7.5-8.5:    {np.sum((valid_data >= 7.5) & (valid_data < 8.5)):>5} ({np.sum((valid_data >= 7.5) & (valid_data < 8.5))/total*100:>5.1f}%)")
            print(f"  ≥ 8.5 m/s:  {np.sum(valid_data >= 8.5):>5} ({np.sum(valid_data >= 8.5)/total*100:>5.1f}%)")
            
            # What color should it be?
            print(f"\n{'='*70}")
            if mean_speed >= 8.5:
                color = "🔴 Dark Red (Excellent)"
                rating = "Excellent"
            elif mean_speed >= 7.5:
                color = "🟠 Orange-Red (Very Good)"
                rating = "Very Good"
            elif mean_speed >= 6.5:
                color = "🟠 Orange (Good)"
                rating = "Good"
            elif mean_speed >= 5.5:
                color = "🟡 Gold/Yellow (Moderate)"
                rating = "Moderate"
            elif mean_speed >= 4.0:
                color = "🟡 Light Yellow (Fair)"
                rating = "Fair"
            else:
                color = "⚪ Gray (Poor)"
                rating = "Poor"
            
            print(f"Expected Map Color: {color}")
            print(f"Rating: {rating}")
            print("="*70)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")

print()
