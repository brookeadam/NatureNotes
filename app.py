import streamlit as st
import pandas as pd
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
import chardet
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Nature Notes Dashboard", layout="wide")

# Constants
CHECKLIST_PATH = "historical_checklists.csv"
WEATHER_PATH = "weather_data.csv"
SPECIES_IMAGES_PATH = "species_thumbnails.json"

# --- Load Data ---
@st.cache_data
def load_checklist():
    # Try auto-detecting encoding and fall back if needed
    with open(CHECKLIST_PATH, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        detected_encoding = result['encoding']

    # Try detected encoding, then UTF-8, then Latin-1
    for enc in [detected_encoding, 'utf-8', 'latin1']:
        try:
            df = pd.read_csv(CHECKLIST_PATH, encoding=enc, parse_dates=["OBSERVATION DATE"])
            break
        except UnicodeDecodeError:
            continue
    else:
        raise UnicodeDecodeError(
            f"Could not decode {CHECKLIST_PATH} using {detected_encoding}, UTF-8, or Latin-1 encodings."
        )

    df["COMMON NAME"] = df["COMMON NAME"].str.strip()
    return df

@st.cache_data
def load_weather():
    df = pd.read_csv(WEATHER_PATH, parse_dates=["date"])
    return df

@st.cache_data
def load_species_images():
    if os.path.exists(SPECIES_IMAGES_PATH):
        with open(SPECIES_IMAGES_PATH, "r") as f:
            return json.load(f)
    return {}

# Load data
ebird_df = load_checklist()
weather_df = load_weather()
species_images = load_species_images()

# --- Sidebar Filters ---
st.sidebar.header("🔎 Filter Data")
view_mode = st.sidebar.radio("View Mode", ["📊 Nature Notes Dashboard", "📄 Raw eBird Checklist"])

min_date = ebird_df["OBSERVATION DATE"].min().date()
max_date = ebird_df["OBSERVATION DATE"].max().date()
def_season_start = max_date - timedelta(days=90)

start_date, end_date = st.sidebar.date_input("Select Date Range", [def_season_start, max_date], min_value=min_date, max_value=max_date)

# Filtered Data
data = ebird_df[(ebird_df["OBSERVATION DATE"].dt.date >= start_date) & (ebird_df["OBSERVATION DATE"].dt.date <= end_date)]
weather = weather_df[(weather_df["date"].dt.date >= start_date) & (weather_df["date"].dt.date <= end_date)]

# --- Main View ---
if view_mode == "📄 Raw eBird Checklist":
    st.title("📄 Raw eBird Checklist")
    st.dataframe(data)
else:
    st.title("📊 Nature Notes Dashboard")
    st.markdown("## Headwaters at Incarnate Word")

    # Species Summary
    st.subheader("🦉 Bird Species Observed")
    species_counts = data["COMMON NAME"].value_counts().reset_index()
    species_counts.columns = ["Species", "Count"]
    st.dataframe(species_counts)

    # Line Chart - Observations per Day
    st.subheader("📈 Daily Bird Observations")
    daily_counts = data.groupby(data["OBSERVATION DATE"].dt.date)["COMMON NAME"].count().reset_index()
    daily_counts.columns = ["Date", "Observation Count"]
    fig = px.line(daily_counts, x="Date", y="Observation Count", title="Observations Over Time")
    st.plotly_chart(fig, use_container_width=True)

    # Weather Overlay
    st.subheader("🌦️ Temperature Trend")
    if not weather.empty:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=weather["date"], y=weather["temperature_avg"], mode='lines+markers', name='Avg Temp'))
        fig2.update_layout(title="Average Temperature Over Time", xaxis_title="Date", yaxis_title="Temp (°F)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No weather data available for selected range.")

# --- Footer ---
st.markdown("---")
st.markdown("Built by Brooke Adam, Run by Kraken Security Operations")
