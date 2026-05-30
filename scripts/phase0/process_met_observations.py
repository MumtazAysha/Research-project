"""
Phase 0 — Step 3: Process All Met Observation Files
Outputs: met_observations_monthly.csv
"""

import pandas as pd
import numpy as np
import os
import glob
import re
from calendar import monthrange

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ─── FILE PATHS — Edit these ──────────────────────────────────────
RF_FILE       = "../../data/bronze/weather_data/Rf .xlsx"
TEM_FILE      = "../../data/bronze/weather_data/tem .xlsx"
SUNSHINE_FILE = "../../data/bronze/weather_data/PUCSLdata2010-2024.xlsx"
WIND_FOLDER   = "../../data/bronze/weather_data/Wind"
OUTPUT_FILE   = "../../data/silver/met_observations_monthly.csv"


MONTHS = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]

MET_STATIONS = {
    "ANURADHAPURA":(8.35,80.38), "BADULLA":(6.98,81.05),
    "BANDARAWELA":(6.84,80.98),  "BATTICALOA":(7.72,81.70),
    "COLOMBO":(6.90,79.87),      "GALLE":(6.03,80.22),
    "HAMBANTOTA":(6.12,81.13),   "JAFFNA":(9.68,80.03),
    "KATUGASTOTA":(7.33,80.63),  "KATUNAYAKA":(7.17,79.88),
    "KURUNEGALA":(7.47,80.37),   "MAHA_ILLUPPALLAMA":(8.12,80.47),
    "MANNAR":(8.98,79.92),       "MATTALA":(6.30,81.13),
    "MONARAGALA":(6.50,81.30),   "MULLAITIVU":(9.25,80.82),
    "NUWARA_ELIYA":(6.97,80.77), "POLONNARUWA":(7.87,81.05),
    "POTTUVIL":(6.88,81.83),     "PUTTALAM":(8.03,79.83),
    "RATMALANA":(6.82,79.88),    "RATNAPURA":(6.68,80.40),
    "TRINCOMALEE":(8.58,81.25),  "VAVUNIYA":(8.75,80.50),
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlam/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

print("=" * 65)
print("PHASE 0 — STEP 3: Processing Met Observation Files")
print("=" * 65)

# ── 1. RAINFALL ───────────────────────────────────────────────────
print("\n[1/4] Processing Rainfall...")
rf_raw = pd.read_excel(RF_FILE, header=1)
rf_raw.columns = ["id","station_name","longitude","latitude","elevation","code","abbreviation","year"] + MONTHS
rf_raw = rf_raw[rf_raw["abbreviation"] == "PRECIP"].copy()
rf_raw["station_name"] = rf_raw["station_name"].str.strip().str.upper().str.replace(" ","_")
rf_long = rf_raw.melt(id_vars=["station_name","latitude","longitude","elevation","year"],
                      value_vars=MONTHS, var_name="month_str", value_name="precip_obs_mm")
rf_long["month"] = rf_long["month_str"].apply(lambda x: MONTHS.index(x) + 1)
rf_long["precip_obs_mm"] = pd.to_numeric(rf_long["precip_obs_mm"], errors="coerce")
rf_long = rf_long.drop(columns="month_str")
print(f"   ✅ {len(rf_long)} rows | Stations: {rf_long['station_name'].nunique()}")

# ── 2. TEMPERATURE ────────────────────────────────────────────────
print("\n[2/4] Processing Temperature...")
tem_raw = pd.read_excel(TEM_FILE, header=1)
tem_raw.columns = ["id","station_name","longitude","latitude","elevation","code","abbreviation","year"] + MONTHS
tem_raw["station_name"] = tem_raw["station_name"].str.strip().str.upper().str.replace(" ","_")

def melt_temp(df, val_name):
    melted = df.melt(id_vars=["station_name","latitude","longitude","elevation","year"],
                     value_vars=MONTHS, var_name="month_str", value_name=val_name)
    melted["month"] = melted["month_str"].apply(lambda x: MONTHS.index(x) + 1)
    melted[val_name] = pd.to_numeric(melted[val_name], errors="coerce")
    return melted.drop(columns="month_str")

tem_max_long = melt_temp(tem_raw[tem_raw["abbreviation"]=="TMPMAX"].copy(), "temp_max_C")
tem_min_long = melt_temp(tem_raw[tem_raw["abbreviation"]=="TMPMIN"].copy(), "temp_min_C")
tem_long = tem_max_long.merge(tem_min_long[["station_name","year","month","temp_min_C"]],
                               on=["station_name","year","month"], how="outer")
tem_long["temp_mean_obs_C"] = (tem_long["temp_max_C"] + tem_long["temp_min_C"]) / 2
print(f"   ✅ {len(tem_long)} rows | Stations: {tem_long['station_name'].nunique()}")

# ── 3. SUNSHINE ───────────────────────────────────────────────────
print("\n[3/4] Processing Sunshine Hours...")
sun_raw = pd.read_excel(SUNSHINE_FILE, header=None)
MONTH_ORDER = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]
SUNSHINE_COORDS = {
    "Agalawatta":(6.57,80.22),   "Giradurukotte":(7.70,80.98),
    "Kottawa":(6.08,80.37),      "Ratnapura":(6.68,80.40),
    "Hambantota":(6.12,81.13),   "Jaffna":(9.68,80.03),
    "Katunayake":(7.17,79.88),   "Mannar":(8.98,79.92),
    "Kurunegala":(7.47,80.37),   "Trincomalee":(8.58,81.25),
    "Anuradhapura":(8.35,80.38), "Nuwara Eliya":(6.97,80.77),
    "Colombo":(6.90,79.87),      "Puttalam":(8.03,79.83),
    "Batticaloa":(7.72,81.70),   "Badulla":(6.98,81.05),
    "Vavuniya":(8.75,80.50),     "Galle":(6.03,80.22),
    "Monaragala":(6.50,81.30),   "Polonnaruwa":(7.87,81.05),
}

