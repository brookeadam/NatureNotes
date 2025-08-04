import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Nature Notes Dashboard", layout="wide")

# Title and Description
st.title("📊 Nature Notes Dashboard")
st.markdown("Welcome to the Headwaters Nature Notes Dashboard! This tool combines eBird species observation data and weather trends from the Headwaters at Incarnate Word to explore seasonal patterns, biodiversity, and more.")

# Load data from root directory
EBIRD_FILE = Path("ebird_data.csv")
WEATHER_FILE = Path("weather_data.csv")

# Check if data files exist
if not EBIRD_FILE.exists() or not WEATHER_FILE.exists():
    st.warning("🛠️ Data files not found. Please upload `ebird_data.csv` and `weather_data.csv` to the root of your repository.")
else:
    ebird_df = pd.read_csv(EBIRD_FILE)
    weather_df = pd.read_csv(WEATHER_FILE)

    # Date range selector
    min_date = pd.to_datetime(ebird_df['observation_date']).min()
    max_date = pd.to_datetime(ebird_df['observation_date']).max()
    date_range = st.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    start_date, end_date = date_range
    ebird_df['observation_date'] = pd.to_datetime(ebird_df['observation_date'])
    filtered_df = ebird_df[(ebird_df['observation_date'] >= pd.to_datetime(start_date)) & (ebird_df['observation_date'] <= pd.to_datetime(end_date))]

    # Summary
    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Species Observed", filtered_df['common_name'].nunique())
    with col2:
        st.metric("Total Checklists", filtered_df['sampling_event_identifier'].nunique())
    with col3:
        st.metric("Total Observations", len(filtered_df))

    st.divider()

    # Placeholder for visuals
    st.subheader("Visualizations (Coming Soon)")
    st.info("📌 Charts showing species trends, weather overlays, and comparative graphs will appear here.")

    st.divider()

    # Export button
    st.download_button(
        label="📥 Download Filtered Data (CSV)",
        data=filtered_df.to_csv(index=False),
        file_name="filtered_ebird_data.csv",
        mime="text/csv"
    )
