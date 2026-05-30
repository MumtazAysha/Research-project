"""
Generate 10km x 10km grid cells covering Sri Lanka (100 km² per cell)
With land/ocean classification
"""
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import box, Point
import folium
from pathlib import Path
import math
import requests
from io import BytesIO

class SriLankaGrid:
    """Creates 10km x 10km grid cells for Sri Lanka with land/ocean filtering"""
    
    def __init__(self):
        # Sri Lanka accurate boundaries
        # From supervisor: 5°55′N to 9°51′N, 79°41′E to 81°53′E
        self.min_lat = 5.0 + 55.0/60.0  # 5°55' = 5.917°N
        self.max_lat = 9.0 + 51.0/60.0  # 9°51' = 9.850°N
        self.min_lon = 79.0 + 41.0/60.0  # 79°41' = 79.683°E
        self.max_lon = 81.0 + 53.0/60.0  # 81°53' = 81.883°E
        
        # Add 10km buffer on all sides (in degrees)
        buffer_lat = self.km_to_degrees_lat(10)
        buffer_lon_min = self.km_to_degrees_lon(10, self.min_lat)
        buffer_lon_max = self.km_to_degrees_lon(10, self.max_lat)
        buffer_lon = max(buffer_lon_min, buffer_lon_max)
        
        self.min_lat_buffered = self.min_lat - buffer_lat
        self.max_lat_buffered = self.max_lat + buffer_lat
        self.min_lon_buffered = self.min_lon - buffer_lon
        self.max_lon_buffered = self.max_lon + buffer_lon
        
        # Grid cell size: 10km x 10km
        self.cell_size_km = 10
        
        # Sri Lanka boundary (will be loaded)
        self.sri_lanka_boundary = None
        
    def km_to_degrees_lat(self, km):
        """Convert km to degrees latitude (constant: ~111km per degree)"""
        return km / 111.0
    
    def km_to_degrees_lon(self, km, latitude):
        """Convert km to degrees longitude (varies by latitude)"""
        return km / (111.0 * math.cos(math.radians(latitude)))
    
    def load_sri_lanka_boundary(self):
        """Load Sri Lanka boundary from Natural Earth data"""
        print("\nLoading Sri Lanka boundary...")
        
        try:
            # Try to load from Natural Earth (global country boundaries)
            world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
            sri_lanka = world[world.name == 'Sri Lanka']
            
            if len(sri_lanka) > 0:
                self.sri_lanka_boundary = sri_lanka.geometry.iloc[0]
                print("✓ Boundary loaded from Natural Earth dataset")
            else:
                print("⚠ Sri Lanka not found in dataset, will use bounding box")
                # Fallback: use simple bounding box
                self.sri_lanka_boundary = box(
                    self.min_lon, self.min_lat, 
                    self.max_lon, self.max_lat
                )
        except Exception as e:
            print(f"⚠ Could not load boundary: {e}")
            print("  Using bounding box instead")
            self.sri_lanka_boundary = box(
                self.min_lon, self.min_lat, 
                self.max_lon, self.max_lat
            )
    
    def classify_cell_type(self, cell_geometry):
        """
        Classify if cell is over land, ocean, or coastal
        
        Returns:
            'land': Centroid is over land
            'ocean': Centroid is over ocean
            'coastal': Cell intersects both land and ocean
        """
        if self.sri_lanka_boundary is None:
            return 'unknown'
        
        centroid = cell_geometry.centroid
        
        # Check if centroid is within Sri Lanka
        if self.sri_lanka_boundary.contains(centroid):
            return 'land'
        
        # Check if cell intersects with Sri Lanka (coastal)
        elif self.sri_lanka_boundary.intersects(cell_geometry):
            return 'coastal'
        
        # Otherwise it's ocean
        else:
            return 'ocean'
    
    def create_grid(self, classify_cells=True):
        """Create 10km x 10km grid cells"""
        
        print("="*70)
        print("Creating 10km × 10km grid cells...")
        print("="*70)
        print(f"Buffered bounds: {self.min_lat_buffered:.4f}°N to {self.max_lat_buffered:.4f}°N")
        print(f"                 {self.min_lon_buffered:.4f}°E to {self.max_lon_buffered:.4f}°E")
        
        # Load boundary if classification is needed
        if classify_cells:
            self.load_sri_lanka_boundary()
        
        # Calculate degree increments for 10km
        lat_step = self.km_to_degrees_lat(self.cell_size_km)
        
        # Use center latitude for longitude calculation
        center_lat = (self.min_lat_buffered + self.max_lat_buffered) / 2
        lon_step = self.km_to_degrees_lon(self.cell_size_km, center_lat)
        
        print(f"\nGrid cell size in degrees:")
        print(f"  Latitude step:  {lat_step:.6f}° (~10 km)")
        print(f"  Longitude step: {lon_step:.6f}° (~10 km at {center_lat:.2f}°N)")
        
        # Calculate number of cells needed
        n_rows = int(np.ceil((self.max_lat_buffered - self.min_lat_buffered) / lat_step))
        n_cols = int(np.ceil((self.max_lon_buffered - self.min_lon_buffered) / lon_step))
        
        print(f"\nGrid dimensions: {n_rows} rows × {n_cols} columns")
        print(f"Expected total cells: {n_rows * n_cols}")
        
        grid_data = []
        cell_count = 0
        
        print("\nGenerating grid cells...")
        for i in range(n_rows):
            for j in range(n_cols):
                # Cell boundaries
                min_lat_cell = self.min_lat_buffered + i * lat_step
                max_lat_cell = min_lat_cell + lat_step
                min_lon_cell = self.min_lon_buffered + j * lon_step
                max_lon_cell = min_lon_cell + lon_step
                
                # Create cell polygon
                cell = box(min_lon_cell, min_lat_cell, max_lon_cell, max_lat_cell)
                
                # Calculate centroid
                centroid = cell.centroid
                
                # Classify cell type
                cell_type = self.classify_cell_type(cell) if classify_cells else 'unknown'
                
                grid_data.append({
                    'grid_id': f'grid_{i}_{j}',
                    'cell_number': cell_count,
                    'row': i,
                    'col': j,
                    'centroid_lat': centroid.y,
                    'centroid_lon': centroid.x,
                    'min_lat': min_lat_cell,
                    'max_lat': max_lat_cell,
                    'min_lon': min_lon_cell,
                    'max_lon': max_lon_cell,
                    'cell_type': cell_type,
                    'geometry': cell
                })
                
                cell_count += 1
        
        # Create GeoDataFrame
        grid_gdf = gpd.GeoDataFrame(grid_data, crs="EPSG:4326")
        
        # Calculate actual area in km² for verification
        grid_gdf_metric = grid_gdf.to_crs("EPSG:32644")  # UTM Zone 44N
        grid_gdf['area_km2'] = grid_gdf_metric.geometry.area / 1_000_000
        
        # Print statistics
        print("\n" + "="*70)
        print("GRID STATISTICS")
        print("="*70)
        print(f"✓ Total cells created: {len(grid_gdf)}")
        print(f"  Average cell area: {grid_gdf['area_km2'].mean():.2f} km²")
        print(f"  Area range: {grid_gdf['area_km2'].min():.2f} - {grid_gdf['area_km2'].max():.2f} km²")
        
        if classify_cells:
            print(f"\nCell Type Distribution:")
            type_counts = grid_gdf['cell_type'].value_counts()
            for cell_type, count in type_counts.items():
                percentage = (count / len(grid_gdf)) * 100
                print(f"  {cell_type.capitalize()}: {count} cells ({percentage:.1f}%)")
        
        return grid_gdf
    
    def filter_by_type(self, grid_gdf, cell_types=['land']):
        """
        Filter grid to specific cell types
        
        Args:
            grid_gdf: GeoDataFrame with all cells
            cell_types: List of types to keep ['land', 'ocean', 'coastal']
        
        Returns:
            Filtered GeoDataFrame
        """
        filtered = grid_gdf[grid_gdf['cell_type'].isin(cell_types)].copy()
        
        print(f"\n✓ Filtered to {cell_types}: {len(filtered)} cells")
        return filtered
    
    def save_grid(self, grid_gdf, output_dir='data/bronze/metadata', save_filtered=True):
        """Save grid to files"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save complete grid
        print(f"\nSaving grid files to {output_dir}...")
        
        grid_gdf.to_file(f'{output_dir}/grid_cells_all.geojson', driver='GeoJSON')
        
        coords_df = grid_gdf[[
            'grid_id', 'cell_number', 'row', 'col', 
            'centroid_lat', 'centroid_lon', 
            'min_lat', 'max_lat', 'min_lon', 'max_lon',
            'area_km2', 'cell_type'
        ]].copy()
        coords_df.to_csv(f'{output_dir}/grid_coordinates_all.csv', index=False)
        
        print(f"  ✓ grid_cells_all.geojson")
        print(f"  ✓ grid_coordinates_all.csv")
        
        # Save filtered versions
        if save_filtered and 'cell_type' in grid_gdf.columns:
            # Land cells only
            land_cells = self.filter_by_type(grid_gdf, ['land'])
            if len(land_cells) > 0:
                land_cells.to_file(f'{output_dir}/grid_cells_land.geojson', driver='GeoJSON')
                land_cells[[
                    'grid_id', 'cell_number', 'centroid_lat', 'centroid_lon', 'area_km2'
                ]].to_csv(f'{output_dir}/grid_coordinates_land.csv', index=False)
                print(f"  ✓ grid_cells_land.geojson ({len(land_cells)} cells)")
                print(f"  ✓ grid_coordinates_land.csv")
            
            # Ocean cells only
            ocean_cells = self.filter_by_type(grid_gdf, ['ocean'])
            if len(ocean_cells) > 0:
                ocean_cells.to_file(f'{output_dir}/grid_cells_ocean.geojson', driver='GeoJSON')
                ocean_cells[[
                    'grid_id', 'cell_number', 'centroid_lat', 'centroid_lon', 'area_km2'
                ]].to_csv(f'{output_dir}/grid_coordinates_ocean.csv', index=False)
                print(f"  ✓ grid_cells_ocean.geojson ({len(ocean_cells)} cells)")
                print(f"  ✓ grid_coordinates_ocean.csv")
            
            # Land + Coastal (useful for solar/wind analysis)
            land_coastal = self.filter_by_type(grid_gdf, ['land', 'coastal'])
            if len(land_coastal) > 0:
                land_coastal.to_file(f'{output_dir}/grid_cells_land_coastal.geojson', driver='GeoJSON')
                land_coastal[[
                    'grid_id', 'cell_number', 'centroid_lat', 'centroid_lon', 'area_km2'
                ]].to_csv(f'{output_dir}/grid_coordinates_land_coastal.csv', index=False)
                print(f"  ✓ grid_cells_land_coastal.geojson ({len(land_coastal)} cells)")
                print(f"  ✓ grid_coordinates_land_coastal.csv")
        
        return coords_df
    
    def visualize_grid(self, grid_gdf, save_path='outputs/figures/grids/sri_lanka_grid_10km.html'):
        """Create interactive map with color-coded cell types"""
        
        center_lat = (self.min_lat_buffered + self.max_lat_buffered) / 2
        center_lon = (self.min_lon_buffered + self.max_lon_buffered) / 2
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=8)
        
        # Color scheme
        color_map = {
            'land': 'green',
            'ocean': 'blue',
            'coastal': 'orange',
            'unknown': 'gray'
        }
        
        # Add grid cells with color coding
        for idx, row in grid_gdf.iterrows():
            cell_color = color_map.get(row['cell_type'], 'gray')
            
            folium.GeoJson(
                row['geometry'],
                style_function=lambda x, color=cell_color: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 0.5,
                    'fillOpacity': 0.3
                },
                tooltip=f"{row['grid_id']} | {row['cell_type'].upper()} | {row['area_km2']:.1f} km²"
            ).add_to(m)
            
            # Add centroid marker (smaller for many cells)
            folium.CircleMarker(
                location=[row['centroid_lat'], row['centroid_lon']],
                radius=1.5,
                color='red',
                fill=True,
                fillOpacity=0.6,
                popup=f"<b>{row['grid_id']}</b><br>"
                      f"Type: {row['cell_type'].upper()}<br>"
                      f"Cell #{row['cell_number']}<br>"
                      f"Lat: {row['centroid_lat']:.4f}°N<br>"
                      f"Lon: {row['centroid_lon']:.4f}°E<br>"
                      f"Area: {row['area_km2']:.2f} km²"
            ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 150px; height: 120px; 
                    background-color: white; z-index:9999; font-size:14px;
                    border:2px solid grey; border-radius:5px; padding: 10px">
        <p style="margin:0"><b>Cell Types</b></p>
        <p style="margin:5px 0"><span style="color:green">●</span> Land</p>
        <p style="margin:5px 0"><span style="color:orange">●</span> Coastal</p>
        <p style="margin:5px 0"><span style="color:blue">●</span> Ocean</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        m.save(save_path)
        print(f"\n✓ Map saved to {save_path}")
        
        return m

# Main execution
if __name__ == "__main__":
    print("="*70)
    print("SRI LANKA 10km × 10km GRID GENERATION WITH LAND/OCEAN FILTERING")
    print("="*70)
    
    grid_gen = SriLankaGrid()
    
    # Create grid with classification
    grid_gdf = grid_gen.create_grid(classify_cells=True)
    
    print("\n" + "="*70)
    print("SAMPLE CELLS (First 10)")
    print("="*70)
    print(grid_gdf[['grid_id', 'centroid_lat', 'centroid_lon', 'area_km2', 'cell_type']].head(10))
    
    # Save all versions (all, land, ocean, land+coastal)
    coords_df = grid_gen.save_grid(grid_gdf, save_filtered=True)
    
    # Visualize with color coding
    grid_gen.visualize_grid(grid_gdf)
    
    print("\n" + "="*70)
    print("✓ GRID GENERATION COMPLETE!")
    print("="*70)
