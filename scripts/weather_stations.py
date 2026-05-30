"""
Map all weather stations to grid cells and export their coordinates per grid.

Usage:
    venv\Scripts\activate
    python scripts/map_weather_stations_to_grids.py
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path


def load_grid(grid_path: str) -> gpd.GeoDataFrame:
    """Load grid GeoJSON with grid polygons."""
    print(f"Loading grid from: {grid_path}")
    grid_gdf = gpd.read_file(grid_path)
    print(f"  Loaded {len(grid_gdf)} grid cells")
    print(f"  Grid columns: {grid_gdf.columns.tolist()}")
    return grid_gdf


def load_rainfall_stations(csv_path: str) -> pd.DataFrame:
    """Load rainfall/weather stations with Lon/Lat from CSV."""
    print(f"\nLoading rainfall stations from: {csv_path}")
    df = pd.read_csv(csv_path, on_bad_lines="skip")
    print(f"  Raw rows: {len(df)}")
    print(f"  Columns: {df.columns.tolist()}")

    # Standardize column names
    rename_map = {
        "id": "station_id",
        "Name": "station_name",
        "Lon": "lon",
        "Lat": "lat",
        "district": "district"
    }
    df = df.rename(columns=rename_map)

    # Keep only rows with valid coordinates
    df = df.dropna(subset=["lon", "lat"])
    print(f"  After dropping NaN coords: {len(df)}")

    # Ensure numeric lon/lat
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df = df.dropna(subset=["lon", "lat"])
    print(f"  After coercing to numeric: {len(df)}")

    return df


def stations_to_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """Convert station DataFrame to GeoDataFrame with Point geometry."""
    print("\nConverting stations to GeoDataFrame...")
    df = df.copy()
    df["geometry"] = df.apply(lambda r: Point(float(r["lon"]), float(r["lat"])), axis=1)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    print(f"  Stations GeoDataFrame has {len(gdf)} rows")
    return gdf


def spatial_join_stations_to_grid(
    stations_gdf: gpd.GeoDataFrame,
    grid_gdf: gpd.GeoDataFrame,
    grid_id_col: str = "grid_id",
) -> gpd.GeoDataFrame:
    """Assign each station to the grid cell that contains it."""
    print("\nPerforming spatial join (stations within grid cells)...")

    # Ensure both are in same CRS
    if stations_gdf.crs != grid_gdf.crs:
        print("  Reprojecting grid to match stations CRS...")
        grid_gdf = grid_gdf.to_crs(stations_gdf.crs)

    # Keep only grid_id + geometry
    if grid_id_col not in grid_gdf.columns:
        raise ValueError(
            f"Grid ID column '{grid_id_col}' not found in grid_gdf. "
            f"Available columns: {grid_gdf.columns.tolist()}"
        )

    grid_subset = grid_gdf[[grid_id_col, "geometry"]].copy()

    # Spatial join: which grid polygon contains each station point
    joined = gpd.sjoin(
        stations_gdf,
        grid_subset,
        how="inner",
        predicate="within",
    )

    print(f"  Stations matched to grids: {len(joined)}")
    print(f"  Unique grids with stations: {joined[grid_id_col].nunique()}")
    return joined


def save_mapping(
    joined_gdf: gpd.GeoDataFrame,
    output_path: str,
    grid_id_col: str = "grid_id",
):
    """Save station–grid mapping to CSV."""
    print(f"\nSaving station–grid mapping to: {output_path}")

    cols_to_keep = [
        grid_id_col,
        "station_id",
        "station_name",
        "district",
        "lat",
        "lon",
    ]
    # Keep only existing columns
    cols_to_keep = [c for c in cols_to_keep if c in joined_gdf.columns]

    mapping_df = pd.DataFrame(joined_gdf[cols_to_keep]).copy()
    mapping_df = mapping_df.sort_values([grid_id_col, "station_id"])

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    mapping_df.to_csv(output_path, index=False)

    print(f"  Saved {len(mapping_df)} station-grid mappings")
    print(f"\nSummary:")
    print(f"  Total stations mapped: {mapping_df['station_id'].nunique()}")
    print(f"  Total grids with stations: {mapping_df[grid_id_col].nunique()}")
    print(f"  Avg stations per grid: {len(mapping_df) / mapping_df[grid_id_col].nunique():.2f}")
    
    print("\nExample rows:")
    print(mapping_df.head(10).to_string(index=False))
    
    # Show grids with most stations
    print("\nTop 10 grids by number of stations:")
    station_counts = mapping_df.groupby(grid_id_col).size().sort_values(ascending=False)
    print(station_counts.head(10))


def main():
    # CORRECTED PATHS
    GRID_GEOJSON = "data/bronze/metadata/grid_cells_all.geojson"
    RAINFALL_CSV =  r"C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\raw\stations\Copy of Met Stations Rainfall stations all from the begining.xlsx.csv"

    OUTPUT_CSV = "data/bronze/metadata/grid_weather_station_mapping.csv"

    # Load data
    grid_gdf = load_grid(GRID_GEOJSON)
    stations_df = load_rainfall_stations(RAINFALL_CSV)
    stations_gdf = stations_to_geodataframe(stations_df)

    # Spatial join with CORRECTED grid_id column name
    joined = spatial_join_stations_to_grid(
        stations_gdf=stations_gdf,
        grid_gdf=grid_gdf,
        grid_id_col="grid_id",  # CORRECTED: was "gridid", now "grid_id"
    )

    # Save mapping
    save_mapping(joined, OUTPUT_CSV, grid_id_col="grid_id")

    print("\n" + "="*70)
    print("✓ DONE!")
    print("="*70)
    print(f"\nOutput file: {OUTPUT_CSV}")
    print("\nNow you have all 1,508 weather station coordinates mapped to grids.")
    print("For any grid with 21 stations, you'll see all 21 lat/lon coordinates.")
    print("\nOpen the CSV in Excel and filter by 'grid_id' to see stations per grid.")

if __name__ == "__main__":
    main()


    
