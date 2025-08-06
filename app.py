import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from meteostat import Point, Daily
from datetime import datetime
import pytz
import os
from PIL import Image
import chardet

# Set page config
st.set_page_config(
    page_title="Nature Notes at Headwaters",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
LOCATION_IDS = ["L1210588", "L1210849"]
CHECKLIST_PATH = "data/checklist.csv"
WEATHER_LOCATION = Point(29.4657, -98.4738)  # Headwaters coordinates

# Helper Functions
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
    return chardet.detect(raw_data)['encoding']

def load_checklist():
    encoding = detect_encoding(CHECKLIST_PATH)
    return pd.read_csv(CHECKLIST_PATH, encoding=encoding, parse_dates=["OBSERVATION DATE"])

def get_weather_data(start, end):
    data = Daily(WEATHER_LOCATION, start, end)
    data = data.fetch()
    return data

def filter_data_by_date(df, start_date, end_date):
    return df[(df["OBSERVATION DATE"] >= start_date) & (df["OBSERVATION DATE"] <= end_date)]

def display_species_summary(df):
    species_counts = df["COMMON NAME"].value_counts()
    st.subheader("🕊️ Species Observed")
    st.metric("Unique Species", len(species_counts))
    st.bar_chart(species_counts.head(10))
    return species_counts

def display_weather_summary(weather):
    st.subheader("🌤️ Weather Summary")
    st.line_chart(weather[["tavg", "tmin", "tmax"]])
    st.dataframe(weather.describe())

def display_comparison(df, weather):
    st.subheader("📊 Compare Two Time Periods")
    col1, col2 = st.columns(2)
    with col1:
        start1 = st.date_input("Start Date 1", df["OBSERVATION DATE"].min())
        end1 = st.date_input("End Date 1", df["OBSERVATION DATE"].max())
    with col2:
        start2 = st.date_input("Start Date 2", df["OBSERVATION DATE"].min())
        end2 = st.date_input("End Date 2", df["OBSERVATION DATE"].max())

    df1 = filter_data_by_date(df, start1, end1)
    df2 = filter_data_by_date(df, start2, end2)
    wx1 = get_weather_data(start1, end1)
    wx2 = get_weather_data(start2, end2)

    st.markdown("### 📅 Time Period 1")
    sp1 = display_species_summary(df1)
    display_weather_summary(wx1)

    st.markdown("### 📅 Time Period 2")
    sp2 = display_species_summary(df2)
    display_weather_summary(wx2)

    st.markdown("### 🔍 Comparison Table")
    comparison_df = pd.DataFrame({
        "Period 1": sp1,
        "Period 2": sp2
    }).fillna(0).astype(int)
    comparison_df["Change"] = comparison_df["Period 2"] - comparison_df["Period 1"]
    st.dataframe(comparison_df.sort_values("Change", ascending=False))

# Sidebar Filters
st.sidebar.header("🔎 Filter Data")
data_toggle = st.sidebar.radio("View Mode", ["Date Range", "Year-to-Date", "All-Time"], index=0)

df = load_checklist()
start = df["OBSERVATION DATE"].min()
end = df["OBSERVATION DATE"].max()

tz = pytz.timezone("America/Chicago")
today = datetime.now(tz).date()

if data_toggle == "Date Range":
    start_date = st.sidebar.date_input("Start Date", start)
    end_date = st.sidebar.date_input("End Date", end)
elif data_toggle == "Year-to-Date":
    start_date = datetime(today.year, 1, 1).date()
    end_date = today
else:
    start_date = start
    end_date = end

filtered_df = filter_data_by_date(df, start_date, end_date)
weather_data = get_weather_data(start_date, end_date)

# Main Layout
st.title("🌿 Nature Notes at Headwaters")
st.caption("Real-time bird sightings and weather insights from Headwaters at Incarnate Word.")

# Species and Weather Dashboards
col1, col2 = st.columns([2, 1])
with col1:
    species_counts = display_species_summary(filtered_df)
with col2:
    display_weather_summary(weather_data)

# Comparison Tool
with st.expander("🔄 Compare Two Date Ranges"):
    display_comparison(df, weather_data)

# Footer
st.markdown("""
---
**Headwaters at Incarnate Word**  
A sanctuary in the heart of San Antonio. This dashboard is made possible through partnership with the Headwaters team and powered by real-time eBird and weather data.  
**Nature Notes by Brooke Adam** | Designed by Brooke Adam and Kraken Security Operations
""")