sunshine_records = []
current_station = None
i = 0
rows = sun_raw.values
while i < len(rows):
    row = rows[i]
    if str(row[1]).strip() == "Month":
        years = [int(float(y)) for y in row[2:] if str(y).strip() not in ["","nan"]]
        # Station name is 2 rows above "Month"
        if i >= 3:
            for back in range(1, 4):
                candidate = str(rows[i-back][1]).strip()
                if candidate and candidate != "nan" and candidate != "Month":
                    current_station = candidate
                    break
        i += 1
        for m_idx, month_name in enumerate(MONTH_ORDER):
            if i >= len(rows): break
            data_row = rows[i]
            if str(data_row[1]).strip() == month_name:
                values = list(data_row[2:2+len(years)])
                for y_idx, yr in enumerate(years):
                    val = pd.to_numeric(values[y_idx] if y_idx < len(values) else np.nan, errors="coerce")
                    days = monthrange(yr, m_idx+1)[1]
                    sunshine_records.append({"sunshine_station": current_station,
                        "year": yr, "month": m_idx+1,
                        "sunshine_sum_obs_hrs": val*days if not pd.isna(val) else np.nan})
            i += 1
    else:
        i += 1

sun_df = pd.DataFrame(sunshine_records)

def nearest_met(sname):
    coords = SUNSHINE_COORDS.get(sname)
    if not coords: return None
    return min(MET_STATIONS, key=lambda m: haversine(coords[0],coords[1],MET_STATIONS[m][0],MET_STATIONS[m][1]))

sun_df["station_name"] = sun_df["sunshine_station"].apply(nearest_met)
sun_df = sun_df.dropna(subset=["station_name"])
sun_agg = sun_df.groupby(["station_name","year","month"])["sunshine_sum_obs_hrs"].mean().reset_index()
print(f"   ✅ {len(sun_agg)} rows | Mapped to nearest Met stations")

