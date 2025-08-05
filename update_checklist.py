import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables (make sure you add EBIRD_API_KEY to GitHub Secrets)
load_dotenv()

EBIRD_API_KEY = os.getenv("EBIRD_API_KEY")
CSV_FILE = "historical_checklists.csv"

# Headwaters at Incarnate Word location IDs
LOCATION_IDS = ["L1210588", "L1210849"]

# Function to fetch recent checklists from a location
def fetch_checklists(loc_id):
    url = f"https://api.ebird.org/v2/data/obs/{loc_id}/historic"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data for {loc_id}: {response.status_code}")
        return []

# Load existing historical data with encoding fallback
try:
    df_old = pd.read_csv(CSV_FILE)
except UnicodeDecodeError:
    df_old = pd.read_csv(CSV_FILE, encoding="ISO-8859-1")

# Fetch new checklists for both locations
all_obs = []
for loc in LOCATION_IDS:
    obs = fetch_checklists(loc)
    all_obs.extend(obs)

# Convert to DataFrame
df_new = pd.DataFrame(all_obs)

# If empty, avoid crashing
if df_new.empty:
    print("No new observations found.")
else:
    # Normalize date format
    df_new["obsDt"] = pd.to_datetime(df_new["obsDt"], errors="coerce")
    df_old["obsDt"] = pd.to_datetime(df_old["obsDt"], errors="coerce")

    # Merge and remove duplicates by unique obsID (or checklist ID if available)
    combined = pd.concat([df_old, df_new], ignore_index=True)
    if "obsId" in combined.columns:
        combined.drop_duplicates(subset="obsId", inplace=True)
    elif "subId" in combined.columns:
        combined.drop_duplicates(subset="subId", inplace=True)

    # Save updated file
    combined.to_csv(CSV_FILE, index=False, encoding="utf-8")
    print("Checklist successfully updated and saved.")
