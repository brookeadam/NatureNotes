import streamlit as st
import pandas as pd
import numpy as np
import requests
import base64
import os
import datetime
import plotly.express as px
from meteostat import Point, Daily
from io import StringIO
import chardet

# Paths
CHECKLIST_PATH = "historical_checklists.csv"
WEATHER_CACHE_PATH = "weather_data.csv"

# Constants
LAT, LON = 29.4658, -98.4665  # Headwaters coordinates
UPDATE_INTERVAL_DAYS = 3  # eBird checklist auto-update frequency

st.set_page_config(page_title="Nature Notes Dashboard", layout="wide")
st.markdown("""
<style>
body {
    background-color: #f5f5dc;
    color: #333;
}
[data-testid="stSidebar"] {
    background-color: #e6e6dc;
}
thead tr th {
    background-color: #dcdcdc !important;
    color: #2f2f2f !important;
}
</style>
""", unsafe_allow_html=True)

# Title and credits
st.title("📊 Nature Notes Dashboard")
st.caption("Headwaters at Incarnate Word")
st.caption("Built by Brooke Adam, Run by Kraken Security Operations")

# Load checklist with encoding detection
def load_checklist():
    with open(CHECKLIST_PATH, 'rb') as f:
        raw = f.read(4096)
        encoding = chardet.detect(raw)['encoding']
    df = pd.read_csv(CHECKLIST_PATH, encoding=encoding, parse_dates=["OBSERVATION DATE"])
    df["OBSERVATION DATE"] = pd.to_datetime(df["OBSERVATION DATE"])
    return df

# Fetch historical weather data
def get_weather_data(dates):
    if os.path.exists(WEATHER_CACHE_PATH):
        weather_df = pd.read_csv(WEATHER_CACHE_PATH, parse_dates=["date"])
    else:
        start = dates.min()
        end = dates.max()
        location = Point(LAT, LON)
        weather = Daily(location, start, end)
        weather_df = weather.fetch().reset_index()
        weather_df.to_csv(WEATHER_CACHE_PATH, index=False)
    return weather_df

# Remove duplicate observations by species/date/count
def deduplicate_data(df):
    return df.drop_duplicates(subset=["COMMON NAME", "OBSERVATION DATE", "OBSERVATION COUNT"])

# Merge bird + weather data
def merge_data(bird_df, weather_df):
    return pd.merge(
        bird_df,
        weather_df,
        left_on="OBSERVATION DATE",
        right_on="date",
        how="left"
    )

# Bird image from eBird CDN
def get_species_image(common_name):
    try:
        code = common_name.lower().replace(" ", "")[:6]  # crude species code
        return f"https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{code}/512"
    except:
        return ""

# Sidebar filters
st.sidebar.header("🔎 Filter Data")
view_mode = st.sidebar.selectbox("View Mode", ["Date Range", "Year-to-Date", "All-Time"])

bird_df = load_checklist()
bird_df = deduplicate_data(bird_df)

# Time filtering
now = pd.Timestamp.now()
if view_mode == "Date Range":
    date_range = st.sidebar.date_input("Select Date Range", [bird_df["OBSERVATION DATE"].min(), now])
    filtered_df = bird_df[(bird_df["OBSERVATION DATE"] >= pd.to_datetime(date_range[0])) &
                          (bird_df["OBSERVATION DATE"] <= pd.to_datetime(date_range[1]))]
elif view_mode == "Year-to-Date":
    ytd_start = pd.Timestamp(year=now.year, month=1, day=1)
    filtered_df = bird_df[bird_df["OBSERVATION DATE"] >= ytd_start]
else:
    filtered_df = bird_df.copy()

# Weather data
weather_df = get_weather_data(filtered_df["OBSERVATION DATE"])
merged_df = merge_data(filtered_df, weather_df)

# Side-by-side comparison tool
with st.expander("📊 Compare Two Timeframes"):
    col1, col2 = st.columns(2)
    with col1:
        timeframe1 = st.date_input("Start of Period A", now - pd.DateOffset(years=2))
        timeframe2 = st.date_input("End of Period A", now - pd.DateOffset(years=2) + pd.DateOffset(months=1))
    with col2:
        timeframe3 = st.date_input("Start of Period B", now - pd.DateOffset(years=0))
        timeframe4 = st.date_input("End of Period B", now - pd.DateOffset(years=0) + pd.DateOffset(months=1))

    period_a = merged_df[(merged_df["OBSERVATION DATE"] >= timeframe1) & (merged_df["OBSERVATION DATE"] <= timeframe2)]
    period_b = merged_df[(merged_df["OBSERVATION DATE"] >= timeframe3) & (merged_df["OBSERVATION DATE"] <= timeframe4)]

    st.subheader("Period A vs B: Species Count")
    col3, col4 = st.columns(2)
    col3.metric("🕊️ Period A", period_a["COMMON NAME"].nunique())
    col4.metric("🕊️ Period B", period_b["COMMON NAME"].nunique())

    st.subheader("📈 Avg Temp")
    col5, col6 = st.columns(2)
    col5.metric("🌡️ A Temp", round(period_a["tavg"].mean(), 1) if "tavg" in period_a else "N/A")
    col6.metric("🌡️ B Temp", round(period_b["tavg"].mean(), 1) if "tavg" in period_b else "N/A")

# Download options
st.download_button("⬇️ Download Filtered Data", filtered_df.to_csv(index=False).encode("utf-8"), file_name="filtered_birds.csv")

# Display table
st.subheader("📝 Recent Bird Observations")
display_df = merged_df[[
    "COMMON NAME", "SCIENTIFIC NAME", "OBSERVATION COUNT", "OBSERVATION DATE",
    "TIME OBSERVATIONS STARTED", "OBSERVER ID", "OBSERVER NAME", "DURATION MINUTES",
    "EFFORT DISTANCE KM", "NUMBER OBSERVERS", "COMMENTS"
]].sort_values(by="OBSERVATION DATE", ascending=False)

# Add thumbnail links
display_df["PHOTO"] = display_df["COMMON NAME"].apply(lambda x: f'<img src="{get_species_image(x)}" width="50">')

st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

st.markdown("---")
st.markdown("""<center>
<b>Built by Brooke Adam</b> | <i>Run by Kraken Security Operations</i>
</center>""", unsafe_allow_html=True)
