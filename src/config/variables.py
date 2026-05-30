"""
Tier 1 variable definitions
"""

# Continuous variables (single-stage prediction)
CONTINUOUS_VARIABLES = {
    'shortwave_radiation': 'GHI',
    'direct_radiation': 'DNI',
    'diffuse_radiation': 'DHI',
    'temperature_2m': 'Temperature',
    'relative_humidity_2m': 'Humidity',
    'surface_pressure': 'Pressure',
    'cloud_cover': 'CloudCover',
    'wind_speed_10m': 'WindSpeed',
}

# Rainfall (two-stage prediction)
RAINFALL_VARIABLE = 'precipitation'

# All variables combined
ALL_VARIABLES = {**CONTINUOUS_VARIABLES, RAINFALL_VARIABLE: 'Precipitation'}

# OpenMeteo API parameter names
OPENMETEO_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "surface_pressure",
    "cloud_cover",
    "precipitation",
    "shortwave_radiation",
    "direct_radiation",
    "diffuse_radiation",
    "wind_speed_10m",
]

# Temporal features to generate
TEMPORAL_FEATURES = [
    'hour_sin', 'hour_cos',      # Daily cycle
    'day_sin', 'day_cos',        # Annual cycle
    'year_normalized',           # Trend
]

# Rainfall classification threshold (mm/day)
RAIN_THRESHOLD = 0.1  # Days with < 0.1mm considered "No Rain"
