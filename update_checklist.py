import os
import requests
import pandas as pd
from datetime import datetime

# Define your locations
LOCATIONS = ["L1210588", "L1210849"]
EBIRD_API_KEY = os.environ["EBIRD_API_KEY"]
CSV_FILENAME = "historical_checklists.csv"

def fetch_ebird_checklists(loc_id, back_days=30):
    url = f"https://api.ebird.org/v2/product/obs/{loc_id}/historic"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    params = {"back": back_days}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def process_checklists(data, loc_id):
    processed = []
    for obs in data:
        processed.append({
            "speciesCode": obs.get("speciesCode"),
            "comName": obs.get("comName"),
            "sciName": obs.get("sciName"),
            "obsDt": obs.get("obsDt"),
            "howMany": obs.get("howMany"),
            "locId": loc_id,
            "locName": obs.get("locName"),
            "obsValid": obs.get("obsValid"),
            "obsReviewed": obs.get("obsReviewed"),
            "locationPrivate": obs.get("locationPrivate"),
            "subId": obs.get("subId")
        })
    return pd.DataFrame(processed)

def load_existing_data(csv_path):
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path, dtype=str)
    return pd.DataFrame()

def save_updated_data(df, csv_path):
    df.to_csv(csv_path, index=False)

def main():
    print("Fetching and updating checklists...")

    all_new_data = []

    for loc_id in LOCATIONS:
        try:
            print(f"Fetching data for {loc_id}...")
            raw_data = fetch_ebird_checklists(loc_id)
            df = process_checklists(raw_data, loc_id)
            all_new_data.append(df)
        except Exception as e:
            print(f"Failed to fetch data for {loc_id}: {e}")

    if all_new_data:
        new_data = pd.concat(all_new_data, ignore_index=True)
        new_data.drop_duplicates(subset=["subId", "speciesCode"], inplace=True)

        print("Loading existing data...")
        existing_data = load_existing_data(CSV_FILENAME)

        combined = pd.concat([existing_data, new_data], ignore_index=True)
        combined.drop_duplicates(subset=["subId", "speciesCode"], inplace=True)

        print(f"Saving updated data to {CSV_FILENAME}...")
        save_updated_data(combined, CSV_FILENAME)
        print("Checklist update complete.")
    else:
        print("No new data to add.")

if __name__ == "__main__":
    main()
