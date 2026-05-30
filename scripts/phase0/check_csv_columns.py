import pandas as pd

# Check daily file
daily = pd.read_csv('data/silver/openmeteo_backup_no_solar/year_2019/daily/station_43415_2019.csv')
print("DAILY FILE COLUMNS:")
print(daily.columns.tolist())
print("\nFirst row:")
print(daily.head(1))

print("\n" + "="*70 + "\n")

# Check 3-hourly file
hourly = pd.read_csv('data/silver/openmeteo_backup_no_solar/year_2019/3hourly/station_43415_2019_3hourly.csv')
print("3-HOURLY FILE COLUMNS:")
print(hourly.columns.tolist())
print("\nFirst row:")
print(hourly.head(1))