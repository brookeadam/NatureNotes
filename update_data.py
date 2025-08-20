import os
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime, timedelta

# === Constants ===
HEADWATERS_LOCATIONS = ["L1210588"]
DATA_DIR = Path("data")
EBIRD_DATA_FILE = DATA_DIR / "ebird_data.parquet"
EBIRD_API_KEY = os.environ.get("EBIRD_API_KEY")

def fetch_ebird_data_paginated(loc_id):
    """Fetches all eBird data for a location using a paginated approach."""
    all_data = []
    
    # We will fetch data in 30-day chunks until we run out of new records.
    # The API will tell us when there's no more data by returning an empty list.
    chunk_size = 30
    
    print(f"Fetching data for location {loc_id} in {chunk_size}-day chunks...")

    while True:
        url = f"https://api.ebird.org/v2/data/obs/loc/{loc_id}"
        headers = {"X-eBirdApiToken": EBIRD_API_KEY}
        params = {
            "back": chunk_size,
        }
        
        # We need to add a parameter to handle pagination, we will use a date.
        # This parameter will change with each API call.
        if all_data:
            last_date = pd.to_datetime([d['obsDt'] for d in all_data]).min().date()
            params['startDate'] = (last_date - timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            chunk_data = response.json()
            
            if not chunk_data:
                break # No more data to fetch

            all_data.extend(chunk_data)
            print(f"Fetched {len(chunk_data)} records. Total: {len(all_data)}")
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching data for chunk: {e}")
            break
            
    return all_data

def main():
    if not EBIRD_API_KEY:
        raise ValueError("EBIRD_API_KEY not found in environment variables.")
        
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(exist_ok=True)
    
    all_new_obs = []
    
    for loc_id in HEADWATERS_LOCATIONS:
        print("Fetching ALL historical data for location...")
        new_data = fetch_ebird_data_paginated(loc_id)
        all_new_obs.extend(new_data)
            
    if all_new_obs:
        new_df = pd.DataFrame(all_new_obs)
        new_df.drop_duplicates(subset=['subId']).to_parquet(EBIRD_DATA_FILE, index=False)
        print(f"Successfully created initial data file with {len(new_df)} observations.")
    else:
        print("No data was fetched. The data file was not created.")

if __name__ == "__main__":
    main()
    
