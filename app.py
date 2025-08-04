import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Nature Notes Dashboard", layout="wide")

# Title and Description
st.title("📊 Nature Notes Dashboard")
st.markdown("Welcome to the Headwaters Nature Notes Dashboard! This tool combines eBird species observation data and weather trends from the Headwaters at Incarnate Word to explore seasonal patterns, biodiversity, and more.")

# Load data
EBIRD_FILE = "ebird_data.csv"
WEATHER_FILE = "weather_data.csv"

# Check if data files exist
if not Path(EBIRD_FILE).exists() or not Path(WEATHER_FILE).exists():
    st.warning("🛠️ Data files not found. Please upload `ebird_data.csv` and `weather_data.csv` to the main directory.")
else:
    ebird_df = pd.read_csv(EBIRD_FILE)
    weather_df = pd.read_csv(WEATHER_FILE)

    # Convert date columns to datetime
    ebird_df['observation_date'] = pd.to_datetime(ebird_df['observation_date'])
    weather_df['Date'] = pd.to_datetime(weather_df['Date'])

    # Date range selector
    min_date = ebird_df['observation_date'].min()
    max_date = ebird_df['observation_date'].max()
    date_range = st.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
    start_date, end_date = date_range

    # Filter data by date range
    filtered_ebird = ebird_df[(ebird_df['observation_date'] >= pd.to_datetime(start_date)) & (ebird_df['observation_date'] <= pd.to_datetime(end_date))]
    filtered_weather = weather_df[(weather_df['Date'] >= pd.to_datetime(start_date)) & (weather_df['Date'] <= pd.to_datetime(end_date))]

    # Summary metrics
    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Species Observed", filtered_ebird['common_name'].nunique())
    with col2:
        st.metric("Total Checklists", filtered_ebird['sampling_event_identifier'].nunique())
    with col3:
        st.metric("Total Observations", len(filtered_ebird))

    st.divider()

    # Visualizations
    st.subheader("Species vs. Temperature Over Time")

    chart_data = pd.merge(
        filtered_ebird.groupby('observation_date')['common_name'].nunique().reset_index(name="Unique Species"),
        filtered_weather[['Date', 'Max Temp (F)', 'Min Temp (F)']],
        left_on='observation_date', right_on='Date', how='left'
    ).dropna()

    st.line_chart(chart_data.set_index("observation_date"))

    st.divider()

    # Download filtered eBird data
    st.download_button(
        label="📥 Download Filtered eBird Data (CSV)",
        data=filtered_ebird.to_csv(index=False),
        file_name="filtered_ebird_data.csv",
        mime="text/csv"
    )
