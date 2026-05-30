"""
Main configuration file
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Create directories
for dir_path in [BRONZE_DIR, SILVER_DIR, GOLD_DIR, OUTPUTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Sri Lanka bounding box
SRI_LANKA_BOUNDS = {
    'min_lat': 5.9,
    'max_lat': 9.9,
    'min_lon': 79.5,
    'max_lon': 81.9
}

# Grid configuration
GRID_SIZE = (5, 5)  # 5x5 grid

# Date ranges
HISTORICAL_START = "1999-01-01"
HISTORICAL_END = "2024-12-31"
TRAIN_END = "2022-12-31"
VAL_END = "2023-12-31"
TEST_END = "2024-12-31"

# API Configuration
OPENMETEO_API = "https://api.open-meteo.com/v1/"

# Model configuration
RANDOM_SEED = 42
BATCH_SIZE = 32
LEARNING_RATE = 0.001
NUM_EPOCHS = 100
