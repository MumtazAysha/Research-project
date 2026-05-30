"""
Create continuous raster visualization of wind speeds (GWA-style)
"""
import matplotlib
matplotlib.use('Agg') 
import rasterio
from rasterio.plot import show
from rasterio.mask import mask
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import geopandas as gpd
from pathlib import Path

print("Creating continuous wind resource visualization...")

# File paths
project_root = Path(__file__).parent.parent 
tif_path = project_root / 'LKA_wind-speed_100m (2).tif'
output_path = project_root / 'outputs' / 'figures' / 'wind_continuous_map.png'

# Create output directory
output_path.parent.mkdir(parents=True, exist_ok=True)

# Load Sri Lanka boundary (to clip the raster)
# You can use your grid file or create a boundary
try:
    grid_gdf = gpd.read_file('data/bronze/metadata/grid_cells_all.geojson')
    # Create Sri Lanka boundary by dissolving all grid cells
    sl_boundary = grid_gdf.dissolve()
except:
    sl_boundary = None

# Create GWA-style color scheme
# Blue → Green → Yellow → Orange → Red → Dark Red
colors = [
    '#D0E7FF',  # Very light blue (< 4 m/s)
    '#90EE90',  # Light green (4-5)
    '#FFFF99',  # Light yellow (5-6)
    '#FFD700',  # Gold (6-7)
    '#FFA500',  # Orange (7-8)
    '#FF6347',  # Tomato/Orange-red (8-9)
    '#FF4500',  # Red-Orange (9-10)
    '#8B0000'   # Dark red (>10)
]

# Create colormap
cmap = LinearSegmentedColormap.from_list('wind_gwa', colors, N=256)

# Open and display the TIF
with rasterio.open(str(tif_path)) as src:
    print(f"Processing TIF: {src.width} x {src.height} pixels")
    
    # If we have boundary, clip to Sri Lanka only
    if sl_boundary is not None:
        print("Clipping to Sri Lanka boundary...")
        out_image, out_transform = mask(src, sl_boundary.geometry, crop=True)
        data = out_image[0]
        
        # Set invalid values to NaN
        data[data < 0] = float('nan')
        data[data > 50] = float('nan')
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 16), dpi=150)
        
        # Plot with custom extent
        from rasterio.plot import show as rshow
        img = ax.imshow(data, cmap=cmap, vmin=3, vmax=12, 
                       extent=[out_transform[2], out_transform[2] + out_transform[0]*data.shape[1],
                               out_transform[5] + out_transform[4]*data.shape[0], out_transform[5]],
                       interpolation='bilinear')
    else:
        # Plot full TIF
        fig, ax = plt.subplots(figsize=(12, 16), dpi=150)
        img = show(src, ax=ax, cmap=cmap, vmin=3, vmax=12, interpolation='bilinear')
    
    # Styling
    ax.set_title('Sri Lanka Wind Resource Map - 100m Height\nContinuous Visualization (Global Wind Atlas Style)', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Longitude (°E)', fontsize=12)
    ax.set_ylabel('Latitude (°N)', fontsize=12)
    
    # Add colorbar
    cbar = plt.colorbar(img if sl_boundary is None else plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=3, vmax=12)), 
                       ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Wind Speed (m/s) at 100m Height', fontsize=12, fontweight='bold')
    
    # Add wind speed category labels on colorbar
    cbar.ax.text(1.5, 11, 'Excellent', fontsize=10, va='center')
    cbar.ax.text(1.5, 8.5, 'Very Good', fontsize=10, va='center')
    cbar.ax.text(1.5, 7, 'Good', fontsize=10, va='center')
    cbar.ax.text(1.5, 5.5, 'Moderate', fontsize=10, va='center')
    cbar.ax.text(1.5, 4, 'Fair', fontsize=10, va='center')
    
    # Add data source
    plt.text(0.02, 0.02, 'Data Source: Global Wind Atlas 3.0 | DTU', 
             transform=ax.transAxes, fontsize=10, style='italic',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
    print(f"\n✓ Continuous wind map saved to: {output_path}")
    
    # Also create an interactive HTML version using folium
    print("\nCreating interactive continuous map...")

# Create interactive version with raster overlay
import folium
from folium import raster_layers
import numpy as np

print("Creating interactive HTML map with continuous data...")

# Load raster data
with rasterio.open(str(tif_path)) as src:
    # Read the data
    wind_data = src.read(1)
    bounds = src.bounds
    
    # Replace invalid values
    wind_data[wind_data < 0] = np.nan
    wind_data[wind_data > 50] = np.nan
    
    # Create folium map
    center_lat = (bounds.bottom + bounds.top) / 2
    center_lon = (bounds.left + bounds.right) / 2
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles='OpenStreetMap')
    
    # Add image overlay
    folium.raster_layers.ImageOverlay(
        image=wind_data,
        bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
        colormap=lambda x: (
            (208, 231, 255) if x < 4 else
            (144, 238, 144) if x < 5 else
            (255, 255, 153) if x < 6 else
            (255, 215, 0) if x < 7 else
            (255, 165, 0) if x < 8 else
            (255, 99, 71) if x < 9 else
            (255, 69, 0) if x < 10 else
            (139, 0, 0)
        ),
        opacity=0.7,
        name='Wind Speed'
    ).add_to(m)
    
    # Add title
    title_html = '''
    <div style="position: fixed; top: 10px; left: 50px; width: 520px; 
                background-color: white; z-index: 9999; font-size: 18px;
                border: 2px solid #8B0000; border-radius: 5px; padding: 10px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <p style="margin: 0; font-weight: bold; color: #8B0000;">
            💨 Sri Lanka Wind Resource - Continuous (250m Resolution)
        </p>
        <p style="margin: 5px 0 0 0; font-size: 12px; color: #7F8C8D;">
            Global Wind Atlas Data • Direct Raster Visualization
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save HTML
    html_output = project_root / 'outputs' / 'figures' / 'wind_continuous_interactive.html'
    m.save(str(html_output))
    print(f"✓ Interactive map saved to: {html_output}")

print("\n" + "="*70)
print("✓ Continuous wind visualization complete!")
print(f"✓ Static image: {output_path}")
print(f"✓ Interactive HTML: {html_output}")
print("="*70)
