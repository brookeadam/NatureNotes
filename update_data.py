import os
import pandas as pd
import requests
import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path

# --- Constants ---
# Make sure to set this as a GitHub Secret, not hardcoded!
EBIRD_API_KEY = os.environ.get("EBIRD_API_KEY") 
HEADWATERS_LOCATIONS = ["L1210588", "L1210849"]
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = DATA_DIR / "ebird_data.parquet"

# === API Fetch: eBird ===
def fetch_ebird_data(loc_id, date):
    url = f"https://api.ebird.org/v2/data/obs/{loc_id}/historic/{date.strftime('%Y/%m/%d')}"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    return pd.DataFrame()

def load_all_ebird_data(start_date, end_date):
    dfs = []
    date_range = pd.date_range(start_date, end_date)
    for loc in HEADWATERS_LOCATIONS:
        for date in date_range:
            df = fetch_ebird_data(loc, date)
            if not df.empty:
                dfs.append(df)
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

if __name__ == "__main__":
    # Define a date range to fetch data.
    # We'll fetch data for the last 14 days, as per your "biweekly" requirement.
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=14)
    
    print(f"Fetching eBird data from {start_date} to {end_date}...")
    df = load_all_ebird_data(start_date, end_date)
    
    if not df.empty:
        # Load existing data if it exists
        if OUTPUT_FILE.exists():
            existing_df = pd.read_parquet(OUTPUT_FILE)
            # Remove duplicate observations and keep the newest ones
            combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=['subId'], keep='last')
            df = combined_df
        
        # Save the combined DataFrame to a file. Parquet is efficient.
        df.to_parquet(OUTPUT_FILE)
        print(f"Successfully saved {len(df)} observations to {OUTPUT_FILE}")
    else:
        print("No new eBird data was fetched.")
