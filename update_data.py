import os
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime, timedelta

# === Constants ===
# Use a single locality ID
HEADWATERS_LOCATIONS = ["L1210588"]
DATA_DIR = Path("data")
EBIRD_DATA_FILE = DATA_DIR / "ebird_data.parquet"
EBIRD_API_KEY = os.environ.get("EBIRD_API_KEY")

def fetch_ebird_data(loc_id):
    """Fetches all eBird data for a location since the start of eBird."""
    # This endpoint is for recent observations, which is what we need to append.
    url = f"https://api.ebird.org/v2/data/obs/loc/{loc_id}"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    params = {
        # The 'back' parameter specifies the number of days to go back.
        # Use a large number to get as much data as possible.
        "back": 999999,  
        "maxResults": 10000,
    }
    
    print(f"Fetching data for location {loc_id} with URL: {url} and params: {params}")
    
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
        
    for loc_id in HEADWATERS_LOCATIONS:
        try:
            new_data = fetch_ebird_data(loc_id)
            all_new_obs.extend(new_data)
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching data for location {loc_id}: {e}")
            
    if all_new_obs:
        new_df = pd.DataFrame(all_new_obs)
        new_df.drop_duplicates(subset=['subId']).to_parquet(EBIRD_DATA_FILE, index=False)
        print(f"Successfully created initial data file with {len(new_df)} observations.")
    else:
        print("No data was fetched. The data file was not created.")

if __name__ == "__main__":
    main()
