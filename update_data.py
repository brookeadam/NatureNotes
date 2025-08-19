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

def fetch_ebird_data_in_chunks(region_id, start_date):
    """Fetches historical eBird data for a region year by year."""
    all_data = []
    
    current_year = datetime.now().year
    start_year = start_date.year

    for year in range(start_year, current_year + 1):
        chunk_start_date = max(datetime(year, 1, 1).date(), start_date)
        chunk_end_date = datetime(year, 12, 31).date()

        url = f"https://api.ebird.org/v2/data/obs/{region_id}/historic"
        headers = {"X-eBirdApiToken": EBIRD_API_KEY}
        params = {
            "startDate": chunk_start_date.strftime("%Y-%m-%d"),
            "endDate": chunk_end_date.strftime("%Y-%m-%d"),
            "maxResults": 10000,
        }
        
        print(f"Fetching data for region {region_id} for year {year}...")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            all_data.extend(response.json())
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching data for year {year}: {e}")
            continue
            
    return all_data

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
        
    print(f"Fetching eBird data from {start_date} to today...")
    
    all_new_obs = fetch_ebird_data_in_chunks(EBIRD_REGION_CODE, start_date)
        
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
