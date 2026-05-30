"""
Generate 10km x 10km grid cells for Sri Lanka (produces ~1,242 cells)
"""
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import box
import folium
from pathlib import Path
import math


class SriLankaGrid:
    """Creates 10km x 10km grid cells for Sri Lanka."""

    def __init__(self):
        # Sri Lanka bounds: 5°55′–9°51′N, 79°41′–81°53′E
        self.minlat = 5.917  # 5°55'N
        self.maxlat = 9.850  # 9°51'N
        self.minlon = 79.683  # 79°41'E
        self.maxlon = 81.883  # 81°53'E

        # Add 10km buffer on all sides
        buffer_lat = self.km_to_degrees_lat(10)
        buffer_lon_min = self.km_to_degrees_lon(10, self.minlat)
        buffer_lon_max = self.km_to_degrees_lon(10, self.maxlat)
        buffer_lon = max(buffer_lon_min, buffer_lon_max)

        self.minlat_buffered = self.minlat - buffer_lat
        self.maxlat_buffered = self.maxlat + buffer_lat
        self.minlon_buffered = self.minlon - buffer_lon
        self.maxlon_buffered = self.maxlon + buffer_lon

        self.cell_size_km = 10

        # Load Sri Lanka boundary
        self.srilanka_boundary = None
        self._load_boundary()

    def _load_boundary(self):
        """Load Sri Lanka boundary."""
        try:
            url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
            world = gpd.read_file(url)
            srilanka = world[world['NAME'] == 'Sri Lanka']
            if len(srilanka) > 0:
                self.srilanka_boundary = srilanka.geometry.iloc[0]
                print("✓ Boundary loaded")
        except:
            print("⚠ Boundary load failed")

    def km_to_degrees_lat(self, km: float) -> float:
        return km / 111.0

    def km_to_degrees_lon(self, km: float, latitude: float) -> float:
        return km / (111.0 * math.cos(math.radians(latitude)))

    def create_grid(self, classify_cells: bool = True) -> gpd.GeoDataFrame:
        """Create 10km x 10km grid."""
        print("Creating 10km x 10km grid cells...")

        lat_step = self.km_to_degrees_lat(self.cell_size_km)
        center_lat = (self.minlat_buffered + self.maxlat_buffered) / 2
        lon_step = self.km_to_degrees_lon(self.cell_size_km, center_lat)

        nrows = int(np.ceil((self.maxlat_buffered - self.minlat_buffered) / lat_step))
        ncols = int(np.ceil((self.maxlon_buffered - self.minlon_buffered) / lon_step))

        print(f"Grid: {nrows} rows x {ncols} columns = {nrows * ncols} cells")

        grid_data = []
        cell_count = 0

        for i in range(nrows):
            for j in range(ncols):
                minlat = self.minlat_buffered + i * lat_step
                maxlat = minlat + lat_step
                minlon = self.minlon_buffered + j * lon_step
                maxlon = minlon + lon_step

                cell_geom = box(minlon, minlat, maxlon, maxlat)
                centroid = cell_geom.centroid

                grid_data.append({
                    "grid_id": f"grid_{i}_{j}",
                    "cell_number": cell_count,
                    "row": i,
                    "col": j,
                    "centroid_lat": centroid.y,
                    "centroid_lon": centroid.x,
                    "minlat": minlat,
                    "maxlat": maxlat,
                    "minlon": minlon,
                    "maxlon": maxlon,
                    "geometry": cell_geom,
                })
                cell_count += 1

        grid_gdf = gpd.GeoDataFrame(grid_data, crs="EPSG:4326")

        # Calculate area
        grid_metric = grid_gdf.to_crs("EPSG:32644")
        grid_gdf["area_km2"] = grid_metric.geometry.area / 1_000_000.0

        print(f"Created {len(grid_gdf)} cells | Avg area: {grid_gdf['area_km2'].mean():.2f} km²")

        if classify_cells and self.srilanka_boundary:
            grid_gdf = self.classify_cells(grid_gdf)

        return grid_gdf

    def classify_cells(self, grid_gdf):
        """Classify as land/ocean/coastal."""
        print("Classifying cells...")
        cell_types = []
        for geom in grid_gdf.geometry:
            if self.srilanka_boundary.contains(geom):
                cell_types.append("land")
            elif self.srilanka_boundary.intersects(geom):
                cell_types.append("coastal")
            else:
                cell_types.append("ocean")
        grid_gdf["cell_type"] = cell_types
        print(grid_gdf["cell_type"].value_counts())
        return grid_gdf

    def save_grid(self, grid_gdf, output_dir="data/bronze/metadata"):
        """Save grid files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        grid_gdf.to_file(output_dir / "grid_cells_all.geojson", driver="GeoJSON")
        
        coords_cols = ["grid_id", "cell_number", "row", "col", "centroid_lat", 
                      "centroid_lon", "minlat", "maxlat", "minlon", "maxlon", "area_km2"]
        if "cell_type" in grid_gdf.columns:
            coords_cols.append("cell_type")
        
        grid_gdf[coords_cols].to_csv(output_dir / "grid_coordinates_all.csv", index=False)
        print(f"✓ Saved to {output_dir}")


if __name__ == "__main__":
    print("=" * 70)
    print("SRI LANKA 10km x 10km GRID GENERATION")
    print("=" * 70)

    gridgen = SriLankaGrid()
    grid_gdf = gridgen.create_grid(classify_cells=True)
    gridgen.save_grid(grid_gdf)

    print("=" * 70)
    print(f"✓ COMPLETE! Total cells: {len(grid_gdf)}")
    print("=" * 70)

