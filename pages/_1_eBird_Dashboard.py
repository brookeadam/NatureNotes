import streamlit as st
import pandas as pd
import requests
import datetime
from pathlib import Path

def main():
    EBIRD_DATA_FILE = Path("historical_checklists.csv")
    LATITUDE = 29.4689
    LONGITUDE = -98.4798

    @st.cache_data
    def load_ebird_data_from_file():
        if not EBIRD_DATA_FILE.exists():
            st.error("CSV file not found.")
            return pd.DataFrame()

        rows = []

        with open(EBIRD_DATA_FILE, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.strip().split()

                # Skip empty lines
                if len(parts) < 12:
                    continue

                # GUID is always first
                guid = parts[0]

                # Count is always the first integer after scientific name
                # Location is always L#####
                # Date is always M/D/YYYY
                # Time is always H:MM:SS AM/PM

                # Find the index of Count (first pure integer)
                count_idx = None
                for i in range(1, len(parts)):
                    if parts[i].isdigit():
                        count_idx = i
                        break

                if count_idx is None:
                    continue

                # Species = words between GUID and scientific name
                # Scientific name = two words before Count
                sci_name = parts[count_idx - 2] + " " + parts[count_idx - 1]

                species = " ".join(parts[1:count_idx - 2])

                count = int(parts[count_idx])

                # Location is next
                location = parts[count_idx + 1]

                # Date and Time
                date = parts[count_idx + 2]
                time = parts[count_idx + 3] + " " + parts[count_idx + 4]

                # Observer, Protocol, Duration, Distance, NumObservers
                observer = parts[count_idx + 5]
                protocol = parts[count_idx + 6]
                duration = parts[count_idx + 7]
                distance = parts[count_idx + 8]
                numobs = parts[count_idx + 9]

                rows.append({
                    "GUID": guid,
                    "Species": species,
                    "Scientific Name": sci_name,
                    "Count": count,
                    "Location": location,
                    "Date": date,
                    "Time": time,
                    "Observer": observer,
                    "Protocol": protocol,
                    "Duration": duration,
                    "Distance": distance,
                    "NumObservers": numobs
                })

        df = pd.DataFrame(rows)

        # Parse datetime
        df["Date"] = pd.to_datetime(df["Date"] + " " + df["Time"], errors="coerce")

        df = df.dropna(subset=["Date"])
        df["Count"] = pd.to_numeric(df["Count"], errors="coerce").fillna(0).astype(int)

        df = df.drop_duplicates(subset=["Date", "Species"], keep="first")

        return df

    @st.cache_data(ttl=3600)
    def fetch_weather_data(lat, lon, start, end):
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
            "timezone": "America/Chicago"
        }
        try:
            r = requests.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            df = pd.DataFrame({
                "Date": pd.to_datetime(data["daily"]["time"]).dt.strftime("%Y-%m-%d"),
                "temp_max": [(t * 9/5 + 32) for t in data["daily"]["temperature_2m_max"]],
                "temp_min": [(t * 9/5 + 32) for t in data["daily"]["temperature_2m_min"]],
                "precipitation": [(p * 0.0393701) for p in data["daily"]["precipitation_sum"]]
            })
            return df
        except:
            return pd.DataFrame()

    df = load_ebird_data_from_file()

    if df.empty:
        st.error("No valid eBird data found.")
        return

    # Latest checklist
    latest_date = df["Date"].max()
    latest_df = df[df["Date"] == latest_date].copy()
    latest_df["Date"] = latest_df["Date"].dt.strftime("%Y-%m-%d")

    st.subheader("Latest Checklist")
    st.write(f"Date: {latest_date.strftime('%Y-%m-%d')}")
    st.dataframe(latest_df[["Species", "Scientific Name", "Count"]], hide_index=True)

    # Weather
    weather = fetch_weather_data(LATITUDE, LONGITUDE, latest_date.date(), latest_date.date())
    if not weather.empty:
        st.subheader("Weather")
        st.dataframe(weather, hide_index=True)

    # Filters
    st.subheader("Filter by Date Range")
    start = st.date_input("Start", latest_date.date() - datetime.timedelta(days=30))
    end = st.date_input("End", latest_date.date())

    filtered = df[(df["Date"] >= pd.to_datetime(start)) & (df["Date"] <= pd.to_datetime(end))].copy()
    filtered["Date"] = filtered["Date"].dt.strftime("%Y-%m-%d")
    st.dataframe(filtered, hide_index=True)

if __name__ == "__main__":
    main()
