import os
import pandas as pd
import requests
from pathlib import Path

# === Constants ===
HEADWATERS_LOCATIONS = ["L1210588"]
DATA_DIR = Path("data")
EBIRD_DATA_FILE = DATA_DIR / "ebird_data.parquet"
EBIRD_API_KEY = os.environ.get("EBIRD_API_KEY")

def fetch_ebird_data(loc_id):
    """Fetches the last 30 days of data for a location."""
    url = f"https://api.ebird.org/v2/data/obs/loc/{loc_id}"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    params = {
        "back": 30,
    }
    
    print(f"Fetching data for location {loc_id} with URL: {url} and params: {params}")
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def main():
    if not EBIRD_API_KEY:
        raise ValueError("EBIRD_API_KEY not found in environment variables.")
        
    all_new_obs = []
    
    for loc_id in HEADWATERS_LOCATIONS:
        try:
            new_data = fetch_ebird_data(loc_id)
            all_new_obs.extend(new_data)
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching data for location {loc_id}: {e}")
            
    if all_new_obs:
        print(f"Successfully fetched {len(all_new_obs)} records.")
    else:
        print("No data was fetched.")

if __name__ == "__main__":
    main()
    
