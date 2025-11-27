"""
Create project folder structure
"""
from pathlib import Path

# Define folder structure
folders = [
    # Bronze layer
    "data/bronze/era5_raw",
    "data/bronze/openmeteo_forecast",
    "data/bronze/metadata",
    
    # Silver layer
    "data/silver/weather_cleaned/continuous_variables",
    "data/silver/weather_cleaned/rainfall",
    "data/silver/weather_features/temporal_features",
    "data/silver/weather_features/lag_features",
    "data/silver/weather_features/spatial_features",
    "data/silver/train_test_split/train",
    "data/silver/train_test_split/validation",
    "data/silver/train_test_split/test",
    
    # Gold layer
    "data/gold/training_datasets",
    "data/gold/weather_forecasts/continuous_predictions",
    "data/gold/weather_forecasts/rainfall_predictions",
    "data/gold/validation_results/continuous_metrics",
    "data/gold/validation_results/rainfall_metrics",
    
    # Code structure
    "notebooks",
    "src/config",
    "src/data",
    "src/features",
    "src/models",
    "src/training",
    "src/prediction",
    "src/utils",
    "tests",
    
    # Outputs
    "outputs/figures/grids",
    "outputs/figures/predictions",
    "outputs/figures/performance",
    "outputs/models/checkpoints",
    "outputs/models/best_models",
    "outputs/reports/training_logs",
    "outputs/reports/evaluation_reports",
    
    # Scripts and docs
    "scripts",
    "docs"
]

# Create all folders
for folder in folders:
    Path(folder).mkdir(parents=True, exist_ok=True)
    print(f"✓ Created: {folder}")

print("\n✓ All folders created successfully!")
