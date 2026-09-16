import streamlit as st
import pandas as pd
import requests
import altair as alt
import datetime
import re
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

        # Read raw file as ONE column
        raw = pd.read_csv(EBIRD_DATA_FILE, header=None, names=["raw"], engine="python")

        rows = []
        pattern = re.compile(
            r"^(?P<GUID>\S+)\s+"
            r"(?P<Species>[A-Za-z'\- ]+?)\s+"
            r"(?P<Sci>[A-Za-z'\- ]+?)\s+"
            r"(?P<Count>\d+)\s+"
            r"(?P<Location>L\d+)\s+"
            r"(?P<Date>\d{1,2}/\d{1,2}/\d{4})\s+"
            r"(?P<Time>\d{1,2}:\d{2}:\d{2}\s+[AP]M)\s+"
            r"(?P<Observer>\S+)\s+"
            r"(?P<Protocol>\S+)\s+"
            r"(?P<Duration>\d+)\s+"
            r"(?P<Distance>\d+)\s+"
            r"(?P<NumObs>\d+)"
        )

        for line in raw["raw"]:
            m = pattern.match(line)
            if m:
                rows.append(m.groupdict())

        df = pd.DataFrame(rows)

        # Parse date + time
        df["Date"] = pd.to_datetime(df["Date"] + " " + df["Time"], errors="coerce")
        df["Count"] = pd.to_numeric(df["Count"], errors="coerce").fillna(0).astype(int)

        df = df.dropna(subset=["Date"])
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
                "Date": pd.to_datetime(data["daily"]["time"]).strftime("%Y-%m-%d"),
                "temp_max": [(t * 9/5 + 32) for t in data["daily"]["temperature_2m_max"]],
                "temp_min": [(t * 9/5 + 32) for t in data["daily"]["temperature_2m_min"]],
                "precipitation": [(p * 0.0393701) for p in data["daily"]["precipitation_sum"]]
            })
            return df
        except:
            return pd.DataFrame()

    # Load data
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
