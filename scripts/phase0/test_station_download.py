import requests
import pandas as pd

def test_download(lat, lon, station_id, year):
    """Test all three frequencies for one station"""
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    # Test MONTHLY
    print(f"\n{'='*60}")
    print(f"Testing MONTHLY for station {station_id}")
    print(f"{'='*60}")
    params_monthly = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "monthly": ["temperature_2m_mean", "precipitation_sum", "shortwave_radiation_sum"],
        "timezone": "Asia/Colombo"
    }
    try:
        response = requests.get(url, params=params_monthly, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'monthly' in data:
                print(f"✅ SUCCESS! Got {len(data['monthly']['time'])} months")
            else:
                print(f"❌ No 'monthly' key. Keys: {list(data.keys())}")
        else:
            print(f"❌ FAILED: {response.text[:200]}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test DAILY
    print(f"\n{'='*60}")
    print(f"Testing DAILY for station {station_id}")
    print(f"{'='*60}")
    params_daily = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "daily": ["temperature_2m_mean", "precipitation_sum", "shortwave_radiation_sum"],
        "timezone": "Asia/Colombo"
    }
    try:
        response = requests.get(url, params=params_daily, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'daily' in data:
                print(f"✅ SUCCESS! Got {len(data['daily']['time'])} days")
            else:
                print(f"❌ No 'daily' key. Keys: {list(data.keys())}")
        else:
            print(f"❌ FAILED: {response.text[:200]}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

# Test with station 43415 (Vavuniya - we know this one works)
test_download(8.7512, 80.4957, "43415", 2019)

# Test with a rainfall-only station
test_download(7.2906, 79.8478, "01AM0012", 2019)
