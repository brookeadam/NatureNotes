import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

st.set_page_config(
    page_title="Nature Notes – Headwaters at Incarnate Word",
    page_icon="🪶",
    layout="wide",
)

st.title("🪶 Nature Notes – Headwaters at Incarnate Word")
st.subheader("Birds, Weather & Phenology Dashboard")
st.markdown(
    "Live updates from Headwaters at Incarnate Word using eBird and local weather records."
)

# Constants
EBIRD_LOC_IDS = ["L1210588", "L1210849"]
EBIRD_API_KEY = os.getenv("EBIRD_API_KEY")
CHECKLIST_PATH = "historical_checklists.csv"

# Load eBird historical data
@st.cache_data
def load_checklist():
    df = pd.read_csv(CHECKLIST_PATH, parse_dates=["obsDt"])
    return df

df = load_checklist()

# Date range selector with safety check
min_date = df["obsDt"].min().date()
max_date = df["obsDt"].max().date()
default_start = max(min_date, max_date - timedelta(days=30))

start_date = st.date_input(
    "Start Date",
    min_value=min_date,
    max_value=max_date,
    value=default_start
)
end_date = st.date_input("End Date", min_value=start_date, max_value=max_date, value=max_date)

# Filter by date
mask = (df["obsDt"].dt.date >= start_date) & (df["obsDt"].dt.date <= end_date)
filtered = df[mask]

st.markdown(f"### 📅 Data from {start_date} to {end_date}")
st.write(f"Total observations: {len(filtered)}")
st.dataframe(filtered)

# Optional: simple species count chart
species_counts = (
    filtered.groupby("comName")["howMany"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

st.markdown("### 🔟 Most Frequently Observed Species")
st.bar_chart(species_counts)

# Branding and footer
st.markdown("---")
st.markdown(
    "📍 _Dashboard powered by Headwaters at Incarnate Word & Nature Notes — created by Brooke Adam_"
)
