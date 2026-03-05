import streamlit as st
import pandas as pd
import requests
import altair as alt
import datetime
from pathlib import Path
from dateutil.relativedelta import relativedelta

def main():
    # === Constants ===
    HEADWATERS_LOCATIONS = ["L1210588", "L1210849"]
    LATITUDE = 29.4689
    LONGITUDE = -98.4798
    DATA_DIR = Path("data")
    EBIRD_DATA_FILE = Path("historical_checklists.csv")
    
    # === API Fetch Functions ===
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
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return pd.DataFrame({
                "Date": pd.to_datetime(data.get("daily", {}).get("time", [])),
                "temp_max": [(t * 9/5 + 32) if t is not None else None for t in data.get("daily", {}).get("temperature_2m_max", [])],
                "temp_min": [(t * 9/5 + 32) if t is not None else None for t in data.get("daily", {}).get("temperature_2m_min", [])],
                "precipitation": [(p * 0.0393701) if p is not None else None for p in data.get("daily", {}).get("precipitation_sum", [])]
            })
        except Exception as e:
            st.error(f"Error fetching weather data: {e}")
            return pd.DataFrame(columns=["Date", "temp_max", "temp_min", "precipitation"])
    
    @st.cache_data
    def load_ebird_data_from_file():
        if EBIRD_DATA_FILE.exists():
            df = pd.read_csv(EBIRD_DATA_FILE, sep=None, engine="python", encoding="cp1252", on_bad_lines="skip")
            return clean_ebird_data(df)
        else:
            st.warning("eBird data file not found.")
            return pd.DataFrame()
    
    @st.cache_data
    def clean_ebird_data(df):
        if df.empty: return df
        if len(df.columns) == 1 and "\t" in df.columns[0]:
            df = df.iloc[:, 0].str.split("\t", expand=True)
            df.columns = [c.strip() for c in df.iloc[0]]
            df = df.iloc[1:].reset_index(drop=True)
        df.columns = [c.strip().upper() for c in df.columns]
        column_map = {
            "SPECIES": ["COMMON NAME", "SPECIES"],
            "SCIENTIFIC NAME": ["SCIENTIFIC NAME"],
            "COUNT": ["COUNT", "OBSERVATION COUNT", "HOW MANY", "NUMBER OBSERVED"],
            "DATE": ["OBSERVATION DATE", "DATE"],
            "TIME": ["TIME OBSERVATIONS STARTED", "TIME"]
        }
        resolved = {}
        for key, options in column_map.items():
            for opt in options:
                if opt in df.columns:
                    resolved[key] = opt
                    break
        if len(resolved) < 5: return pd.DataFrame()
        df_cleaned = pd.DataFrame({
            "Species": df[resolved["SPECIES"]],
            "Scientific Name": df[resolved["SCIENTIFIC NAME"]],
            "Date": pd.to_datetime(df[resolved["DATE"]], errors="coerce"),
            "Time": df[resolved["TIME"]],
            "Count": pd.to_numeric(df[resolved["COUNT"]], errors="coerce").fillna(0).astype(int)
        })
        return df_cleaned.dropna(subset=["Date"])
    
    # === HEADER ===
    st.markdown("<h1 style='text-align: center;'>🌳 Nature Notes: Headwaters at Incarnate Word 🌳</h1>", unsafe_allow_html=True)
    
    # === Data Loading ===
    MIN_DATE = datetime.date(1985, 1, 1)
    MAX_DATE = datetime.date(2035, 12, 31)
    ebird_df = load_ebird_data_from_file()
    
    if ebird_df.empty:
        st.error("No eBird data found.")
        return

    # === Latest Checklist ===
    st.subheader("🆕 Latest Checklist 🆕")
    latest_date = ebird_df["Date"].max()
    latest_df = ebird_df[ebird_df["Date"] == latest_date].copy()
    st.write(f"**Checklist from:** {latest_date.strftime('%Y-%m-%d')}")
    st.dataframe(latest_df[["Species", "Scientific Name", "Count"]], use_container_width=True, hide_index=True)

    # === Weather ===
    weather_latest = fetch_weather_data(LATITUDE, LONGITUDE, latest_date.date(), latest_date.date())
    if not weather_latest.empty:
        st.subheader(f"Weather for {latest_date.date()}")
        st.dataframe(weather_latest, use_container_width=True, hide_index=True)

    # === Filtered View ===
    st.subheader("⏱️ Filter by Single Date Range ⏱️")
    d1 = st.date_input("Start Date", latest_date - datetime.timedelta(days=30))
    d2 = st.date_input("End Date", latest_date)
    
    filtered = ebird_df[(ebird_df["Date"] >= pd.to_datetime(d1)) & (ebird_df["Date"] <= pd.to_datetime(d2))]
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    # === Footer ===
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray;'>Nature Notes • Developed with ❤️ by Brooke 🌿</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
