import streamlit as st
import pandas as pd
import altair as alt
import requests
from meteostat import Daily, Point
from datetime import datetime
import chardet
import os

# ──────────────────────────────────────────────
# App Config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Nature Notes – Headwaters",
    page_icon="🪶",
    layout="wide",
)

st.title("📖 Nature Notes – Headwaters Dashboard")
st.caption("Powered by real-time bird sightings and weather trends")

# ──────────────────────────────────────────────
# Constants & Paths
# ──────────────────────────────────────────────
LOCATION_IDS = ["L1210588", "L1210849"]  # Headwaters locations
eBIRD_API_KEY = os.getenv("EBIRD_API_KEY", "c49o0js5vkjb")
CHECKLIST_PATH = "historical_checklists.csv"
CITY_COORDS = Point(29.4658, -98.4684)  # San Antonio, TX

# ──────────────────────────────────────────────
# Auto-Detect Encoding
# ──────────────────────────────────────────────
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

# ──────────────────────────────────────────────
# Load Historical eBird Checklist
# ──────────────────────────────────────────────
def load_checklist():
    encoding = detect_encoding(CHECKLIST_PATH)
    return pd.read_csv(CHECKLIST_PATH, encoding=encoding, parse_dates=["OBSERVATION DATE"])

df = load_checklist()

# ──────────────────────────────────────────────
# Load Historical Weather Data from Meteostat
# ──────────────────────────────────────────────
def load_weather_data(start_date, end_date):
    data = Daily(CITY_COORDS, start=start_date, end=end_date)
    data = data.fetch().reset_index()
    return data

# ──────────────────────────────────────────────
# Date Filters
# ──────────────────────────────────────────────
st.sidebar.header("🔎 Filter Data")
view_mode = st.sidebar.radio("View Mode", ["Date Range", "Year-to-Date", "All-Time"])

today = datetime.today()

if view_mode == "Date Range":
    date_range = st.sidebar.date_input("Select Range", [df["OBSERVATION DATE"].min(), today])
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
elif view_mode == "Year-to-Date":
    start_date = datetime(today.year, 1, 1)
    end_date = today
else:
    start_date = df["OBSERVATION DATE"].min()
    end_date = today

# ──────────────────────────────────────────────
# Filter Data by Date
# ──────────────────────────────────────────────
df_filtered = df[(df["OBSERVATION DATE"] >= start_date) & (df["OBSERVATION DATE"] <= end_date)]
weather_df = load_weather_data(start_date, end_date)

# ──────────────────────────────────────────────
# Summary Stats
# ──────────────────────────────────────────────
st.subheader("📊 Summary")
col1, col2 = st.columns(2)

species_count = df_filtered["COMMON NAME"].nunique()
observation_count = df_filtered.shape[0]

col1.metric("Unique Species", species_count)
col2.metric("Total Observations", observation_count)

# ──────────────────────────────────────────────
# Daily Observations Chart
# ──────────────────────────────────────────────
df_daily = df_filtered.groupby("OBSERVATION DATE")["COMMON NAME"].nunique().reset_index()
df_daily.columns = ["Date", "Unique Species"]

st.subheader("🗓️ Daily Unique Species Count")
chart = alt.Chart(df_daily).mark_line().encode(
    x="Date:T",
    y="Unique Species:Q"
).properties(width=800, height=300)

st.altair_chart(chart, use_container_width=True)

# ──────────────────────────────────────────────
# Weather Trend Chart
# ──────────────────────────────────────────────
st.subheader("🌤️ Temperature Trends")

if not weather_df.empty:
    temp_chart = alt.Chart(weather_df).transform_fold(
        ["tavg", "tmin", "tmax"],
        as_=["Temperature Type", "Temperature"]
    ).mark_line().encode(
        x="time:T",
        y="Temperature:Q",
        color="Temperature Type:N"
    ).properties(width=800, height=300)

    st.altair_chart(temp_chart, use_container_width=True)
else:
    st.info("No weather data available for the selected range.")

# ──────────────────────────────────────────────
# Checklist Table Preview
# ──────────────────────────────────────────────
st.subheader("📋 Recent Bird Observations")
st.dataframe(df_filtered.sort_values("OBSERVATION DATE", ascending=False).head(20), use_container_width=True)

# ──────────────────────────────────────────────
# Footer: Branding, Mission, and Credits
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; font-size: 0.9em; color: #666;'>
        <p><strong>Nature Notes</strong> is a community-driven bird and weather dashboard for the Headwaters at Incarnate Word.<br>
        Powered by real-time eBird data and local weather trends.<br><br>
        Developed in partnership with <a href="https://www.uiw.edu/headwaters/" target="_blank">The Headwaters at Incarnate Word</a> and <a href="https://krakencollective.org" target="_blank">Kraken Collective</a>.<br>
        Built by Brooke Adam. Run by Kraken Security Operations.<br>
        Built with ❤️ for environmental awareness and education.</p>
    </div>
    """,
    unsafe_allow_html=True
)
