"""
Generate 5x5 grid covering Sri Lanka
"""
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import box, Point
import folium
from pathlib import Path

class SriLankaGrid:
    """Creates and manages 5x5 grid for Sri Lanka"""
    
    def __init__(self):
        # Sri Lanka bounding box
        self.min_lat = 5.9
        self.max_lat = 9.9
        self.min_lon = 79.5
        self.max_lon = 81.9
        self.grid_rows = 5
        self.grid_cols = 5
        
    def create_grid(self):
        """Create 5x5 grid cells"""
        
        lon_step = (self.max_lon - self.min_lon) / self.grid_cols
        lat_step = (self.max_lat - self.min_lat) / self.grid_rows
        
        grid_cells = []
        grid_data = []
        
        for i in range(self.grid_rows):
            for j in range(self.grid_cols):
                # Create grid cell polygon
                min_x = self.min_lon + j * lon_step
                max_x = self.min_lon + (j + 1) * lon_step
                min_y = self.min_lat + i * lat_step
                max_y = self.min_lat + (i + 1) * lat_step
                
                cell = box(min_x, min_y, max_x, max_y)
                
                # Calculate centroid
                centroid = cell.centroid
                
                grid_data.append({
                    'grid_id': f'grid_{i}_{j}',
                    'row': i,
                    'col': j,
                    'centroid_lat': centroid.y,
                    'centroid_lon': centroid.x,
                    'geometry': cell
                })
        
        # Create GeoDataFrame
        grid_gdf = gpd.GeoDataFrame(grid_data, crs="EPSG:4326")
        
        return grid_gdf
    
    def save_grid(self, grid_gdf, output_dir='data/bronze/metadata'):
        """Save grid to files"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save as GeoJSON
        grid_gdf.to_file(f'{output_dir}/grid_cells.geojson', driver='GeoJSON')
        
        # Save coordinates as CSV
        coords_df = grid_gdf[['grid_id', 'row', 'col', 'centroid_lat', 'centroid_lon']]
        coords_df.to_csv(f'{output_dir}/grid_coordinates.csv', index=False)
        
        print(f"✓ Grid saved to {output_dir}")
        return coords_df
    
    def visualize_grid(self, grid_gdf, save_path='outputs/figures/grids/sri_lanka_grid.html'):
        """Create interactive map of grid"""
        
        # Center of Sri Lanka
        center_lat = (self.min_lat + self.max_lat) / 2
        center_lon = (self.min_lon + self.max_lon) / 2
        
        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=8)
        
        # Add grid cells
        for idx, row in grid_gdf.iterrows():
            folium.GeoJson(
                row['geometry'],
                style_function=lambda x: {
                    'fillColor': 'lightblue',
                    'color': 'blue',
                    'weight': 2,
                    'fillOpacity': 0.3
                },
                tooltip=row['grid_id']
            ).add_to(m)
            
            # Add centroid marker
            folium.CircleMarker(
                location=[row['centroid_lat'], row['centroid_lon']],
                radius=3,
                color='red',
                fill=True,
                popup=f"{row['grid_id']}<br>Lat: {row['centroid_lat']:.2f}<br>Lon: {row['centroid_lon']:.2f}"
            ).add_to(m)
        
        # Save map
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        m.save(save_path)
        print(f"✓ Map saved to {save_path}")
        
        return m

# Main execution
if __name__ == "__main__":
    print("Creating 5x5 grid for Sri Lanka...")
    
    grid_gen = SriLankaGrid()
    grid_gdf = grid_gen.create_grid()
    
    print(f"\n✓ Created {len(grid_gdf)} grid cells")
    print("\nGrid Cell Sample:")
    print(grid_gdf.head())
    
    # Save grid
    coords_df = grid_gen.save_grid(grid_gdf)
    
    # Visualize
    grid_gen.visualize_grid(grid_gdf)
    
    print("\n✓ Grid creation complete!")
    print(f"✓ Total grid cells: {len(grid_gdf)}")
