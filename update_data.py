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

def fetch_ebird_data_in_chunks(region_id, start_year):
    """Fetches historical eBird data for a region year by year."""
    all_data = []
    current_year = datetime.now().year
    
    for year in range(start_year, current_year + 1):
        start_date = datetime(year, 1, 1).strftime("%Y-%m-%d")
        end_date = datetime(year, 12, 31).strftime("%Y-%m-%d")
        
        url = f"https://api.ebird.org/v2/data/obs/{region_id}/historic"
        headers = {"X-eBirdApiToken": EBIRD_API_KEY}
        params = {
            "startDate": start_date,
            "endDate": end_date,
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
        
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(exist_ok=True)
    
    # Check if the data file exists to determine if this is the first run
    if EBIRD_DATA_FILE.exists():
        existing_df = pd.read_parquet(EBIRD_DATA_FILE)
        print("Existing data found. No updates will be made on this run.")
        print("This script is designed for the initial historical pull only.")
        return
    else:
        print("No existing data found. Fetching ALL historical data.")
        
    all_new_obs = fetch_ebird_data_in_chunks(EBIRD_REGION_CODE, start_year=2000)
        
    if all_new_obs:
        new_df = pd.DataFrame(all_new_obs)
        
        # Filter the data to include only your specific locations
        filtered_df = new_df[new_df['locId'].isin(HEADWATERS_LOCATIONS)]
        
        filtered_df.drop_duplicates(subset=['subId']).to_parquet(EBIRD_DATA_FILE, index=False)
        print(f"Successfully created initial data file with {len(filtered_df)} observations.")
    else:
        print("No data was fetched. The data file was not created.")

if __name__ == "__main__":
    main()
    
