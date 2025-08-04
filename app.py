import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

# -------------- SETTINGS --------------
EBIRD_API_KEY = "c49o0js5vkjb"
LOCATION_IDS = ["L1210588", "L1210849"]
WEATHER_CSV = "weather_data.csv"
CHECKLIST_CSV = "checklist_data.csv"
APP_TITLE = "Nature Notes – Headwaters at Incarnate Word"
APP_SUBTITLE = "Birds, Weather & Phenology Dashboard"
APP_DESCRIPTION = "Live updates from Headwaters at Incarnate Word using eBird and local weather records."
# --------------------------------------

st.set_page_config(APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.subheader(APP_SUBTITLE)
st.markdown(APP_DESCRIPTION)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_weather_data():
    df = pd.read_csv(WEATHER_CSV)
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'])
    return df

@st.cache_data
def load_checklist_data():
    df = pd.read_csv(CHECKLIST_CSV)
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    return df

weather_df = load_weather_data()
checklist_df = load_checklist_data()

# ---------------- DATE FILTERS ----------------
min_date = checklist_df['observation_date'].min()
max_date = checklist_df['observation_date'].max()

start_date = st.date_input("Start Date", min_value=min_date, max_value=max_date, value=max_date - timedelta(days=30))
end_date = st.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date)

filtered_checklist = checklist_df[
    (checklist_df['observation_date'] >= pd.to_datetime(start_date)) &
    (checklist_df['observation_date'] <= pd.to_datetime(end_date))
]

filtered_weather = weather_df[
    (weather_df['Date'] >= pd.to_datetime(start_date)) &
    (weather_df['Date'] <= pd.to_datetime(end_date))
]

# ---------------- WEATHER VISUALS ----------------
st.subheader("📈 Weather Trends")

if not filtered_weather.empty:
    st.line_chart(filtered_weather.set_index('Date')[['Max Temp (F)', 'Min Temp (F)']])
    st.bar_chart(filtered_weather.set_index('Date')['Precipitation (in)'])
else:
    st.warning("No weather data available for selected date range.")

# ---------------- EBIRD DATA & THUMBNAILS ----------------
st.subheader("🕊️ Recent Bird Observations")

def fetch_species_images(species_name):
    query = species_name.replace(" ", "+")
    url = f"https://api.ebird.org/v2/ref/taxa/photos/{query}?q={query}&fmt=json"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list):
                return data[0].get("mediaUrl")
    except:
        pass
    return None

if not filtered_checklist.empty:
    species_counts = filtered_checklist['comName'].value_counts().reset_index()
    species_counts.columns = ['Species', 'Count']

    for i, row in species_counts.iterrows():
        col1, col2 = st.columns([1, 8])
        with col1:
            img_url = fetch_species_images(row['Species'])
            if img_url:
                st.image(img_url, width=80)
            else:
                st.empty()
        with col2:
            st.markdown(f"**{row['Species']}** — {row['Count']} observation(s)")
else:
    st.warning("No bird observations available for selected date range.")

# ----------------- FOOTER -----------------
st.markdown("---")
st.markdown("""
**Credits:** Built for [Headwaters at Incarnate Word](https://www.headwaters-iw.org/)  
**Mission:** To observe and share seasonal nature insights using real data from the land we steward.  
**Maintainer:** Brooke Adam
""")
