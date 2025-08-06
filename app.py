import streamlit as st
import pandas as pd
import chardet
from datetime import datetime
from utils import (
    load_weather_data,
    filter_by_date_range,
    generate_weather_summary,
    generate_species_summary,
    compare_timeframes,
    fetch_recent_ebird_observations,
    display_species_photos,
)

st.set_page_config(page_title="Nature Notes Dashboard", layout="wide")

# Constants
CHECKLIST_PATH = "historical_checklists.csv"
WEATHER_PATH = "weather_data.csv"
PHOTO_PATH = "bird_photos"

# --- Load Checklist with Encoding Patch ---
@st.cache_data(ttl=3600)
def load_checklist():
    with open(CHECKLIST_PATH, 'rb') as rawdata:
        result = chardet.detect(rawdata.read(100000))
    encoding = result['encoding'] if result['encoding'] else 'utf-8'
    
    try:
        df = pd.read_csv(CHECKLIST_PATH, encoding=encoding, parse_dates=["OBSERVATION DATE"])
    except UnicodeDecodeError:
        df = pd.read_csv(CHECKLIST_PATH, encoding='utf-8', parse_dates=["OBSERVATION DATE"])
    
    df.columns = df.columns.str.strip()
    return df

# --- Load Data ---
bird_df = load_checklist()
weather_df = load_weather_data(WEATHER_PATH)

# --- UI Styling ---
st.markdown("""
    <style>
    body, .stApp {
        background-color: #f4f1ee;
        color: #3d3b31;
        font-family: 'Arial', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
    }
    .stDataFrame th, .stDataFrame td {
        color: #3d3b31 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("📊 Nature Notes Dashboard")
st.subheader("Headwaters at Incarnate Word")

# --- Sidebar Filters ---
st.sidebar.header("🔎 Filter Data")
view_mode = st.sidebar.selectbox("View Mode", ["Recent Observations", "Compare Timeframes"])

# --- View 1: Recent Observations ---
if view_mode == "Recent Observations":
    st.markdown("### 🐦 Recent Bird Observations")

    recent_data = fetch_recent_ebird_observations(bird_df)

    st.dataframe(
        recent_data[[
            "Common Name",
            "Scientific Name",
            "Observation Count",
            "Observation Date",
            "Time Observations Started",
            "Observer ID",
            "Observer Name",
            "Duration Minutes",
            "Effort Distance KM",
            "Number Observers",
            "Checklist Comments"
        ]],
        use_container_width=True
    )

    display_species_photos(recent_data, PHOTO_PATH)

# --- View 2: Compare Timeframes ---
if view_mode == "Compare Timeframes":
    st.markdown("### 📅 Compare Bird & Weather Trends")

    col1, col2 = st.columns(2)
    with col1:
        start1 = st.date_input("Start Date 1", datetime(2022, 9, 1))
        end1 = st.date_input("End Date 1", datetime(2022, 9, 30))
    with col2:
        start2 = st.date_input("Start Date 2", datetime(2024, 9, 1))
        end2 = st.date_input("End Date 2", datetime(2024, 9, 30))

    filtered1 = filter_by_date_range(bird_df, weather_df, start1, end1)
    filtered2 = filter_by_date_range(bird_df, weather_df, start2, end2)

    comparison = compare_timeframes(filtered1, filtered2)

    st.markdown("#### 📊 Observation Summary")
    st.dataframe(comparison, use_container_width=True)

    st.markdown("#### 🌦️ Weather Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Avg Temp (Period 1)", f"{filtered1['weather']['avg_temp']:.1f}°C")
        st.metric("Total Precip (Period 1)", f"{filtered1['weather']['total_precip']:.1f} mm")
    with col2:
        st.metric("Avg Temp (Period 2)", f"{filtered2['weather']['avg_temp']:.1f}°C")
        st.metric("Total Precip (Period 2)", f"{filtered2['weather']['total_precip']:.1f} mm")

# --- Footer ---
st.markdown("""
---
<div style='text-align: center; font-size: 0.9em; color: #6a645c;'>
    Built by <strong>Brooke Adam</strong>, Run by <strong>Kraken Security Operations</strong><br>
    Nature Notes Dashboard – Powered by eBird & NOAA | Headwaters at Incarnate Word
</div>
""", unsafe_allow_html=True)
