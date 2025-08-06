import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta
from meteostat import Daily, Point

# --- Configuration ---
CHECKLIST_PATH = "historical_checklists.csv"
EBIRD_LOCATION_IDS = ["L1210588", "L1210849"]
HEADWATERS_COORDS = (29.4654, -98.4736)  # San Antonio
DEFAULT_TZ = "US/Central"

st.set_page_config(
    page_title="Nature Notes – Headwaters at Incarnate Word",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
body {
    background-color: #f3f2ef;
    color: #3e3e3e;
    font-family: 'Arial', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# --- Load Data ---
@st.cache_data

def load_checklist():
    return pd.read_csv(CHECKLIST_PATH, encoding="utf-8", parse_dates=["OBSERVATION DATE"])

df = load_checklist()

# --- Sidebar Filters ---
st.sidebar.header("Select Date Range")
date_options = ["Today", "Last 7 Days", "This Month", "This Season", "Year-to-Date", "All-Time", "Custom Range"]
date_selection = st.sidebar.radio("", date_options)

now = datetime.now()

if date_selection == "Today":
    start_date = end_date = now.date()
elif date_selection == "Last 7 Days":
    start_date = now.date() - timedelta(days=6)
    end_date = now.date()
elif date_selection == "This Month":
    start_date = now.replace(day=1).date()
    end_date = now.date()
elif date_selection == "This Season":
    month = now.month
    if month in [12, 1, 2]:
        start_date = datetime(now.year if month != 12 else now.year - 1, 12, 1).date()
    elif month in [3, 4, 5]:
        start_date = datetime(now.year, 3, 1).date()
    elif month in [6, 7, 8]:
        start_date = datetime(now.year, 6, 1).date()
    else:
        start_date = datetime(now.year, 9, 1).date()
    end_date = now.date()
elif date_selection == "Year-to-Date":
    start_date = datetime(now.year, 1, 1).date()
    end_date = now.date()
elif date_selection == "All-Time":
    start_date = df["OBSERVATION DATE"].min().date()
    end_date = df["OBSERVATION DATE"].max().date()
else:
    start_date = st.sidebar.date_input("Start Date", value=now.date() - timedelta(days=30))
    end_date = st.sidebar.date_input("End Date", value=now.date())

mask = (df["OBSERVATION DATE"].dt.date >= start_date) & (df["OBSERVATION DATE"].dt.date <= end_date)
df_filtered = df[mask]

# --- Weather Data (Live) ---
def get_weather_data(start, end):
    location = Point(HEADWATERS_COORDS[0], HEADWATERS_COORDS[1], 200)
    data = Daily(location, start, end)
    data = data.fetch()
    data.reset_index(inplace=True)
    return data

weather_df = get_weather_data(start_date, end_date)

# --- Bird Counts ---
species_counts = df_filtered.groupby("COMMON NAME")["OBSERVATION COUNT"].sum().sort_values(ascending=False)
total_species = species_counts.shape[0]
total_birds = species_counts.sum()

st.title("🪶 Nature Notes – Headwaters at Incarnate Word")
st.caption("Live updates from Headwaters at Incarnate Word using eBird and local weather records.")

st.metric("Unique Species Observed", total_species)
st.metric("Total Bird Count", total_birds)

# --- Plots ---
st.subheader("Bird Counts by Species")
st.bar_chart(species_counts.head(20))

st.subheader("Temperature Trend")
if not weather_df.empty:
    st.line_chart(weather_df.set_index("time")["tavg"])
else:
    st.warning("No weather data available for the selected range.")

# --- Comparison Tool ---
st.header("📊 Compare Two Timeframes")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Timeframe A**")
    a_start = st.date_input("Start A", value=now.date() - timedelta(days=60), key="a_start")
    a_end = st.date_input("End A", value=now.date() - timedelta(days=45), key="a_end")

with col2:
    st.markdown("**Timeframe B**")
    b_start = st.date_input("Start B", value=now.date() - timedelta(days=30), key="b_start")
    b_end = st.date_input("End B", value=now.date() - timedelta(days=15), key="b_end")

# Get data for A
mask_a = (df["OBSERVATION DATE"].dt.date >= a_start) & (df["OBSERVATION DATE"].dt.date <= a_end)
df_a = df[mask_a]
species_a = df_a.groupby("COMMON NAME")["OBSERVATION COUNT"].sum()
weather_a = get_weather_data(a_start, a_end)

# Get data for B
mask_b = (df["OBSERVATION DATE"].dt.date >= b_start) & (df["OBSERVATION DATE"].dt.date <= b_end)
df_b = df[mask_b]
species_b = df_b.groupby("COMMON NAME")["OBSERVATION COUNT"].sum()
weather_b = get_weather_data(b_start, b_end)

comparison = pd.DataFrame({
    "Timeframe A": species_a,
    "Timeframe B": species_b
}).fillna(0).astype(int).sort_values(by="Timeframe A", ascending=False)

st.subheader("Species Count Comparison")
st.dataframe(comparison)

st.subheader("Temperature Comparison")
fig, ax = plt.subplots()
ax.plot(weather_a["time"], weather_a["tavg"], label="A")
ax.plot(weather_b["time"], weather_b["tavg"], label="B")
ax.set_ylabel("Average Temp (°C)")
ax.set_xlabel("Date")
ax.legend()
st.pyplot(fig)

# --- Footer ---
st.markdown("""
<hr style="margin-top: 3em;">
<p style="font-size: 0.9em; color: #666;">
Nature Notes is a project of Headwaters at Incarnate Word. Data sourced from eBird and Meteostat.
</p>
""", unsafe_allow_html=True)
