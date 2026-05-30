
"""
Generate Detailed Station Coverage Reports
1. Stations grouped by grid location
2. Grids with no stations
3. Station type breakdown
"""
import pandas as pd
from pathlib import Path

print("="*70)
print("GENERATING DETAILED COVERAGE REPORTS")
print("="*70)

# Load the station-grid report
stations_report = pd.read_csv('outputs/reports/stations_grid_report.csv')
grid_summary = pd.read_csv('outputs/reports/grid_summary.csv')

print(f"\nLoaded {len(stations_report)} station records")
print(f"Loaded {len(grid_summary)} grid cells")

# ============================================================================
# REPORT 1: STATIONS BY GRID LOCATION
# ============================================================================
print("\n" + "="*70)
print("REPORT 1: STATIONS BY GRID LOCATION")
print("="*70)

# Group stations by grid
stations_by_grid = stations_report.groupby(['grid_id', 'location_name'])

report1_data = []

for (grid_id, location_name), group in stations_by_grid:
    # Count by type
    met_count = len(group[group['type'] == 'met'])
    old_count = len(group[group['type'] == 'rainfall_old'])
    new_count = len(group[group['type'] == 'rainfall_new'])

    # Get station names by type
    met_stations = group[group['type'] == 'met']['name'].tolist()
    old_stations = group[group['type'] == 'rainfall_old']['name'].tolist()
    new_stations = group[group['type'] == 'rainfall_new']['name'].tolist()

    report1_data.append({
        'Location': location_name,
        'Grid_ID': grid_id,
        'Total_Stations': len(group),
        'Met_Stations_Count': met_count,
        'Rainfall_Old_Count': old_count,
        'Rainfall_New_Count': new_count,
        'Met_Stations': ', '.join(met_stations) if met_stations else 'None',
        'Rainfall_Old_Stations': ', '.join(old_stations[:3]) + ('...' if len(old_stations) > 3 else '') if old_stations else 'None',
        'Rainfall_New_Stations': ', '.join(new_stations[:3]) + ('...' if len(new_stations) > 3 else '') if new_stations else 'None'
    })

report1_df = pd.DataFrame(report1_data)
report1_df = report1_df.sort_values('Total_Stations', ascending=False)

# Save Report 1
report1_path = Path('outputs/reports/stations_by_location.csv')
report1_df.to_csv(report1_path, index=False)
print(f"\n✓ Saved: {report1_path}")

# Print summary
print(f"\nGrids with stations: {len(report1_df)}")
print(f"\nTop 10 locations by station count:")
print(report1_df[['Location', 'Total_Stations', 'Met_Stations_Count', 'Rainfall_Old_Count', 'Rainfall_New_Count']].head(10).to_string(index=False))

# ============================================================================
# REPORT 2: GRIDS WITH NO STATIONS
# ============================================================================
print("\n\n" + "="*70)
print("REPORT 2: GRIDS WITH NO STATIONS")
print("="*70)

# Find grids with zero stations
no_stations = grid_summary[grid_summary['total_stations'] == 0].copy()

report2_data = []
for idx, row in no_stations.iterrows():
    report2_data.append({
        'Location': row['location_name'],
        'Grid_ID': row['grid_id'],
        'Latitude': row.get('centroid_lat', 'N/A'),
        'Longitude': row.get('centroid_lon', 'N/A')
    })

report2_df = pd.DataFrame(report2_data)
report2_df = report2_df.sort_values('Location')

# Save Report 2
report2_path = Path('outputs/reports/grids_without_stations.csv')
report2_df.to_csv(report2_path, index=False)
print(f"\n✓ Saved: {report2_path}")

print(f"\nTotal grids without ANY stations: {len(report2_df)}")
print(f"\nFirst 20 locations without stations:")
print(report2_df[['Location', 'Grid_ID']].head(20).to_string(index=False))

# ============================================================================
# REPORT 3: MET STATIONS ONLY (DETAILED)
# ============================================================================
print("\n\n" + "="*70)
print("REPORT 3: MET STATIONS DETAILED LIST")
print("="*70)

met_only = stations_report[stations_report['type'] == 'met'].copy()

report3_data = []
for idx, row in met_only.iterrows():
    report3_data.append({
        'Station_Name': row['name'],
        'Location': row.get('location_name', 'Unknown'),
        'Grid_ID': row['grid_id'] if pd.notna(row.get('grid_id')) else 'Outside Grid',
        'Latitude': row['latitude'],
        'Longitude': row['longitude'],
        'Elevation': row.get('elevation', 'N/A')
    })

report3_df = pd.DataFrame(report3_data)
report3_df = report3_df.sort_values('Station_Name')

# Save Report 3
report3_path = Path('outputs/reports/met_stations_detailed.csv')
report3_df.to_csv(report3_path, index=False)
print(f"\n✓ Saved: {report3_path}")

print(f"\nTotal Met Stations: {len(report3_df)}")
print(f"\nAll Met Stations with their locations:")
print(report3_df[['Station_Name', 'Location', 'Grid_ID']].to_string(index=False))

# ============================================================================
# REPORT 4: SUMMARY STATISTICS
# ============================================================================
print("\n\n" + "="*70)
print("REPORT 4: SUMMARY STATISTICS")
print("="*70)

summary_stats = {
    'Total_Grids': len(grid_summary),
    'Grids_With_Stations': len(report1_df),
    'Grids_Without_Stations': len(report2_df),
    'Total_Stations': len(stations_report),
    'Met_Stations': len(met_only),
    'Rainfall_Old_Stations': len(stations_report[stations_report['type'] == 'rainfall_old']),
    'Rainfall_New_Stations': len(stations_report[stations_report['type'] == 'rainfall_new']),
    'Grids_With_Met_Stations': (grid_summary['met'] > 0).sum(),
    'Grids_With_Rainfall_Old': (grid_summary['rainfall_old'] > 0).sum(),
    'Grids_With_Rainfall_New': (grid_summary['rainfall_new'] > 0).sum(),
}

summary_df = pd.DataFrame([summary_stats]).T
summary_df.columns = ['Count']

# Save summary
summary_path = Path('outputs/reports/coverage_summary.csv')
summary_df.to_csv(summary_path)
print(f"\n✓ Saved: {summary_path}")

print("\nCoverage Summary:")
print(summary_df.to_string())

print("\n" + "="*70)
print("✓ ALL REPORTS GENERATED SUCCESSFULLY!")
print("="*70)
print("\nGenerated Files:")
print(f"  1. {report1_path} - Stations grouped by location")
print(f"  2. {report2_path} - Locations with NO stations")
print(f"  3. {report3_path} - Met stations detailed list")
print(f"  4. {summary_path} - Overall coverage statistics")
print("="*70)