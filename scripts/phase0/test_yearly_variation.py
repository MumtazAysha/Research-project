import pandas as pd

station = "43476"  # Change to your test station

for year in [2019, 2020, 2021, 2022, 2023, 2024]:
    file_path = f'data/silver/openmeteo/year_{year}/3hourly/station_{station}_{year}_3hourly.csv'
    
    try:
        df = pd.read_csv(file_path)
        
        # Check for solar radiation column
        solar_col = None
        for col in df.columns:
            if 'radiation' in col.lower():
                solar_col = col
                break
        
        if solar_col:
            avg_rad = df[solar_col].mean()
            print(f"{year}: {avg_rad:.2f} kWh/m²/day (from {solar_col})")
        else:
            print(f"{year}: No radiation column found")
            print(f"       Available columns: {list(df.columns)}")
            break
    except:
        print(f"{year}: File not found")
