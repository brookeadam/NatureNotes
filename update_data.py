import os
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime, timedelta

# === Constants ===
HEADWATERS_LOCATIONS = ["L1210588", "L1210849"]
DATA_DIR = Path("data")
EBIRD_DATA_FILE = DATA_DIR / "ebird_data.parquet"
EBIRD_API_KEY = os.environ.get("EBIRD_API_KEY")

def fetch_ebird_data(loc_id, start_date):
    """Fetches eBird data from the specified start date up to today."""
    url = f"https://api.ebird.org/v2/data/obs/{{loc_id}}/historic/"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    params = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "maxResults": 10000,
    }
    
    print(f"Fetching data for location {loc_id} with URL: {url.format(loc_id=loc_id)} and params: {params}")

    response = requests.get(url.format(loc_id=loc_id), headers=headers, params=params)
    response.raise_for_status()  # This will raise an exception for bad status codes
    return response.json()

def main():
    if not EBIRD_API_KEY:
        raise ValueError("EBIRD_API_KEY not found in environment variables.")
        
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(exist_ok=True)
    
    # Load existing data or create an empty DataFrame
    if EBIRD_DATA_FILE.exists():
        existing_df = pd.read_parquet(EBIRD_DATA_FILE)
        # Determine the last date in the existing data
        last_obs_date = pd.to_datetime(existing_df['obsDt']).max().date()
        # Set the API start date to the day after the last observation
        start_date = last_obs_date + timedelta(days=1)
        print("Existing data found. Updating from last observation date.")
    else:
        existing_df = pd.DataFrame()
        # For the first run, pull ALL historical data from a very early date
        start_date = datetime(1900, 1, 1).date()
        print("No existing data found. Fetching ALL historical data.")
        
    all_new_obs = []
    print(f"Fetching eBird data from {start_date} to today...")
    
    for loc_id in HEADWATERS_LOCATIONS:
        try:
            new_data = fetch_ebird_data(loc_id, start_date)
            all_new_obs.extend(new_data)
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching data for location {loc_id}: {e}")
            
    if all_new_obs:
        new_df = pd.DataFrame(all_new_obs)
        combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['subId']).reset_index(drop=True)
        combined_df.to_parquet(EBIRD_DATA_FILE, index=False)
        print(f"Successfully updated data with {len(new_df)} new observations.")
    else:
        print("No new data to add.")

if __name__ == "__main__":
    main()
