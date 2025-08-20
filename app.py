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
        # Corrected syntax by adding the missing single quote
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
                                 (merged_df["Date"] <= pd.to_datetime(main_end_date))]
    
    if not filtered_ebird_df.empty:
        filtered_ebird_df = filtered_ebird_df.sort_values("Date", ascending=False).copy()
        filtered_ebird_df["Date"] = filtered_ebird_df["Date"].dt.strftime("%Y-%m-%d")
        
        table_df = filtered_ebird_df[["Species", "Scientific Name", "Count", "Date"]].rename(columns={
            "Species": "COMMON NAME",
            "Scientific Name": "SCIENTIFIC NAME",
            "Count": "OBSERVATION COUNT",
            "Date": "OBSERVATION DATE",
        })
        
        styled_table = table_df.style.set_properties(**{'text-align': 'left'})
        st.dataframe(styled_table, use_container_width=True)
    else:
        st.warning("No recent observations available for the selected date range.")
else:
    st.warning("Ebird data file not found. Please check if the GitHub Action ran successfully.")

# === Weather Metrics ===
st.subheader("🌡️ Weather Metrics 🌡️")
weather_filtered = weather_df.copy()
weather_filtered["Date"] = pd.to_datetime(weather_filtered["Date"])
weather_filtered = weather_filtered.dropna(subset=["temp_max", "temp_min"])

if not weather_filtered.empty:
    col1, col2 = st.columns(2)
    with col1:
        max_temp_row = weather_filtered.loc[weather_filtered["temp_max"].idxmax()]
        max_temp = max_temp_row["temp_max"]
        max_temp_date = max_temp_row["Date"]
        st.metric(label=f"Max Temp (F) on {max_temp_date.date()}", value=f"{max_temp:.1f}")
    with col2:
        min_temp_row = weather_filtered.loc[weather_filtered["temp_min"].idxmin()]
        min_temp = min_temp_row["temp_min"]
        min_temp_date = min_temp_row["Date"]
        st.metric(label=f"Min Temp (F) on {min_temp_date.date()}", value=f"{min_temp:.1f}")
        
    st.subheader("Daily Weather Data")
    # Create a copy of the dataframe for display to avoid SettingWithCopyWarning
    display_weather_df = weather_filtered.copy()
    
    # Format the 'Date' column as YYYY-MM-DD string
    display_weather_df["Date"] = display_weather_df["Date"].dt.strftime("%Y-%m-%d")
    
    # Rename the columns for display
    display_weather_df = display_weather_df.rename(columns={
        "temp_max": "Max Temp °F",
        "temp_min": "Min Temp °F",
        "precipitation": "Total Precip in"
    })
    
    # Add index=False to hide the index column
    st.dataframe(display_weather_df, use_container_width=True)
else:
    st.warning("No weather data available for the selected date range.")
    
# === Species Count Comparison ==
st.subheader("📊 Species Comparison by Date Range 📊")

col1, col2 = st.columns(2)
with col1:
    range1_start = st.date_input("Range 1 Start", key="range1_start", min_value=MIN_DATE, max_value=MAX_DATE)
    range1_end = st.date_input("Range 1 End", key="range1_end", min_value=MIN_DATE, max_value=MAX_DATE)
with col2:
    range2_start = st.date_input("Range 2 Start", key="range2_start", min_value=MIN_DATE, max_value=MAX_DATE)
    range2_end = st.date_input("Range 2 End", key="range2_end", min_value=MIN_DATE, max_value=MAX_DATE)

if st.button("Compare Species and Weather"):
    # Filter bird data
    # This filters the complete 'merged_df' loaded from the .csv file
    range_a_birds = merged_df[
        (merged_df["Date"] >= pd.to_datetime(range1_start)) &
        (merged_df["Date"] <= pd.to_datetime(range1_end))
    ]
    range_b_birds = merged_df[
        (merged_df["Date"] >=)
