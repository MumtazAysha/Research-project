# merge_station_data.py — FINAL VERSION
import os
import pandas as pd
import numpy as np

BASE     = os.path.join(r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project',
                        'data', 'bronze', 'weather_data')
TEM_FILE = os.path.join(BASE, 'tem .xlsx')
RF_FILE  = os.path.join(BASE, 'Rf .xlsx')
EXISTING = os.path.join(BASE, 'corrected_historical_2010_2025.csv')
OUTPUT   = os.path.join(BASE, 'corrected_historical_2010_2025.csv')  # overwrite same file

MONTHS   = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']

# ── 1. Load tem .xlsx (header is row 1, skip row 0) ──────────────────────────
temp_raw = pd.read_excel(TEM_FILE, header=1)   # row 1 = real header
temp_raw.columns = temp_raw.columns.str.strip()
temp_raw[MONTHS]       = temp_raw[MONTHS].apply(pd.to_numeric, errors='coerce')
temp_raw['yyyy']       = pd.to_numeric(temp_raw['yyyy'],      errors='coerce')
temp_raw['latitude']   = pd.to_numeric(temp_raw['latitude'],  errors='coerce')
temp_raw['longitude']  = pd.to_numeric(temp_raw['longitude'], errors='coerce')
temp_raw['elevation']  = pd.to_numeric(temp_raw['elevation'], errors='coerce')

print("Abbreviations in tem:", temp_raw['abbreviation'].unique())
print("Stations in tem:", sorted(temp_raw['station_name'].dropna().unique()))

# ── 2. Load Rf .xlsx ──────────────────────────────────────────────────────────
rain_raw = pd.read_excel(RF_FILE, header=1)
rain_raw.columns = rain_raw.columns.str.strip()
rain_raw[MONTHS]       = rain_raw[MONTHS].apply(pd.to_numeric, errors='coerce')
rain_raw['yyyy']       = pd.to_numeric(rain_raw['yyyy'],      errors='coerce')
rain_raw['latitude']   = pd.to_numeric(rain_raw['latitude'],  errors='coerce')
rain_raw['longitude']  = pd.to_numeric(rain_raw['longitude'], errors='coerce')
rain_raw['elevation']  = pd.to_numeric(rain_raw['elevation'], errors='coerce')

print("\nAbbreviations in Rf:", rain_raw['abbreviation'].unique())
print("Stations in Rf:", sorted(rain_raw['station_name'].dropna().unique()))

# ── 3. Average TMPMAX + TMPMIN → T_corrected ─────────────────────────────────
tmax = temp_raw[temp_raw['abbreviation'] == 'TMPMAX'].copy()
tmin = temp_raw[temp_raw['abbreviation'] == 'TMPMIN'].copy()

# merge on station + year
tmax_long = tmax.melt(id_vars=['station_name','latitude','longitude','elevation','yyyy'],
                      value_vars=MONTHS, var_name='month_name', value_name='TMAX')
tmin_long = tmin.melt(id_vars=['station_name','latitude','longitude','elevation','yyyy'],
                      value_vars=MONTHS, var_name='month_name', value_name='TMIN')

t_merged = tmax_long.merge(tmin_long,
                            on=['station_name','latitude','longitude','elevation','yyyy','month_name'],
                            how='inner')
t_merged['T_corrected'] = (t_merged['TMAX'] + t_merged['TMIN']) / 2

# ── 4. Melt rainfall → RF_corrected ──────────────────────────────────────────
rain_long = rain_raw.melt(id_vars=['station_name','latitude','longitude','elevation','yyyy'],
                          value_vars=MONTHS, var_name='month_name', value_name='RF_corrected')

# ── 5. Merge temp + rain ──────────────────────────────────────────────────────
station_df = t_merged.merge(rain_long,
                             on=['station_name','latitude','longitude','elevation','yyyy','month_name'],
                             how='inner')

# ── 6. Convert month_name → month number ─────────────────────────────────────
month_map = {m: i+1 for i, m in enumerate(MONTHS)}
station_df['month'] = station_df['month_name'].map(month_map)
station_df['year']  = station_df['yyyy'].astype(int)

# ── 7. Build final columns to match training CSV ──────────────────────────────
station_df = station_df.rename(columns={
    'latitude' : 'lat',
    'longitude': 'lon',
})
station_df['grid_id']  = 'station_' + station_df['station_name'].str.lower().str.replace(' ', '_')
station_df['T_om']     = station_df['T_corrected']   # no separate raw value
station_df['RF_om']    = station_df['RF_corrected']

final_cols = ['grid_id','lat','lon','elevation','year','month','T_om','RF_om','T_corrected','RF_corrected']
station_df = station_df[final_cols].dropna()

print(f"\n✅ Station rows prepared : {len(station_df)}")
print(f"   Lat range: {station_df['lat'].min():.2f} – {station_df['lat'].max():.2f}")
print(f"   Stations  : {station_df['grid_id'].nunique()}")

# ── 8. Load existing training CSV and merge ───────────────────────────────────
existing_df = pd.read_csv(EXISTING)
print(f"\nExisting training rows  : {len(existing_df)}")
print(f"Existing lat range      : {existing_df['lat'].min():.2f} – {existing_df['lat'].max():.2f}")

combined = pd.concat([existing_df, station_df], ignore_index=True)
combined = combined.drop_duplicates(subset=['grid_id','year','month'])
combined = combined.sort_values(['lat','lon','year','month']).reset_index(drop=True)

print(f"\nCombined rows           : {len(combined)}")
print(f"Combined lat range      : {combined['lat'].min():.2f} – {combined['lat'].max():.2f}")
print(f"Any points above lat 8.5? {(combined['lat'] > 8.5).sum()}")

# ── 9. Save ───────────────────────────────────────────────────────────────────
combined.to_csv(OUTPUT, index=False)
print(f"\n✅ Saved to: {OUTPUT}")
print("Now retrain: python scripts/phase1/temp_model.py")
print("         and: python scripts/phase1/rain_model.py")
