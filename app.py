import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Nature Notes", layout="wide")

st.markdown("# 📊 Nature Notes Dashboard")
st.markdown("### Headwaters at Incarnate Word")
st.markdown("**Built by Brooke Adam, Run by Kraken Security Operations**")

CHECKLIST_PATH = "historical_checklists.csv"
WEATHER_PATH = "weather_data.csv"

# Robust loading function with utf-8 fallback to latin1
@st.cache_data
def load_checklist():
    try:
        return pd.read_csv(CHECKLIST_PATH, encoding="utf-8", parse_dates=["OBSERVATION DATE"])
    except UnicodeDecodeError:
        return pd.read_csv(CHECKLIST_PATH, encoding="latin1", parse_dates=["OBSERVATION DATE"])

@st.cache_data
def load_weather():
    try:
        return pd.read_csv(WEATHER_PATH, encoding="utf-8", parse_dates=["date"])
    except UnicodeDecodeError:
        return pd.read_csv(WEATHER_PATH, encoding="latin1", parse_dates=["date"])

bird_df = load_checklist()
weather_df = load_weather()

# Sidebar filters
st.sidebar.header("🔎 Filter Data")
date_range = st.sidebar.date_input("Select Date Range", [bird_df["OBSERVATION DATE"].min(), bird_df["OBSERVATION DATE"].max()])
selected_location = st.sidebar.selectbox("Select Location", bird_df["LOCALITY"].unique())
view_mode = st.sidebar.radio("View Mode", ["Summary", "Raw Data"])

# Filter data
filtered_df = bird_df[
    (bird_df["OBSERVATION DATE"] >= pd.to_datetime(date_range[0])) &
    (bird_df["OBSERVATION DATE"] <= pd.to_datetime(date_range[1])) &
    (bird_df["LOCALITY"] == selected_location)
]

filtered_weather = weather_df[
    (weather_df["date"] >= pd.to_datetime(date_range[0])) &
    (weather_df["date"] <= pd.to_datetime(date_range[1]))
]

# Display filtered data
if view_mode == "Summary":
    st.subheader("Species Observed")
    species_counts = filtered_df["COMMON NAME"].value_counts().reset_index()
    species_counts.columns = ["Species", "Sightings"]
    st.dataframe(species_counts)

    st.subheader("Weather Trends")
    fig, ax = plt.subplots()
    ax.plot(filtered_weather["date"], filtered_weather["temperature_avg"], marker='o')
    ax.set_title("Average Temperature Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Avg Temp (°F)")
    st.pyplot(fig)

else:
    st.subheader("Raw Bird Observations")
    st.dataframe(filtered_df)

    st.subheader("Raw Weather Data")
    st.dataframe(filtered_weather)

# Footer
st.markdown("---")
st.markdown("🕊️ Powered by eBird and Weather Data | 📍 Headwaters at Incarnate Word")
st.markdown("© 2025 Brooke Adam. All rights reserved.")
