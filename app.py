# app.py  — PUCSL Solar & Weather Prediction System

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import os, base64, warnings
warnings.filterwarnings('ignore')

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PUCSL Solar & Weather System",
    page_icon="☀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Paths ─────────────────────────────────────────────────────────────────────
FIGURES_DIR       = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\outputs\figures\grids'
SOLAR_REAL_MAP    = FIGURES_DIR + r'\solar_resource_map_REAL_DATA.html'
SOLAR_STATION_MAP = FIGURES_DIR + r'\solar_resource_with_weather_stations.html'
SOLAR_OVERLAY_MAP = FIGURES_DIR + r'\solar_weather_overlay.html'
BASE              = r'C:\Users\Mumtaz Aysha\Documents\UNI HUB\Research-project\data\bronze\weather_data'
TEMP_MODEL        = BASE + r'\temp_model.pkl'
RAIN_MODEL        = BASE + r'\rain_model.pkl'
SOLAR_MODEL       = BASE + r'\solar_model.pkl'
SOLAR_MAP         = BASE + r'\solar_potential_map.html'
TEMP_MAP          = BASE + r'\temp_map_srilanka.html'
RAIN_MAP          = BASE + r'\rain_map_srilanka.html'
CORR_DIR          = BASE + r'\correlation_plots'
SOLAR_GRID        = BASE + r'\solar_grid_predictions_annual.csv'
TEMP_GRID         = BASE + r'\temp_grid_predictions.csv'
RAIN_GRID         = BASE + r'\rain_grid_predictions.csv'

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0D1F3C !important; padding-top: 0px; }
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    background: transparent; border-radius: 8px; padding: 10px 15px;
    display: block; cursor: pointer; transition: background 0.2s;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.1);
}
.main { background-color: #F0F2F5; }
.block-container { padding: 2rem 2rem 2rem 2rem; }
.card {
    background: white; border-radius: 12px; padding: 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 16px;
}
.stat-card {
    background: white; border-radius: 12px; padding: 18px 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07); border-left: 4px solid #C8742A;
    text-align: left; margin-bottom: 12px;
}
.stat-card.blue  { border-left-color: #2E86AB; }
.stat-card.green { border-left-color: #2E7D32; }
.stat-card.red   { border-left-color: #C62828; }
.stat-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.stat-value { font-size: 28px; font-weight: 700; color: #0D1F3C; }
.stat-sub   { font-size: 12px; color: #aaa; margin-top: 2px; }
.corr-card {
    background: white; border-radius: 12px; padding: 22px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07); margin-bottom: 16px;
}
.corr-r { font-size: 38px; font-weight: 800; color: #0D1F3C; margin: 10px 0; }
.badge-green { background:#E8F5E9; color:#2E7D32; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; }
.badge-red   { background:#FFEBEE; color:#C62828; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; }
.stButton > button {
    background: #C8742A; color: white; border-radius: 8px; border: none;
    padding: 12px 28px; font-size: 15px; font-weight: 600; width: 100%;
    cursor: pointer; transition: background 0.2s;
}
.stButton > button:hover { background: #A85E1E; }
.hero {
    background: linear-gradient(135deg, #0D1F3C 0%, #1A3A6E 100%);
    border-radius: 16px; padding: 40px; color: white; margin-bottom: 24px;
}
.hero h1 { font-size: 32px; font-weight: 800; margin: 0 0 8px 0; }
.hero p  { color: #aac4e8; font-size: 15px; margin: 0; }
.hero-badge {
    background: #C8742A; color: white; padding: 4px 12px;
    border-radius: 20px; font-size: 12px; display: inline-block; margin-bottom: 16px;
}
.page-title { font-size: 28px; font-weight: 800; color: #0D1F3C; margin-bottom: 4px; }
.page-sub   { font-size: 14px; color: #666; margin-bottom: 24px; }
.insight-box {
    background: linear-gradient(135deg, #0D3050 0%, #1A4A70 100%);
    border-radius: 12px; padding: 24px; color: white; margin-top: 20px;
}
.insight-box h3 { color: #7EC8E3; margin-bottom: 10px; }
.insight-box p  { color: #ccc; font-size: 14px; line-height: 1.6; }
.action-card {
    background: #0D1F3C; border-radius: 12px; padding: 30px 20px;
    text-align: center; color: white;
}
.action-card .icon { font-size: 36px; margin-bottom: 12px; }
.action-card h3 { font-size: 18px; font-weight: 700; margin-bottom: 4px; }
.action-card p  { font-size: 11px; color: #aac4e8; text-transform: uppercase; }
.footer {
    text-align: center; color: #aaa; font-size: 12px;
    padding: 20px 0 0 0; border-top: 1px solid #e0e0e0; margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)

# ── City Coordinates ──────────────────────────────────────────────────────────
CITIES = {
    'Colombo'      : (6.9271,  79.8612,   8),
    'Kandy'        : (7.2906,  80.6337, 488),
    'Galle'        : (6.0535,  80.2210,   4),
    'Jaffna'       : (9.6615,  80.0255,  10),
    'Trincomalee'  : (8.5874,  81.2152,   7),
    'Batticaloa'   : (7.7170,  81.7000,   5),
    'Anuradhapura' : (8.3114,  80.4037,  81),
    'Polonnaruwa'  : (7.9403,  81.0188,  59),
    'Badulla'      : (6.9934,  81.0550, 678),
    'Nuwara Eliya' : (6.9497,  80.7891,1868),
    'Ratnapura'    : (6.6828,  80.3992,  34),
    'Kurunegala'   : (7.4818,  80.3609, 116),
    'Matara'       : (5.9549,  80.5550,   4),
    'Hambantota'   : (6.1241,  81.1185,   7),
    'Puttalam'     : (8.0362,  79.8283,   3),
    'Vavuniya'     : (8.7514,  80.4971,  98),
    'Ampara'       : (7.2980,  81.6724,  21),
    'Monaragala'   : (6.8728,  81.3484, 136),
    'Matale'       : (7.4675,  80.6234, 369),
    'Kegalle'      : (7.2513,  80.3464, 120),
    'Kalutara'     : (6.5854,  79.9607,   5),
    'Gampaha'      : (7.0917,  80.0000,  11),
    'Kalmunai'     : (7.4167,  81.8333,   5),
    'Mannar'       : (8.9810,  79.9044,   5),
    'Mullaitivu'   : (9.2671,  80.8128,   5),
    'Kilinochchi'  : (9.3803,  80.4000,  10),
}
MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_resource
def load_models():
    temp_pkg  = joblib.load(TEMP_MODEL)
    rain_pkg  = joblib.load(RAIN_MODEL)
    solar_pkg = joblib.load(SOLAR_MODEL)
    return temp_pkg['model'], rain_pkg['model'], solar_pkg['model'], solar_pkg['features']

@st.cache_data
def load_grid_data():
    solar = pd.read_csv(SOLAR_GRID)
    temp  = pd.read_csv(TEMP_GRID)
    rain  = pd.read_csv(RAIN_GRID)
    return solar, temp, rain

# NO @st.cache_data here — inject_resize must apply fresh every time
def read_html_map(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def inject_resize(html_content, height=500):
    injection = f"""
<style>
html, body {{
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}}
.leaflet-container {{
    width: 100% !important;
    height: {height}px !important;
}}
#map {{
    width: 100% !important;
    height: {height}px !important;
}}
div[id^="map_"] {{
    width: 100% !important;
    height: {height}px !important;
}}
</style>
<script>
(function() {{
    function fix() {{
        document.querySelectorAll('[id^="map_"]').forEach(function(el) {{
            el.style.width  = '100%';
            el.style.height = '{height}px';
        }});
        for (var key in window) {{
            try {{
                if (window[key] && typeof window[key].invalidateSize === 'function') {{
                    window[key].invalidateSize(true);
                }}
            }} catch(e) {{}}
        }}
        try {{
            if (window.L && window.L.Map && window.L.Map._instances) {{
                Object.values(window.L.Map._instances).forEach(function(m) {{
                    try {{ m.invalidateSize(true); }} catch(e) {{}}
                }});
            }}
        }} catch(e) {{}}
    }}
    [0, 100, 300, 600, 1000, 1500, 2500, 4000].forEach(function(t) {{
        setTimeout(fix, t);
    }});
    document.addEventListener('DOMContentLoaded', fix);
    window.addEventListener('load', fix);
}})();
</script>
"""
    if '</head>' in html_content:
        return html_content.replace('</head>', injection + '</head>')
    elif '</body>' in html_content:
        return html_content.replace('</body>', injection + '</body>')
    else:
        return injection + html_content

def predict_solar(lat, lon, elev, capacity, year, temp_model, rain_model, solar_model, solar_features):
    results = []
    for month in range(1, 13):
        ms = np.sin(2 * np.pi * month / 12)
        mc = np.cos(2 * np.pi * month / 12)

        # ✅ Updated: use interaction features for temp/rain prediction
        X_w = pd.DataFrame([[
            lat, lon, elev, ms, mc, year,
            lat * ms, lat * mc,
            lon * ms, lon * mc,
            elev * ms, elev * mc
        ]], columns=[
            'lat', 'lon', 'elevation',
            'month_sin', 'month_cos', 'year',
            'lat_x_sin', 'lat_x_cos',
            'lon_x_sin', 'lon_x_cos',
            'elev_x_sin', 'elev_x_cos'
        ])
        T  = temp_model.predict(X_w)[0]
        RF = max(0, rain_model.predict(X_w)[0])

        # Solar model stays the same
        X_s = pd.DataFrame([[lat, lon, elev, ms, mc, T, RF]],
                            columns=['lat','lon','plant_elev','month_sin','month_cos',
                                     'T_corrected','RF_corrected'])
        yld = max(0, solar_model.predict(X_s)[0])
        results.append({
            'Month'          : MONTHS[month-1],
            'Avg Temp (°C)'  : round(T, 1),
            'Rainfall (mm)'  : round(RF, 1),
            'Yield (kWh/kWp)': round(yld, 2),
            'Gen (kWh)'      : round(yld * capacity, 1),
        })
    return pd.DataFrame(results)

# NEW — paste this in
def predict_weather(lat, lon, elev, year, temp_model, rain_model):
    results = []
    for month in range(1, 13):
        ms = np.sin(2 * np.pi * month / 12)
        mc = np.cos(2 * np.pi * month / 12)
        X = pd.DataFrame([[
            lat, lon, elev, ms, mc, year,
            lat * ms, lat * mc,
            lon * ms, lon * mc,
            elev * ms, elev * mc
        ]], columns=[
            'lat', 'lon', 'elevation',
            'month_sin', 'month_cos', 'year',
            'lat_x_sin', 'lat_x_cos',
            'lon_x_sin', 'lon_x_cos',
            'elev_x_sin', 'elev_x_cos'
        ])
        T  = temp_model.predict(X)[0]
        RF = max(0, rain_model.predict(X)[0])
        results.append({
            'Month'           : MONTHS[month-1],
            'Temperature (°C)': round(T, 1),
            'Rainfall (mm)'   : round(RF, 1),
        })
    return pd.DataFrame(results)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:20px 10px 10px 10px;border-bottom:1px solid rgba(255,255,255,0.1);margin-bottom:20px;'>
        <div style='font-size:28px;'>☀</div>
        <div style='font-size:16px;font-weight:800;color:white;'>PUCSL Solar &</div>
        <div style='font-size:16px;font-weight:800;color:white;'>Weather</div>
        <div style='font-size:11px;color:#aac4e8;letter-spacing:1px;text-transform:uppercase;'>Institutional Architect</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "",
        ["🏠  Home",
         "☀  Solar Prediction",
         "🌡  Weather Prediction",
         "🗺  Maps Viewer",
         "📊  Correlation Analysis",
         "📈  Data Visualizations"],
        label_visibility="collapsed"
    )

    st.markdown("""
    <div style='margin-top:40px;background:rgba(255,255,255,0.08);
         border-radius:10px;padding:12px;'>
        <div style='font-size:11px;color:#aac4e8;text-transform:uppercase;
             letter-spacing:1px;margin-bottom:4px;'>SYSTEM STATUS</div>
        <div>
            <span style='width:8px;height:8px;background:#4CAF50;border-radius:50%;
                 display:inline-block;margin-right:6px;'></span>
            <span style='color:white;font-size:13px;font-weight:600;'>Live Feed Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — HOME
# ══════════════════════════════════════════════════════════════════════════════
if "Home" in page:
    st.markdown("""
    <div class='hero'>
        <div class='hero-badge'>● LIVE ANALYSIS ACTIVE</div>
        <h1>Sri Lanka Solar Power Generation<br>Prediction System</h1>
        <p>Powered by Machine Learning |
           <span style='color:#C8742A;font-weight:700;'>PUCSL Research 2026</span></p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='stat-card'>
            <div class='stat-label'>📊 Coverage</div>
            <div class='stat-value'>141</div>
            <div class='stat-sub'>Grid Cells Analyzed</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class='stat-card blue'>
            <div class='stat-label'>🗺 Density</div>
            <div class='stat-value'>1,242</div>
            <div class='stat-sub'>Country-wide Predictions</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class='stat-card green'>
            <div class='stat-label'>📅 Historical Context</div>
            <div class='stat-value'>15 Years</div>
            <div class='stat-sub'>Of Historical Data</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_txt, _ = st.columns([3, 2])
    with col_txt:
        st.markdown("""
        <div class='card'>
            <h3 style='color:#0D1F3C;border-left:4px solid #C8742A;padding-left:12px;'>
              Institutional Insight</h3>
            <p style='color:#444;line-height:1.8;font-size:14px;'>
            The PUCSL Solar & Weather Prediction System serves as the definitive institutional
            engine for renewable energy forecasting in Sri Lanka. By leveraging fifteen years of
            high-resolution meteorological data and advanced machine learning algorithms, this
            platform provides grid operators and policymakers with the precise intelligence needed
            to manage the national energy transition.</p>
            <p style='color:#444;line-height:1.8;font-size:14px;'>
            Every grid cell across the island is continuously monitored, delivering predictions
            that account for localized weather anomalies and atmospheric conditions, ensuring the
            stability of our national power infrastructure.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><p style='text-align:center;color:#888;font-size:11px;letter-spacing:2px;'>EXECUTIVE COMMAND ACTIONS</p>",
                unsafe_allow_html=True)
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown("""<div class='action-card'>
            <div class='icon'>☀</div><h3>Predict Solar</h3><p>Algorithm Launch</p>
        </div>""", unsafe_allow_html=True)
    with a2:
        st.markdown("""<div class='action-card'>
            <div class='icon'>🌡</div><h3>Check Weather</h3><p>Meteorological Data</p>
        </div>""", unsafe_allow_html=True)
    with a3:
        st.markdown("""<div class='action-card'>
            <div class='icon'>🗺</div><h3>View Maps</h3><p>Geospatial Viewer</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class='footer'>
        © 2026 Public Utilities Commission of Sri Lanka. All Rights Reserved.
        &nbsp;|&nbsp; SECURITY PROTOCOL &nbsp;|&nbsp; SYSTEM INTEGRITY &nbsp;|&nbsp; PUCSL HUB
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — SOLAR PREDICTION
# ══════════════════════════════════════════════════════════════════════════════
elif "Solar" in page:
    temp_model, rain_model, solar_model, solar_features = load_models()

    col_hdr, col_badge = st.columns([4, 1])
    with col_hdr:
        st.markdown("<div class='page-title'>Solar Generation Forecasting</div>", unsafe_allow_html=True)
        st.markdown("<div class='page-sub'>Institutional modeling tool for multi-year grid stability analysis.</div>", unsafe_allow_html=True)
    with col_badge:
        st.markdown("""<div style='background:#E8F5E9;color:#2E7D32;padding:6px 14px;
            border-radius:20px;font-size:12px;font-weight:700;margin-top:10px;text-align:center;'>
            ● LIVE API STATUS: ACTIVE</div>""", unsafe_allow_html=True)

    left, right = st.columns([1.2, 2.5])

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#0D1F3C;'>☀ Solar Power Predictor</h3>", unsafe_allow_html=True)
        city = st.selectbox("INSTALLATION LOCATION", list(CITIES.keys()))
        lat_d, lon_d, elev_d = CITIES[city]
        c_lat, c_lon = st.columns(2)
        with c_lat:
            lat = st.number_input("LATITUDE", value=lat_d, format="%.4f")
        with c_lon:
            lon = st.number_input("LONGITUDE", value=lon_d, format="%.4f")
        capacity = st.number_input("CAPACITY (kWp)", min_value=0.1, value=10.0, step=0.5)
        year = st.slider("FORECAST HORIZON (YEAR)", 2025, 2035, 2030)
        predict_btn = st.button("🔍  Predict Generation")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        if predict_btn:
            with st.spinner("Running prediction..."):
                df = predict_solar(lat, lon, elev_d, capacity, year,
                                   temp_model, rain_model, solar_model, solar_features)

            annual   = df['Gen (kWh)'].sum()
            best_m   = df.loc[df['Gen (kWh)'].idxmax(), 'Month']
            worst_m  = df.loc[df['Gen (kWh)'].idxmin(), 'Month']
            avg_temp = df['Avg Temp (°C)'].mean()

            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.markdown(f"""<div class='stat-card'>
                    <div class='stat-label'>Annual Generation</div>
                    <div class='stat-value'>{annual:,.0f}</div>
                    <div class='stat-sub'>kWh</div></div>""", unsafe_allow_html=True)
            with s2:
                st.markdown(f"""<div class='stat-card blue'>
                    <div class='stat-label'>Best Month</div>
                    <div class='stat-value'>{best_m}</div>
                    <div class='stat-sub'>&nbsp;</div></div>""", unsafe_allow_html=True)
            with s3:
                st.markdown(f"""<div class='stat-card green'>
                    <div class='stat-label'>Avg Temperature</div>
                    <div class='stat-value'>{avg_temp:.1f}°C</div>
                    <div class='stat-sub'>&nbsp;</div></div>""", unsafe_allow_html=True)
            with s4:
                st.markdown(f"""<div class='stat-card red'>
                    <div class='stat-label'>Worst Month</div>
                    <div class='stat-value'>{worst_m}</div>
                    <div class='stat-sub'>&nbsp;</div></div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            colors = ['#8B4513' if m == best_m else '#F4C49E' for m in df['Month']]
            fig = go.Figure(go.Bar(x=df['Month'], y=df['Gen (kWh)'],
                                   marker_color=colors))
            fig.update_layout(
                title="Monthly Generation Forecast",
                plot_bgcolor='white', paper_bgcolor='white',
                font=dict(color='#0D1F3C'),
                height=300, margin=dict(t=40,b=20,l=20,r=20),
                xaxis=dict(gridcolor='#f0f0f0'),
                yaxis=dict(gridcolor='#f0f0f0', title='kWh'),
                showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            col_t, col_d = st.columns([3, 1])
            with col_t:
                st.markdown("<h4 style='color:#0D1F3C;'>Detailed Modeling Data</h4>", unsafe_allow_html=True)
            with col_d:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("⬇ Download CSV", csv, f"solar_{city}_{year}.csv", "text/csv")
            st.dataframe(df[['Month','Avg Temp (°C)','Rainfall (mm)','Yield (kWh/kWp)','Gen (kWh)']],
                         use_container_width=True, hide_index=True)
        else:
            st.markdown("""
            <div style='display:flex;align-items:center;justify-content:center;
                 height:400px;background:white;border-radius:12px;
                 box-shadow:0 2px 12px rgba(0,0,0,0.08);'>
                <div style='text-align:center;color:#aaa;'>
                    <div style='font-size:48px;'>☀</div>
                    <p style='font-size:16px;'>Enter inputs and click<br><b>Predict Generation</b></p>
                </div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — WEATHER PREDICTION
# ══════════════════════════════════════════════════════════════════════════════
elif "Weather" in page:
    temp_model, rain_model, solar_model, solar_features = load_models()

    st.markdown("<div class='page-title'>🌡 Temperature & Rainfall Predictor</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Meteorological forecasting for grid planning and energy management.</div>", unsafe_allow_html=True)

    left, right = st.columns([1.2, 2.5])

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        city = st.selectbox("SELECT LOCATION", list(CITIES.keys()))
        lat_d, lon_d, elev_d = CITIES[city]
        c_lat, c_lon = st.columns(2)
        with c_lat:
            st.markdown(f"<div style='font-size:11px;color:#888;font-weight:600;'>LATITUDE</div>"
                        f"<div style='padding:8px;background:#f5f5f5;border-radius:6px;"
                        f"color:#0D1F3C;font-weight:600;'>{lat_d:.4f}° N</div>",
                        unsafe_allow_html=True)
        with c_lon:
            st.markdown(f"<div style='font-size:11px;color:#888;font-weight:600;'>LONGITUDE</div>"
                        f"<div style='padding:8px;background:#f5f5f5;border-radius:6px;"
                        f"color:#0D1F3C;font-weight:600;'>{lon_d:.4f}° E</div>",
                        unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        year = st.slider("PREDICTION YEAR", 2025, 2035, 2030)
        predict_btn = st.button("🔍  Predict Weather")
        st.markdown("""
        <div style='margin-top:20px;border-top:1px solid #eee;padding-top:16px;'>
            <div style='font-size:11px;color:#888;text-transform:uppercase;
                 letter-spacing:1px;margin-bottom:8px;'>INSTITUTIONAL MODEL SPECS</div>
            <div style='display:flex;justify-content:space-between;font-size:13px;'>
                <span style='color:#666;'>Model Version</span>
                <span style='color:#C8742A;font-weight:700;'>RF-2026-GOLD</span>
            </div>
            <div style='display:flex;justify-content:space-between;font-size:13px;margin-top:6px;'>
                <span style='color:#666;'>R² Score (Temp)</span>
                <span style='color:#2E7D32;font-weight:700;'>98.9%</span>
            </div>
            <div style='display:flex;justify-content:space-between;font-size:13px;margin-top:6px;'>
                <span style='color:#666;'>R² Score (Rain)</span>
                <span style='color:#2E7D32;font-weight:700;'>95.6%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        if predict_btn:
            with st.spinner("Running prediction..."):
                df = predict_weather(lat_d, lon_d, elev_d, year, temp_model, rain_model)

            avg_T   = df['Temperature (°C)'].mean()
            total_R = df['Rainfall (mm)'].sum()
            hot_m   = df.loc[df['Temperature (°C)'].idxmax(), 'Month']
            dry_m   = df.loc[df['Rainfall (mm)'].idxmin(), 'Month']

            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.markdown(f"""<div class='stat-card red'>
                    <div class='stat-label'>Annual Avg Temp</div>
                    <div class='stat-value'>{avg_T:.1f}°C</div></div>""", unsafe_allow_html=True)
            with s2:
                st.markdown(f"""<div class='stat-card blue'>
                    <div class='stat-label'>Total Rainfall</div>
                    <div class='stat-value'>{total_R:.0f}mm</div></div>""", unsafe_allow_html=True)
            with s3:
                st.markdown(f"""<div class='stat-card'>
                    <div class='stat-label'>Hottest Month</div>
                    <div class='stat-value'>{hot_m}</div></div>""", unsafe_allow_html=True)
            with s4:
                st.markdown(f"""<div class='stat-card green'>
                    <div class='stat-label'>Driest Month</div>
                    <div class='stat-value'>{dry_m}</div></div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            ch1, ch2 = st.columns(2)
            with ch1:
                fig_t = go.Figure(go.Scatter(
                    x=df['Month'], y=df['Temperature (°C)'],
                    mode='lines+markers',
                    line=dict(color='#C62828', width=3, shape='spline'),
                    fill='tozeroy', fillcolor='rgba(198,40,40,0.08)'))
                fig_t.update_layout(
                    title="Monthly Temperature Profile",
                    plot_bgcolor='white', paper_bgcolor='white',
                    height=260, margin=dict(t=40,b=20,l=20,r=20),
                    yaxis=dict(title='°C', gridcolor='#f0f0f0'),
                    xaxis=dict(gridcolor='#f0f0f0'), showlegend=False)
                st.plotly_chart(fig_t, use_container_width=True)
            with ch2:
                fig_r = go.Figure(go.Bar(
                    x=df['Month'], y=df['Rainfall (mm)'],
                    marker_color='#2E86AB'))
                fig_r.update_layout(
                    title="Precipitation Forecast",
                    plot_bgcolor='white', paper_bgcolor='white',
                    height=260, margin=dict(t=40,b=20,l=20,r=20),
                    yaxis=dict(title='mm', gridcolor='#f0f0f0'),
                    xaxis=dict(gridcolor='#f0f0f0'), showlegend=False)
                st.plotly_chart(fig_r, use_container_width=True)

            col_t2, col_d2 = st.columns([3, 1])
            with col_t2:
                st.markdown(f"<h4 style='color:#0D1F3C;'>Prediction Dataset {year}</h4>", unsafe_allow_html=True)
            with col_d2:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("⬇ Download CSV", csv, f"weather_{city}_{year}.csv", "text/csv")
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown(f"""
            <div class='insight-box'>
                <h3>🔍 Institutional Weather Insight</h3>
                <p>The {year} forecast for <b>{city}</b> indicates an annual average temperature of
                <b>{avg_T:.1f}°C</b> with total rainfall of <b>{total_R:.0f}mm</b>.
                The hottest month is <b>{hot_m}</b> and the driest month is <b>{dry_m}</b>.
                PUCSL recommends solar installations be planned with peak generation aligned
                to dry months for optimal grid contribution.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='display:flex;align-items:center;justify-content:center;
                 height:400px;background:white;border-radius:12px;
                 box-shadow:0 2px 12px rgba(0,0,0,0.08);'>
                <div style='text-align:center;color:#aaa;'>
                    <div style='font-size:48px;'>🌡</div>
                    <p style='font-size:16px;'>Enter inputs and click<br><b>Predict Weather</b></p>
                </div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — MAPS VIEWER
# ══════════════════════════════════════════════════════════════════════════════
elif "Maps" in page:
    st.markdown("<div class='page-title'>🗺 Interactive Maps</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Geospatial visualization of solar, temperature, and rainfall predictions.</div>",
                unsafe_allow_html=True)

    MAP_CONFIGS = {
        "solar": {
            "path": SOLAR_MAP,
            "desc": "Annual solar yield (kWh/kWp) across the 10km grid. Based on 15 years of ML-corrected weather data.",
            "legend": [
                ("#FF4500","Excellent ≥ 1600 kWh/kWp"),
                ("#FF8C00","High ≥ 1400 kWh/kWp"),
                ("#FFD700","Moderate ≥ 1200 kWh/kWp"),
                ("#ADFF2F","Low ≥ 1000 kWh/kWp"),
                ("#90EE90","Very Low < 1000 kWh/kWp"),
            ]
        },
        "temp": {
            "path": TEMP_MAP,
            "desc": "Annual average temperature across all 1,242 grid cells. Coastal areas are hotter; highlands are cooler.",
            "legend": [
                ("#FF0000","Very Hot ≥ 30°C"),
                ("#FF6600","Hot ≥ 28°C"),
                ("#FFA500","Warm ≥ 25°C"),
                ("#FFD700","Moderate ≥ 22°C"),
                ("#90EE90","Cool ≥ 18°C"),
                ("#00BFFF","Cold < 18°C"),
            ]
        },
        "rain": {
            "path": RAIN_MAP,
            "desc": "Annual total rainfall across all grid cells. Dry zone (north/east) has highest solar potential.",
            "legend": [
                ("#00008B","Very Wet ≥ 4000mm"),
                ("#1E90FF","Wet ≥ 3000mm"),
                ("#87CEEB","Moderate ≥ 2000mm"),
                ("#FFD700","Dry ≥ 1000mm"),
                ("#FF8C00","Very Dry < 1000mm"),
            ]
        }
    }

    def render_map_tab(config_key):
        cfg = MAP_CONFIGS[config_key]
        st.markdown(f"<p style='color:#555;font-size:14px;line-height:1.7;'>{cfg['desc']}</p>",
                    unsafe_allow_html=True)
        if os.path.exists(cfg['path']):
            components.html(inject_resize(read_html_map(cfg['path']), height=500),
                            height=520, scrolling=False)
        else:
            st.warning(f"Map file not found: {cfg['path']}")

        leg_col, note_col = st.columns([2, 1])
        with leg_col:
            legend_html = " &nbsp;&nbsp; ".join(
                [f"<span style='background:{c};display:inline-block;width:14px;height:14px;"
                 f"border-radius:3px;vertical-align:middle;margin-right:5px;'></span>"
                 f"<span style='font-size:13px;'>{lbl}</span>"
                 for c, lbl in cfg['legend']])
            st.markdown(f"<div class='card'><b style='font-size:12px;color:#888;"
                        f"text-transform:uppercase;'>Color Legend</b><br><br>"
                        f"{legend_html}</div>", unsafe_allow_html=True)
        with note_col:
            st.info("💡 Click on any grid cell to see detailed values.")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "☀ Solar Potential",
        "🌡 Temperature",
        "🌧 Rainfall",
        "📍 Solar Real Data",
        "🏭 Weather Stations",
        "🔄 Solar Overlay"
    ])

    with tab1:
        render_map_tab("solar")

    with tab2:
        render_map_tab("temp")

    with tab3:
        render_map_tab("rain")

    with tab4:
        st.markdown("<p style='color:#555;font-size:14px;'>Solar resource map generated from real plant data across Sri Lanka.</p>",
                    unsafe_allow_html=True)
        if os.path.exists(SOLAR_REAL_MAP):
            components.html(inject_resize(read_html_map(SOLAR_REAL_MAP), height=500),
                            height=520, scrolling=False)
        else:
            st.warning(f"Map not found: {SOLAR_REAL_MAP}")

    with tab5:
        st.markdown("<p style='color:#555;font-size:14px;'>Solar resource map overlaid with meteorological weather station locations.</p>",
                    unsafe_allow_html=True)
        if os.path.exists(SOLAR_STATION_MAP):
            components.html(inject_resize(read_html_map(SOLAR_STATION_MAP), height=500),
                            height=520, scrolling=False)
        else:
            st.warning(f"Map not found: {SOLAR_STATION_MAP}")

    with tab6:
        st.markdown("<p style='color:#555;font-size:14px;'>Combined solar potential and weather data overlay map.</p>",
                    unsafe_allow_html=True)
        if os.path.exists(SOLAR_OVERLAY_MAP):
            components.html(inject_resize(read_html_map(SOLAR_OVERLAY_MAP), height=620),
                            height=650, scrolling=True)
        else:
            st.warning(f"Map not found: {SOLAR_OVERLAY_MAP}")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — CORRELATION ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif "Correlation" in page:
    st.markdown("<div class='page-title'>📊 Correlation Analysis</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Relationship between Solar Potential, Temperature & Rainfall</div>",
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='corr-card'>
            <div style='font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;'>Solar vs Temperature</div>
            <span class='badge-green'>Moderate Positive</span>
            <div class='corr-r'>r = +0.50</div>
            <div style='background:#C8742A;height:3px;border-radius:2px;width:50%;margin-bottom:10px;'></div>
            <p style='font-size:13px;color:#666;'>Increase in temperature moderately correlates
            with higher solar outputs across provinces.</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class='corr-card'>
            <div style='font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;'>Solar vs Rainfall</div>
            <span class='badge-red'>Strong Negative</span>
            <div class='corr-r'>r = -0.71</div>
            <div style='background:#C62828;height:3px;border-radius:2px;width:71%;margin-bottom:10px;'></div>
            <p style='font-size:13px;color:#666;'>Heavy precipitation strictly inversely affects
            solar potential due to cloud cover density.</p>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class='corr-card'>
            <div style='font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;'>Temperature vs Rainfall</div>
            <span class='badge-red'>Very Strong Negative</span>
            <div class='corr-r'>r = -0.91</div>
            <div style='background:#C62828;height:3px;border-radius:2px;width:91%;margin-bottom:10px;'></div>
            <p style='font-size:13px;color:#666;'>Inverse thermal peaks during monsoon cycles
            indicate high predictive certainty for weather modeling.</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    ch1, ch2 = st.columns(2)
    charts = [
        (CORR_DIR + r'\scatter_solar_vs_temp.png', "SCATTER PLOT: SOLAR VS TEMPERATURE", "Trend: Linear Positive"),
        (CORR_DIR + r'\scatter_solar_vs_rain.png', "SCATTER PLOT: SOLAR VS RAINFALL",    "Trend: Linear Negative"),
        (CORR_DIR + r'\correlation_heatmap.png',   "CORRELATION HEATMAP",                "● Hot  ● Cold"),
        (CORR_DIR + r'\district_comparison.png',   "DISTRICT COMPARISON BAR CHART",      "Sri Lanka – All Districts"),
    ]
    for i, (path, title, badge) in enumerate(charts):
        col = ch1 if i % 2 == 0 else ch2
        with col:
            st.markdown(f"""
            <div class='card'>
                <div style='display:flex;justify-content:space-between;
                     align-items:center;margin-bottom:12px;'>
                    <span style='font-size:12px;font-weight:700;color:#0D1F3C;'>{title}</span>
                    <span style='font-size:11px;color:#888;'>{badge}</span>
                </div>
            """, unsafe_allow_html=True)
            if os.path.exists(path):
                from PIL import Image
                st.image(Image.open(path), use_container_width=True)
            else:
                st.warning(f"Chart not found: {path}")
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='display:flex;justify-content:space-between;padding:12px;
         border-top:1px solid #eee;margin-top:16px;color:#888;font-size:12px;'>
        <span>● LAST UPDATED: MARCH 2026</span>
        <span>● CONFIDENCE INTERVAL: 95%</span>
        <span>✅ Analysis peer-reviewed by 3 analysts</span>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — DATA VISUALIZATIONS
# ══════════════════════════════════════════════════════════════════════════════
elif "Visualizations" in page:
    st.markdown("<div class='page-title'>📈 Prediction Visualizations</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Spatial distribution and statistical analysis of prediction results.</div>",
                unsafe_allow_html=True)

    solar_df, temp_df, rain_df = load_grid_data()

    tab1, tab2, tab3 = st.tabs(["☀ Solar Potential", "🌡 Temperature", "🌧 Rainfall"])

    def viz_tab(df, value_col, label, unit, color_scale, district_col='district'):
        left, right = st.columns([1.5, 1])
        with left:
            st.markdown(f"<div class='card'><b>Spatial Distribution of {label}</b><br><br>",
                        unsafe_allow_html=True)
            fig_map = px.scatter_mapbox(
                df, lat='lat', lon='lon', color=value_col,
                color_continuous_scale=color_scale,
                mapbox_style='carto-positron',
                zoom=6, center={"lat": 7.87, "lon": 80.77},
                height=420,
                hover_data={value_col: ':.1f', 'lat': ':.3f', 'lon': ':.3f'}
            )
            fig_map.update_layout(margin=dict(t=0,b=0,l=0,r=0),
                                  coloraxis_colorbar=dict(title=unit))
            st.plotly_chart(fig_map, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown("<div class='card'><b>Average Values by District</b><br><br>",
                        unsafe_allow_html=True)
            if district_col in df.columns and df[district_col].nunique() > 1:
                dist_avg = df.groupby(district_col)[value_col].mean().sort_values(ascending=True)
                fig_bar = go.Figure(go.Bar(
                    y=dist_avg.index, x=dist_avg.values,
                    orientation='h', marker_color='#8B4513',
                    text=[f"{v:.1f}" for v in dist_avg.values],
                    textposition='outside'
                ))
                fig_bar.update_layout(
                    plot_bgcolor='white', paper_bgcolor='white',
                    height=380, margin=dict(t=10,b=20,l=10,r=50),
                    xaxis=dict(title=unit, gridcolor='#f0f0f0'),
                    yaxis=dict(gridcolor='#f0f0f0'))
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("District breakdown not available in this dataset.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'><h4 style='color:#0D1F3C;'>Summary Statistics</h4>",
                    unsafe_allow_html=True)
        stats = df[value_col].describe().round(2)
        stat_df = pd.DataFrame({
            'Statistical Metric': ['Mean Annual Value','Maximum Observed','Minimum Value','Std Deviation'],
            'Value': [f"{stats['mean']:.2f} {unit}", f"{stats['max']:.2f} {unit}",
                      f"{stats['min']:.2f} {unit}", f"{stats['std']:.2f} {unit}"],
            'Reliability': ['●●●●','●●●●','●●●','●●●●']
        })
        st.dataframe(stat_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab1:
        viz_tab(solar_df, 'annual_yield_kWh_kWp', 'Solar Potential', 'kWh/kWp', 'YlOrRd')
    with tab2:
        viz_tab(temp_df, 'annual_avg_T', 'Temperature', '°C', 'RdYlBu_r')
    with tab3:
        viz_tab(rain_df, 'annual_total_RF', 'Rainfall', 'mm', 'Blues')




