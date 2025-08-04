
import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

st.set_page_config(page_title="Nature Notes Dashboard", layout="wide")

# Title and Description
st.title("📊 Nature Notes Dashboard")
st.markdown("Welcome to the Headwaters Nature Notes Dashboard! This tool combines eBird species observation data and weather trends from the Headwaters at Incarnate Word to explore seasonal patterns, biodiversity, and more.")

# Load data
EBIRD_FILE = Path("ebird_data.csv")
WEATHER_FILE = Path("weather_data.csv")

# Check if data files exist
if not EBIRD_FILE.exists() or not WEATHER_FILE.exists():
    st.warning("🛠️ Data files not found. Please upload `ebird_data.csv` and `weather_data.csv` to the root of the app.")
else:
    ebird_df = pd.read_csv(EBIRD_FILE)
    weather_df = pd.read_csv(WEATHER_FILE)

    # Format dates
    ebird_df['observation_date'] = pd.to_datetime(ebird_df['observation_date'])
    weather_df['Date'] = pd.to_datetime(weather_df['Date'])

    # Date range selector
    min_date = ebird_df['observation_date'].min()
    max_date = ebird_df['observation_date'].max()
    date_range = st.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    start_date, end_date = date_range
    filtered_ebird = ebird_df[(ebird_df['observation_date'] >= pd.to_datetime(start_date)) & (ebird_df['observation_date'] <= pd.to_datetime(end_date))]
    filtered_weather = weather_df[(weather_df['date'] >= pd.to_datetime(start_date)) & (weather_df['date'] <= pd.to_datetime(end_date))]

    # Summary
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
    st.subheader("📈 Observations Over Time")
    obs_chart = alt.Chart(filtered_ebird.groupby('observation_date').size().reset_index(name="observations")).mark_line().encode(
        x='observation_date:T',
        y='observations:Q',
        tooltip=['observation_date:T', 'observations:Q']
    ).properties(width="container", height=300)
    st.altair_chart(obs_chart, use_container_width=True)

    st.subheader("🌡️ Temperature Trends")
    temp_chart = alt.Chart(filtered_weather).mark_line().encode(
        x='date:T',
        y='avg_temp:Q',
        tooltip=['date:T', 'avg_temp:Q']
    ).properties(width="container", height=300)
    st.altair_chart(temp_chart, use_container_width=True)

    st.subheader("🦋 Top Observed Species")
    top_species = filtered_ebird['common_name'].value_counts().nlargest(10).reset_index()
    top_species.columns = ['Species', 'Count']
    species_chart = alt.Chart(top_species).mark_bar().encode(
        x=alt.X('Count:Q'),
        y=alt.Y('Species:N', sort='-x'),
        tooltip=['Species:N', 'Count:Q']
    ).properties(width="container", height=300)
    st.altair_chart(species_chart, use_container_width=True)

    st.divider()

    # Export button
    st.download_button(
        label="📥 Download Filtered Data (CSV)",
        data=filtered_ebird.to_csv(index=False),
        file_name="filtered_ebird_data.csv",
        mime="text/csv"
    )
