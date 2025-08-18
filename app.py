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
EBIRD_DATA_FILE = DATA_DIR / "ebird_data.parquet"

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
        return pd.read_parquet(EBIRD_DATA_FILE)
    else:
        st.warning("Ebird data file not found. Please check if the GitHub Action ran successfully.")
        return pd.DataFrame()

# === HEADER ===
st.title("🌳 Nature Notes: Headwaters at Incarnate Word")
st.caption("Explore bird sightings and weather patterns side-by-side. Updated biweekly.")

# === Date Range Selection (Single, for main display) ===
st.subheader("🔎 Recent eBird Sightings")
st.subheader("⏱️ Filter by Date Range")
quick_range = st.radio("Select Range", ["Last 7 Days", "This Month", "Custom Range"], index=1, key="main_range")

if quick_range == "Last 7 Days":
    main_start_date = datetime.date.today() - datetime.timedelta(days=7)
    main_end_date = datetime.date.today()
elif quick_range == "This Month":
    today = datetime.date.today()
    main_start_date = today.replace(day=1)
    main_end_date = today
else:
    main_start_date = st.date_input("Start Date", key="main_start")
    main_end_date = st.date_input("End Date", key="main_end")

# === Load Data from File ===
weather_df = fetch_weather_data(LATITUDE, LONGITUDE, main_start_date, main_end_date)
ebird_df = load_ebird_data_from_file()

# === Data Cleaning & Preprocessing ===
if not ebird_df.empty:
    ebird_df["obsDt"] = pd.to_datetime(ebird_df["obsDt"])
    merged_df = ebird_df.rename(columns={
        "comName": "Species",
        "sciName": "Scientific Name",
        "howMany": "Count",
        "obsDt": "Date"
    })
else:
    merged_df = pd.DataFrame(columns=["Species", "Scientific Name", "Count", "Date"])

# === Display Recent eBird Sightings ===
if not ebird_df.empty:
    # Filter ebird_df for the date range selected by the user
    filtered_ebird_df = ebird_df[(ebird_df["obsDt"] >= pd.to_datetime(main_start_date)) & 
                                 (ebird_df["obsDt"] <= pd.to_datetime(main_end_date))]
    
    if not filtered_ebird_df.empty:
        filtered_ebird_df = filtered_ebird_df.sort_values("obsDt", ascending=False).copy()
        filtered_ebird_df["obsDt"] = filtered_ebird_df["obsDt"].dt.strftime("%Y-%m-%d")
        
        table_df = filtered_ebird_df[["comName", "sciName", "howMany", "obsDt"]].rename(columns={
            "comName": "COMMON NAME",
            "sciName": "SCIENTIFIC NAME",
            "howMany": "OBSERVATION COUNT",
            "obsDt": "OBSERVATION DATE",
        })
        
        styled_table = table_df.style.set_properties(**{'text-align': 'left'})
        st.dataframe(styled_table, use_container_width=True)
    else:
        st.warning("No recent observations available for the selected date range.")
else:
    st.warning("Ebird data file not found. Please check if the GitHub Action ran successfully.")

# === Weather Metrics ===
st.subheader("🌡️ Weather Metrics")
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
    
    st.dataframe(display_weather_df, use_container_width=True)
else:
    st.warning("No weather data available for the selected date range.")
    

# === Species Count Comparison ===
st.subheader("📊 Species Comparison by Date Range")

col1, col2 = st.columns(2)
with col1:
    range1_start = st.date_input("Range 1 Start", key="range1_start")
    range1_end = st.date_input("Range 1 End", key="range1_end")
with col2:
    range2_start = st.date_input("Range 2 Start", key="range2_start")
    range2_end = st.date_input("Range 2 End", key="range2_end")

if st.button("Compare Species and Weather"):
    # Filter bird data
    range_a_birds = merged_df[
        (merged_df["Date"] >= pd.to_datetime(range1_start)) &
        (merged_df["Date"] <= pd.to_datetime(range1_end))
    ]
    range_b_birds = merged_df[
        (merged_df["Date"] >= pd.to_datetime(range2_start)) &
        (merged_df["Date"] <= pd.to_datetime(range2_end))
    ]

    # Summary stats
    unique_species_a = range_a_birds["Species"].nunique()
    unique_species_b = range_b_birds["Species"].nunique()
    total_birds_a = range_a_birds["Count"].sum()
    total_birds_b = range_b_birds["Count"].sum()

    st.markdown("### 🔢 Bird Summary")
    st.write(f"**Range A ({range1_start}–{range1_end}):** {unique_species_a} unique species, {total_birds_a} total birds")
    st.write(f"**Range B ({range2_start}–{range2_end}):** {unique_species_b} unique species, {total_birds_b} total birds")
    
    # Species comparison table
    table_a = range_a_birds.groupby(["Species", "Scientific Name"])["Count"].sum().reset_index()
    table_b = range_b_birds.groupby(["Species", "Scientific Name"])["Count"].sum().reset_index()

    col_a = f"Birds ({range1_start}–{range1_end})"
    col_b = f"Birds ({range2_start}–{range2_end})"
    comparison_df = pd.merge(table_a.rename(columns={"Count": col_a}), 
                             table_b.rename(columns={"Count": col_b}), 
                             on=["Species", "Scientific Name"], how="outer").fillna(0)
    comparison_df["Difference"] = comparison_df[col_b] - comparison_df[col_a]

    st.markdown("### 🐦 Species Comparison Table")
    st.dataframe(comparison_df.style.set_properties(**{'text-align': 'left'}), use_container_width=True)

    # Weather comparison
    st.markdown("### 🌡️ Weather Trends (Detailed)")
    weather_range_a = weather_df[(weather_df["Date"] >= pd.to_datetime(range1_start)) & (weather_df["Date"] <= pd.to_datetime(range1_end))]
    weather_range_b = weather_df[(weather_df["Date"] >= pd.to_datetime(range2_start)) & (weather_df["Date"] <= pd.to_datetime(range2_end))]

if not weather_range_a.empty:
    st.write(f"**Weather Summary: Range A ({range1_start}–{range1_end})**")
    
    # Create a copy to avoid a SettingWithCopyWarning
    renamed_a = weather_range_a.copy()
    
    # Convert 'Date' column to YYYY-MM-DD string format
    renamed_a["Date"] = renamed_a["Date"].dt.strftime("%Y-%m-%d")
    
    renamed_a = renamed_a.rename(columns={
        "temp_max": "Max Temp °F",
        "temp_min": "Min Temp °F",
        "precipitation": "Total Precip in"
    })
    st.dataframe(renamed_a, use_container_width=True)
else:
    st.info("No weather data for Range A.")

if not weather_range_b.empty:
    st.write(f"**Weather Summary: Range B ({range2_start}–{range2_end})**")
    
    # Create a copy to avoid a SettingWithCopyWarning
    renamed_b = weather_range_b.copy()
    
    # Convert 'Date' column to YYYY-MM-DD string format
    renamed_b["Date"] = renamed_b["Date"].dt.strftime("%Y-%m-%d")
    
    renamed_b = renamed_b.rename(columns={
        "temp_max": "Max Temp °F",
        "temp_min": "Min Temp °F",
        "precipitation": "Total Precip in"
    })
    st.dataframe(renamed_b, use_container_width=True)
else:
    st.info("No weather data for Range B.")
    
# === Footer ===
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Nature Notes for Headwaters at Incarnate Word • Developed with ❤️ by Brooke Adam and Kraken Security Operations 🌿"
    "</div>",
    unsafe_allow_html=True
)