# ── 4. WIND SPEED ─────────────────────────────────────────────────
print("\n[4/4] Processing Wind Speed files...")
WIND_MAP = {
    "anuradhapura":"ANURADHAPURA", "badulla":"BADULLA",
    "bandarawela":"BANDARAWELA",   "batticaloa":"BATTICALOA",
    "colombo":"COLOMBO",           "galle":"GALLE",
    "hambantota":"HAMBANTOTA",     "jaffna":"JAFFNA",
    "katugastota":"KATUGASTOTA",   "katunayake":"KATUNAYAKA",
    "kurunegala":"KURUNEGALA",     "maha":"MAHA_ILLUPPALLAMA",
    "mannar":"MANNAR",             "mattala":"MATTALA",
    "monaragala":"MONARAGALA",     "mullaitivu":"MULLAITIVU", "mullathive":"MULLAITIVU",
    "nuwaraeliya":"NUWARA_ELIYA",  "nuwara":"NUWARA_ELIYA",
    "polonnaruwa":"POLONNARUWA",   "pottuvil":"POTTUVIL",
    "puttalam":"PUTTALAM",         "ratmalana":"RATMALANA",
    "ratnapura":"RATNAPURA",       "trincomalee":"TRINCOMALEE",
    "vavuniya":"VAVUNIYA",
}

wind_frames = []
for wf in sorted(glob.glob(os.path.join(WIND_FOLDER, "*.xlsx"))):
    fname = os.path.basename(wf)
    station = next((v for k,v in WIND_MAP.items() if k in fname.lower()), None)
    if not station:
        print(f"   ⚠️  Could not map: {fname}"); continue
    try:
        raw = pd.read_excel(wf, header=None)
        data_start = next((i for i,row in raw.iterrows()
                           if re.match(r"^20[0-9]{2}$", str(row.iloc[0]).strip())), None)
        if data_start is None:
            print(f"   ⚠️  No data rows in {fname}"); continue
        records = []
        for _, row in raw.iloc[data_start:].iterrows():
            yv = str(row.iloc[0]).strip()
            if not re.match(r"^20[0-9]{2}$", yv): continue
            vals = list(row.iloc[1:])
            for m in range(12):
                am = pd.to_numeric(vals[m*2]   if m*2   < len(vals) else np.nan, errors="coerce")
                pm = pd.to_numeric(vals[m*2+1] if m*2+1 < len(vals) else np.nan, errors="coerce")   
                valid = [v for v in [am,pm] if not np.isnan(v)]
                records.append({"station_name":station, "year":int(yv), "month":m+1,
                                 "wind_obs_ms": np.mean(valid)/3.6 if valid else np.nan})
        wind_frames.append(pd.DataFrame(records))
        print(f"   ✅ {station:25s} → {len(records)} records")
    except Exception as e:
        print(f"   ❌ {fname}: {e}")

wind_df = pd.concat(wind_frames, ignore_index=True) if wind_frames else pd.DataFrame()

# ── 5. MERGE ALL ──────────────────────────────────────────────────
print("\n[5/5] Merging all datasets...")
merged = rf_long[["station_name","latitude","longitude","elevation","year","month","precip_obs_mm"]].copy()
merged["year"] = merged["year"].astype(int)
merged = merged.merge(tem_long[["station_name","year","month","temp_mean_obs_C","temp_max_C","temp_min_C"]],
                      on=["station_name","year","month"], how="left")
merged = merged.merge(sun_agg[["station_name","year","month","sunshine_sum_obs_hrs"]],
                      on=["station_name","year","month"], how="left")
if not wind_df.empty:
    merged = merged.merge(wind_df[["station_name","year","month","wind_obs_ms"]],
                          on=["station_name","year","month"], how="left")

merged.sort_values(["station_name","year","month"], inplace=True)
merged.reset_index(drop=True, inplace=True)
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
merged.to_csv(OUTPUT_FILE, index=False)

print("\n" + "=" * 65)
print(f"✅ Total rows  : {len(merged):,}")
print(f"✅ Stations    : {merged['station_name'].nunique()}")
print(f"✅ Year range  : {merged['year'].min()} – {merged['year'].max()}")
print(f"📁 Saved to    : {OUTPUT_FILE}")
print("\n📋 Next step: merge with Open-Meteo data")
