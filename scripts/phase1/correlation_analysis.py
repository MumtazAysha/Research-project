# correlation_analysis.py
# Correlation analysis between solar potential, temperature, and rainfall
# Generates scatter plots, correlation matrix heatmap, and monthly trend charts

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE        = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\weather_data'
SOLAR_FILE  = BASE + r'\solar_grid_predictions_annual.csv'
TEMP_FILE   = BASE + r'\temp_grid_predictions.csv'
RAIN_FILE   = BASE + r'\rain_grid_predictions.csv'
OUT_DIR     = BASE + r'\correlation_plots'

import os
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load Data ─────────────────────────────────────────────────────────────────
solar = pd.read_csv(SOLAR_FILE)
temp  = pd.read_csv(TEMP_FILE)
rain  = pd.read_csv(RAIN_FILE)

print("Solar columns:", solar.columns.tolist())
print("Temp columns :", temp.columns.tolist())
print("Rain columns :", rain.columns.tolist())

# ── Merge on lat/lon ──────────────────────────────────────────────────────────
df = solar[['lat', 'lon', 'annual_yield_kWh_kWp', 'district', 'province']].copy()
df = df.merge(temp[['lat', 'lon', 'annual_avg_T']], on=['lat', 'lon'], how='inner')
df = df.merge(rain[['lat', 'lon', 'annual_total_RF']], on=['lat', 'lon'], how='inner')
df.rename(columns={
    'annual_yield_kWh_kWp' : 'Solar_Yield',
    'annual_avg_T'          : 'Temperature',
    'annual_total_RF'       : 'Rainfall'
}, inplace=True)

print(f"\nMerged dataset: {len(df)} grid cells")
print(df[['Solar_Yield', 'Temperature', 'Rainfall']].describe().round(2))

# ── Pearson Correlation ───────────────────────────────────────────────────────
r_temp, p_temp = stats.pearsonr(df['Solar_Yield'], df['Temperature'])
r_rain, p_rain = stats.pearsonr(df['Solar_Yield'], df['Rainfall'])
r_tr,   p_tr   = stats.pearsonr(df['Temperature'], df['Rainfall'])

print(f"\n── Pearson Correlation Coefficients ────────────────")
print(f"  Solar Yield  vs Temperature : r = {r_temp:.4f}  (p = {p_temp:.4f})")
print(f"  Solar Yield  vs Rainfall    : r = {r_rain:.4f}  (p = {p_rain:.4f})")
print(f"  Temperature  vs Rainfall    : r = {r_tr:.4f}  (p = {p_tr:.4f})")
print(f"────────────────────────────────────────────────────")

# ── Plot Style ────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family'  : 'DejaVu Sans',
    'font.size'    : 11,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'figure.facecolor': 'white',
})
COLORS = {'Uva Province': '#E07B39', 'Western Province': '#2E86AB'}

# ── Plot 1: Solar vs Temperature ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 6))
for prov, grp in df.groupby('province'):
    color = COLORS.get(prov, '#888888')
    ax.scatter(grp['Temperature'], grp['Solar_Yield'],
               c=color, label=prov, alpha=0.75, edgecolors='white', s=70)

# Regression line
m, b, *_ = stats.linregress(df['Temperature'], df['Solar_Yield'])
x_line = np.linspace(df['Temperature'].min(), df['Temperature'].max(), 100)
ax.plot(x_line, m * x_line + b, 'k--', linewidth=1.5, label='Trend line')

ax.set_xlabel('Annual Avg Temperature (°C)')
ax.set_ylabel('Solar Yield (kWh/kWp)')
ax.set_title(f'Solar Yield vs Temperature  |  r = {r_temp:.3f}')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUT_DIR + r'\scatter_solar_vs_temp.png', dpi=150)
plt.close()
print("✅ scatter_solar_vs_temp.png saved")

# ── Plot 2: Solar vs Rainfall ─────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 6))
for prov, grp in df.groupby('province'):
    color = COLORS.get(prov, '#888888')
    ax.scatter(grp['Rainfall'], grp['Solar_Yield'],
               c=color, label=prov, alpha=0.75, edgecolors='white', s=70)

m2, b2, *_ = stats.linregress(df['Rainfall'], df['Solar_Yield'])
x_line2 = np.linspace(df['Rainfall'].min(), df['Rainfall'].max(), 100)
ax.plot(x_line2, m2 * x_line2 + b2, 'k--', linewidth=1.5, label='Trend line')

ax.set_xlabel('Annual Total Rainfall (mm)')
ax.set_ylabel('Solar Yield (kWh/kWp)')
ax.set_title(f'Solar Yield vs Rainfall  |  r = {r_rain:.3f}')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUT_DIR + r'\scatter_solar_vs_rain.png', dpi=150)
plt.close()
print("✅ scatter_solar_vs_rain.png saved")

# ── Plot 3: Correlation Heatmap ───────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(6, 5))
corr_matrix = df[['Solar_Yield', 'Temperature', 'Rainfall']].corr()
mask = np.zeros_like(corr_matrix, dtype=bool)
mask[np.triu_indices_from(mask, k=1)] = False

sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='RdYlGn',
            vmin=-1, vmax=1, ax=ax, linewidths=0.5,
            annot_kws={'size': 13, 'weight': 'bold'})
ax.set_title('Correlation Matrix\nSolar Yield, Temperature & Rainfall')
plt.tight_layout()
plt.savefig(OUT_DIR + r'\correlation_heatmap.png', dpi=150)
plt.close()
print("✅ correlation_heatmap.png saved")

# ── Plot 4: District-level Average Bar Chart ──────────────────────────────────
district_avg = df.groupby('district')[['Solar_Yield', 'Temperature', 'Rainfall']].mean().round(2)

fig, axes = plt.subplots(1, 3, figsize=(14, 5))

district_avg['Solar_Yield'].sort_values().plot(kind='barh', ax=axes[0],
    color='#F4A261', edgecolor='white')
axes[0].set_title('Solar Yield (kWh/kWp)')
axes[0].set_xlabel('kWh/kWp')

district_avg['Temperature'].sort_values().plot(kind='barh', ax=axes[1],
    color='#E76F51', edgecolor='white')
axes[1].set_title('Avg Temperature (°C)')
axes[1].set_xlabel('°C')

district_avg['Rainfall'].sort_values().plot(kind='barh', ax=axes[2],
    color='#2E86AB', edgecolor='white')
axes[2].set_title('Total Rainfall (mm)')
axes[2].set_xlabel('mm')

plt.suptitle('District-wise Comparison: Solar, Temperature & Rainfall',
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(OUT_DIR + r'\district_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ district_comparison.png saved")

# ── Save Summary CSV ──────────────────────────────────────────────────────────
summary = pd.DataFrame({
    'Variable Pair'          : ['Solar vs Temperature', 'Solar vs Rainfall', 'Temperature vs Rainfall'],
    'Pearson r'              : [round(r_temp,4), round(r_rain,4), round(r_tr,4)],
    'p-value'                : [round(p_temp,4), round(p_rain,4), round(p_tr,4)],
    'Significant (p<0.05)'   : [p_temp<0.05, p_rain<0.05, p_tr<0.05],
    'Interpretation'         : [
        'Positive: higher temp → more solar',
        'Negative: more rain → less solar',
        'Inverse: hotter areas are drier'
    ]
})
summary.to_csv(OUT_DIR + r'\correlation_summary.csv', index=False)
print("✅ correlation_summary.csv saved")

print(f"\n{'─'*55}")
print(f"  All outputs saved to:")
print(f"  {OUT_DIR}")
print(f"{'─'*55}")
print(summary.to_string(index=False))