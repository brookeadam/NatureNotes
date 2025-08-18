import os
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime

# === Constants ===
# Use a single locality ID
HEADWATERS_LOCATIONS = ["L1210588"]
DATA_DIR = Path("data")
EBIRD_DATA_FILE = DATA_DIR / "ebird_data.parquet"
EBIRD_API_KEY = os.environ.get("EBIRD_API_KEY")

def fetch_ebird_data(loc_id, start_date):
    """Fetches eBird data from the specified start date up to today."""
    url = f"https://api.ebird.org/v2/data/obs/{loc_id}/historic/"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    params = {
        "startDate": start_date.strftime("%Y-%m-%d"),
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
    
    # # For the first run, pull ALL historical data from a more reasonable date
    start_date = datetime(2000, 1, 1).date()
    print("Fetching ALL historical data from 2000...")
        
    all_new_obs = []
    
    for loc_id in HEADWATERS_LOCATIONS:
        try:
            new_data = fetch_ebird_data(loc_id, start_date)
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
