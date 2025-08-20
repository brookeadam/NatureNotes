import streamlit as st
import pandas as pd
import requests
import altair as alt
import datetime
from pathlib import Path
from dateutil.relativedelta import relativedelta

# === Constants ===
HEADWATERS_LOCATIONS = ["L1210588", "L1210849"]
LATITUDE = 29.4689
LONGITUDE = -98.4798
DATA_DIR = Path("data")
# Updated to use the CSV file
EBIRD_DATA_FILE = Path("historical_checklists.csv")

st.set_page_config(page_title="Nature Notes @ Headwaters", layout="wide")

# === API Fetch Functions (Only for live weather data) ===
@st.cache_data
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
            "temp_max": [
                (t * 9/5 + 32) if t is not None else None
                for t in data.get("daily", {}).get("temperature_2m_max", [])
            ],
            "temp_min": [
                (t * 9/5 + 32) if t is not None else None
                for t in data.get("daily", {}).get("temperature_2m_min", [])
            ],
            "precipitation": [
                (p * 0.0393701) if p is not None else None
                for p in data.get("daily", {}).get("precipitation_sum", [])
            ]
        })
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_ebird_data_from_file():
    if EBIRD_DATA_FILE.exists():
        # Updated to read from CSV with the correct encoding and to handle bad lines
        return pd.read_csv(EBIRD_DATA_FILE, encoding='cp1252', on_bad_lines='skip')
    else:
        st.warning("Ebird data file not found. Please check if the GitHub Action ran successfully.")
        return pd.DataFrame()

# === HEADER ===
st.markdown("<h1 style='text-align: center;'>🌳 Nature Notes: Headwaters at Incarnate Word 🌳</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: gray;'>Explore bird sightings and weather patterns side-by-side. Updated biweekly.</h4>", unsafe_allow_html=True)

# Define the minimum and maximum dates for filtering
MIN_DATE = datetime.date(1985, 1, 1)
MAX_DATE = datetime.date(2035, 12, 31)

# === Date Range Selection (Single, for main display) ===
st.subheader("🔎 Recent eBird Sightings 🔎")
st.subheader("⏱️ Filter by Date Range ⏱️")

main_start_date = st.date_input("Start Date", key="main_start", min_value=MIN_DATE, max_value=MAX_DATE)
main_end_date = st.date_input("End Date", key="main_end", min_value=MIN_DATE, max_value=MAX_DATE)

# === Load Data from File ===
weather_df = fetch_weather_data(LATITUDE, LONGITUDE, main_start_date, main_end_date)
ebird_df = load_ebird_data_from_file()

# === Data Cleaning & Preprocessing ===
if not ebird_df.empty:
    # Renamed to match the CSV column headers
    merged_df = ebird_df.rename(columns={
        "COMMON NAME": "Species",
        "SCIENTIFIC NAME": "Scientific Name",
        "OBSERVATION COUNT": "Count",
        "OBSERVATION DATE": "Date"
    })
    # Convert 'Count' column to numeric, replacing errors with NaN
    merged_df["Count"] = pd.to_numeric(merged_df["Count"], errors='coerce').fillna(0).astype(int)
    merged_df["Date"] = pd.to_datetime(merged_df["Date"])
else:
    merged_df = pd.DataFrame(columns=["Species", "Scientific Name", "Count", "Date"])

# === Display Recent eBird Sightings ===
if not merged_df.empty:
    # Filter ebird_df for the date range selected by the user
    filtered_ebird_df = merged_df[(merged_df["Date"] >= pd.to_datetime(main_start_date)) &
                                 (merged_df["Date"] <= pd
