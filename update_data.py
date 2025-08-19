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

def fetch_all_historical_data(region_id):
    """Fetches all historical eBird data for a region using a single API call."""
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
        
    DATA_DIR.mkdir(exist_ok=True)
    
    if EBIRD_DATA_FILE.exists():
        existing_df = pd.read_parquet(EBIRD_DATA_FILE)
        last_obs_date = pd.to_datetime(existing_df['obsDt']).max().date()
        start_date = last_obs_date + timedelta(days=1)
        print("Existing data found. Updating from last observation date.")
    else:
        existing_df = pd.DataFrame()
        start_date = datetime(2000, 1, 1).date()
        print("No existing data found. Fetching ALL historical data from 2000.")
        
    all_new_obs = fetch_all_historical_data(EBIRD_REGION_CODE)
        
    if all_new_obs:
        new_df = pd.DataFrame(all_new_obs)
        
        filtered_df = new_df[new_df['locId'].isin(HEADWATERS_LOCATIONS)]
        
        combined_df = pd.concat([existing_df, filtered_df]).drop_duplicates(subset=['subId']).reset_index(drop=True)
        combined_df.to_parquet(EBIRD_DATA_FILE, index=False)
        print(f"Successfully updated data with {len(filtered_df)} new observations for your locations.")
    else:
        print("No new data to add.")

if __name__ == "__main__":
    main()
