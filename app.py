import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import io
import zipfile
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from meteostat import Stations, Daily
from PIL import Image
from urllib.parse import quote
import base64
import chardet

# Constants
CHECKLIST_PATH = "data/historical_checklists.csv"
WEATHER_CACHE_PATH = "data/weather_cache.csv"
EBIRD_LOCATIONS = {
    "Headwaters UIW Trail": "L1210588",
    "Headwaters UIW Circle": "L1210849"
}

st.set_page_config(page_title="Nature Notes Dashboard", layout="wide")

# --- Sidebar Filters ---
st.sidebar.header("🔎 Filter Data")

view_mode = st.sidebar.radio("View Mode", ["📊 Nature Notes Dashboard", "📋 Raw Data Table"])

# --- Utility Functions ---
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def load_checklist():
    encoding = detect_encoding(CHECKLIST_PATH)
    df = pd.read_csv(CHECKLIST_PATH, encoding=encoding, parse_dates=["OBSERVATION DATE"])
    df = df[df['LOCATION ID'].isin(EBIRD_LOCATIONS.values())].copy()
    df['OBSERVATION DATE'] = pd.to_datetime(df['OBSERVATION DATE'])
    df['COMMON NAME'] = df['COMMON NAME'].str.title()
    df['SCIENTIFIC NAME'] = df['SCIENTIFIC NAME'].str.title()
    return df

def get_date_options(df):
    min_date = df['OBSERVATION DATE'].min()
    max_date = df['OBSERVATION DATE'].max()
    today = pd.Timestamp.today().normalize()
    return {
        "All Time": (min_date, max_date),
        "This Month": (today.replace(day=1), today),
        "Last 7 Days": (today - pd.Timedelta(days=6), today),
        "This Season (Est)": (today - pd.Timedelta(days=90), today)
    }

@st.cache_data(ttl=3600)
def get_weather_data(lat, lon, start, end):
    station = Stations().nearby(lat, lon).fetch(1)
    if station.empty:
        return pd.DataFrame()
    station_id = station.index[0]
    data = Daily(station_id, start, end)
    df = data.fetch()
    df.reset_index(inplace=True)
    return df

@st.cache_data(ttl=600)
def fetch_ebird_species_photo(species_name):
    encoded_name = quote(species_name)
    url = f"https://api.ebird.org/v2/ref/photo/{encoded_name}"
    headers = {"X-eBirdApiToken": os.getenv("EBIRD_API_KEY", "")}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("photoUrl")
    return None

# --- Load Data ---
bird_df = load_checklist()

# --- Sidebar Date Filter ---
date_options = get_date_options(bird_df)
default_range = date_options["Last 7 Days"]
selected_range_label = st.sidebar.selectbox("Select Timeframe", list(date_options.keys()))
start_date, end_date = date_options[selected_range_label]

filtered_df = bird_df[(bird_df['OBSERVATION DATE'] >= start_date) & (bird_df['OBSERVATION DATE'] <= end_date)]

# --- Main Content ---
st.title("📊 Nature Notes Dashboard")
st.subheader("Headwaters at Incarnate Word")
st.caption("Built by Brooke Adam, Run by Kraken Security Operations")

if view_mode == "📋 Raw Data Table":
    st.dataframe(filtered_df)
else:
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Unique Species Observed", filtered_df['COMMON NAME'].nunique())
        st.metric("Total Observations", filtered_df['COMMON NAME'].count())

    with col2:
        daily_counts = filtered_df.groupby("OBSERVATION DATE")["COMMON NAME"].nunique()
        st.line_chart(daily_counts, use_container_width=True)

    with st.expander("📷 Recent Observations with Photos"):
        recent_obs = filtered_df.sort_values("OBSERVATION DATE", ascending=False).drop_duplicates("COMMON NAME").head(10)
        for _, row in recent_obs.iterrows():
            cols = st.columns([1, 3])
            with cols[0]:
                st.markdown(f"**{row['COMMON NAME']}**")
                st.caption(row['SCIENTIFIC NAME'])
                st.caption(f"{row['OBSERVATION DATE'].date()} | {row['LOCATION']}")
            with cols[1]:
                photo_url = fetch_ebird_species_photo(row['COMMON NAME'])
                if photo_url:
                    st.image(photo_url, width=300)
                else:
                    st.text("[No image available]")

    with st.expander("🌦️ Weather Trends Comparison"):
        lat, lon = 29.4659, -98.4695
        weather_df = get_weather_data(lat, lon, start_date, end_date)
        if not weather_df.empty:
            st.line_chart(weather_df.set_index("time")["tavg"], use_container_width=True)
        else:
            st.warning("No weather data available for the selected range.")

# --- Footer ---
st.markdown("---")
st.markdown("**Headwaters at Incarnate Word**  ")
st.caption("A sanctuary for nature, science, and spirit in the heart of San Antonio.  ")
st.caption("© 2025 Nature Notes | Developed with ❤️ by Brooke Adam and Kraken Security Ops")
