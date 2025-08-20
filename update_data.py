import os
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime, timedelta

# === Constants ===
HEADWATERS_LOCATIONS = ["L1210588"]
# The file is in the main branch
DATA_FILE = Path("historical_checklists.csv") 

def fetch_new_data(loc_id, start_date, end_date):
    """
    Fetches new eBird data for a location.
    NOTE: This function requires an eBird API key.
    If an API key is not provided, this function will not run.
    """
    ebird_api_key = os.environ.get("EBIRD_API_KEY")
    if not ebird_api_key:
        print("Warning: EBIRD_API_KEY is not set. Skipping API data fetch.")
        return []
    
    url = f"https://api.ebird.org/v2/data/obs/loc/{loc_id}/historic"
    headers = {"X-eBirdApiToken": ebird_api_key}
    params = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
    }
    
    print(f"Fetching new data for location {loc_id} from {start_date} to {end_date}...")
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 403:
        raise requests.exceptions.HTTPError("403 Forbidden: Invalid or expired API key. Please check your EBIRD_API_KEY secret.")
    
    response.raise_for_status()
    return response.json()

def main():
    if not DATA_FILE.exists():
        print("Historical data file not found. Please ensure historical_checklists.csv is in the main branch.")
        return 
        
    existing_df = pd.read_csv(DATA_FILE, encoding='cp1252', on_bad_lines='skip')
    print("Columns in your file:", existing_df.columns.tolist())
    
    last_obs_date = pd.to_datetime(existing_df['OBSERVATION DATE']).max().date()
    start_date = last_obs_date + timedelta(days=1)
    end_date = datetime.now().date()
    print(f"Existing data found. Updating from last observation date: {start_date}")
        
    all_new_obs = []
    
    for loc_id in HEADWATERS_LOCATIONS:
        try:
            new_data = fetch_new_data(loc_id, start_date, end_date)
            all_new_obs.extend(new_data)
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching new data for location {loc_id}: {e}")
            
    if all_new_obs:
        new_df = pd.DataFrame(all_new_obs)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates(subset=['subId']).reset_index(drop=True)
        combined_df.to_csv(DATA_FILE, index=False)
        print(f"Successfully updated data with {len(new_df)} new observations.")
    else:
        print("No new data to add.")

if __name__ == "__main__":
    main()
