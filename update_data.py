import os
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime, timedelta

# === Constants ===
HEADWATERS_LOCATIONS = ["L1210588"]
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "historical_checklists.csv"
EBIRD_API_KEY = os.environ.get("EBIRD_API_KEY")

def fetch_new_data(loc_id, start_date):
    """Fetches new eBird data for a location from a specific start date to today."""
    
    url = f"https://api.ebird.org/v2/data/obs/loc/{loc_id}/recent"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    params = {
        "startDate": start_date.strftime("%Y-%m-%d"),
    }
    
    print(f"Fetching new data for location {loc_id} from {start_date} to today...")
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def main():
    if not EBIRD_API_KEY:
        raise ValueError("EBIRD_API_KEY not found in environment variables.")
        
    DATA_DIR.mkdir(exist_ok=True)
    
    if DATA_FILE.exists():
        existing_df = pd.read_csv(DATA_FILE)
        last_obs_date = pd.to_datetime(existing_df['obsDt']).max().date()
        start_date = last_obs_date + timedelta(days=1)
        print(f"Existing data found. Updating from last observation date: {start_date}")
    else:
        print("Historical data file not found. Please upload it as historical_checklists.csv.")
        return # Exit if file is not present
        
    all_new_obs = []
    
    for loc_id in HEADWATERS_LOCATIONS:
        try:
            new_data = fetch_new_data(loc_id, start_date)
            all_new_obs.extend(new_data)
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching new data for location {loc_id}: {e}")
            
    if all_new_obs:
        new_df = pd.DataFrame(all_new_obs)
        combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['subId']).reset_index(drop=True)
        combined_df.to_csv(DATA_FILE, index=False)
        print(f"Successfully updated data with {len(new_df)} new observations.")
    else:
        print("No new data to add.")

if __name__ == "__main__":
    main()
    
