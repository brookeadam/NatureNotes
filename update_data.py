import os
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime, timedelta

# === Constants ===
EBIRD_REGION_CODE = "US-TX-029"
HEADWATERS_LOCATIONS = ["L1210588"]
DATA_DIR = Path("data")
EBIRD_DATA_FILE = DATA_DIR / "ebird_data.parquet"
EBIRD_API_KEY = os.environ.get("EBIRD_API_KEY")

def fetch_ebird_data(region_id):
    """Fetches a large amount of recent eBird data for a region."""
    url = f"https://api.ebird.org/v2/data/obs/region/{region_id}"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    params = {
        # The 'back' parameter specifies the number of days to go back.
        # Use a very large number to get as much historical data as possible.
        "back": 999999,  
        "maxResults": 10000,
    }
    
    print(f"Fetching data for region {region_id} with URL: {url} and params: {params}")
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def main():
    if not EBIRD_API_KEY:
        raise ValueError("EBIRD_API_KEY not found in environment variables.")
        
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(exist_ok=True)
    
    all_new_obs = []
    print("Fetching ALL historical data...")
    
    try:
        new_data = fetch_ebird_data(EBIRD_REGION_CODE)
        all_new_obs.extend(new_data)
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching data for region {EBIRD_REGION_CODE}: {e}")
        
    if all_new_obs:
        new_df = pd.DataFrame(all_new_obs)
        
        # Filter the data to include only your specific locations
        filtered_df = new_df[new_df['locId'].isin(HEADWATERS_LOCATIONS)]
        
        filtered_df.to_parquet(EBIRD_DATA_FILE, index=False)
        print(f"Successfully created initial data file with {len(filtered_df)} observations.")
    else:
        print("No data was fetched.")
