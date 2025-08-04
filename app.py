import streamlit as st import pandas as pd import requests from datetime import datetime, timedelta from pathlib import Path import os

CONFIGURATION

EBIRD_LOCATIONS = ["L1210588", "L1210849"] EBIRD_API_KEY = "c49o0js5vkjb" EBIRD_HEADERS = {"X-eBirdApiToken": EBIRD_API_KEY}

WEATHER_CSV = "weather_data.csv" DATA_EXPORT = "filtered_ebird_data.csv"

st.set_page_config(page_title="Nature Notes Dashboard", layout="wide")

--- HEADER ---

st.title("📊 Nature Notes Dashboard") st.markdown(""" Welcome to the Headwaters at Incarnate Word Nature Notes Dashboard. This tool combines live eBird species observations and weather trends to explore biodiversity, phenology, and seasonal changes at the Headwaters Sanctuary. """)

--- LOAD WEATHER DATA ---

@st.cache_data def load_weather(): df = pd.read_csv(WEATHER_CSV) df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns] df['date'] = pd.to_datetime(df['date']) return df

--- FETCH LATEST EBIRD DATA ---

@st.cache_data(ttl=3600) def fetch_ebird_data(): all_data = [] for loc_id in EBIRD_LOCATIONS: url = f"https://api.ebird.org/v2/data/obs/{loc_id}/recent" response = requests.get(url, headers=EBIRD_HEADERS) if response.status_code == 200: for obs in response.json(): obs['location_id'] = loc_id all_data.append(obs) df = pd.DataFrame(all_data) if not df.empty: df['obsDt'] = pd.to_datetime(df['obsDt']) df.rename(columns={ 'comName': 'common_name', 'sciName': 'scientific_name', 'howMany': 'count', 'obsDt': 'observation_date', 'locName': 'location_name' }, inplace=True) return df

--- LOAD & FILTER ---

weather_df = load_weather() ebird_df = fetch_ebird_data()

--- DATE RANGE FILTER ---

if not ebird_df.empty: min_date = ebird_df['observation_date'].min() max_date = ebird_df['observation_date'].max() date_range = st.date_input("📅 Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date) start_date, end_date = date_range ebird_filtered = ebird_df[(ebird_df['observation_date'] >= pd.to_datetime(start_date)) & (ebird_df['observation_date'] <= pd.to_datetime(end_date))] weather_filtered = weather_df[(weather_df['date'] >= pd.to_datetime(start_date)) & (weather_df['date'] <= pd.to_datetime(end_date))]

# --- SUMMARY METRICS ---
st.subheader("📈 Observation Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Species", ebird_filtered['common_name'].nunique())
col2.metric("Total Checklists", ebird_filtered['location_id'].nunique())
col3.metric("Total Observations", len(ebird_filtered))

# --- WEATHER CHARTS ---
st.subheader("🌦️ Weather Trends")
st.line_chart(weather_filtered.set_index('date')[['max_temp_(f)', 'min_temp_(f)']])
st.bar_chart(weather_filtered.set_index('date')[['precipitation_(in)']])

# --- SPECIES THUMBNAILS ---
st.subheader("🦉 Recent Sightings")
grouped = ebird_filtered.groupby(['common_name', 'observation_date']).size().reset_index(name='counts')
for _, row in grouped.iterrows():
    with st.container():
        col1, col2 = st.columns([1, 6])
        img_url = f"https://ebird.org/media/catalog?taxonCode={row['common_name'].lower().replace(' ', '')}&mediaType=photo"
        col1.image("https://upload.wikimedia.org/wikipedia/commons/1/14/No_Image_Available.jpg", width=80)
        col2.markdown(f"**{row['common_name']}** — {row['observation_date'].date()} ({row['counts']} obs)")

# --- DOWNLOAD ---
st.download_button(
    "📥 Download CSV", ebird_filtered.to_csv(index=False), file_name=DATA_EXPORT, mime="text/csv")

else: st.warning("⚠️ No eBird data found. Please check the eBird API key or location IDs.")

--- FOOTER ---

st.markdown("""

Nature Notes is a project of the Headwaters at Incarnate Word. Data sources include eBird and the NOAA National Weather Service. """)

