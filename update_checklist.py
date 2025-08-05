import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path

# === CONFIGURATION ===
EBIRD_API_KEY = "c49o0js5vkjb"
LOC_IDS = ["L1210588", "L1210849"]
CSV_FILE = "historical_checklists.csv"
DAYS_LOOKBACK = 7  # Fetch data from the last week

headers = {"X-eBirdApiToken": EBIRD_API_KEY}
new_rows = []

for loc_id in LOC_IDS:
    url = f"https://api.ebird.org/v2/data/obs/{loc_id}/recent?back={DAYS_LOOKBACK}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        for obs in data:
            new_rows.append({
                "speciesCode": obs.get("speciesCode"),
                "comName": obs.get("comName"),
                "sciName": obs.get("sciName"),
                "locId": obs.get("locId"),
                "locName": obs.get("locName"),
                "obsDt": obs.get("obsDt"),
                "howMany": obs.get("howMany"),
                "lat": obs.get("lat"),
                "lng": obs.get("lng"),
                "obsValid": obs.get("obsValid"),
                "obsReviewed": obs.get("obsReviewed"),
                "locationPrivate": obs.get("locationPrivate"),
                "subId": obs.get("subId")
            })
    else:
        print(f"Failed to fetch data for {loc_id}: {response.status_code}")

# Load historical data
df_old = pd.read_csv(CSV_FILE, encoding='ISO-8859-1')

# Create new DataFrame and ensure obsDt is parsed
df_new = pd.DataFrame(new_rows)
df_new["obsDt"] = pd.to_datetime(df_new["obsDt"])
df_old["obsDt"] = pd.to_datetime(df_old["obsDt"])

# Only keep truly new rows (not duplicates)
df_combined = pd.concat([df_old, df_new]).drop_duplicates(subset=["subId"]).sort_values(by="obsDt")

# Save updated CSV
df_combined.to_csv(CSV_FILE, index=False)
print("✅ Checklist data updated.")
