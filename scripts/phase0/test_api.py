import requests
from datetime import datetime

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 6.9,
    "longitude": 79.9,
    "start_date": "2019-01-01",
    "end_date": "2019-01-02",
    "daily": ["temperature_2m_max"],
    "timezone": "Asia/Colombo"
}

print(f"\n{'='*60}")
print(f"⏰ Testing at: {datetime.now().strftime('%I:%M:%S %p')}")
print(f"{'='*60}")
print("🌐 Accessing Open-Meteo API...")

try:
    response = requests.get(url, params=params, timeout=10)
    
    print(f"\n📡 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ API IS WORKING!")
        print("   You can download data.")
        print("   Issue might be with the batch script.")
    elif response.status_code == 429:
        print("❌ RATE LIMITED!")
        print("   Your IP is temporarily blocked.")
        print("   ⏰ Wait until 1:00 PM and try again.")
    else:
        print(f"❌ ERROR: {response.status_code}") 
        print(f"   Message: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ CONNECTION ERROR: {e}")
    print("   Check your internet connection.")

print(f"{'='*60}\n")
