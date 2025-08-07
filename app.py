import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import base64
import os
from datetime import datetime, timedelta
from io import BytesIO, StringIO
from chardet import detect

st.set_page_config(layout="wide")

# Constants
EBIRD_API_KEY = "c49o0js5vkjb"
EBIRD_LOCATIONS = ["L1210588", "L1210849"]
CHECKLIST_PATH = "data/historical_checklists.csv"
CACHE_PATH = "data/recent_checklists.csv"
THUMBNAIL_URL_TEMPLATE = "https://api.ebird.org/v2/ref/media/{{speciesCode}}?q={{commonName}}&maxResults=1"

# Load historical checklist with encoding detection
def load_checklist():
    with open(CHECKLIST_PATH, 'rb') as f:
        result = detect(f.read())
    encoding = result['encoding']
    df = pd.read_csv(CHECKLIST_PATH, encoding=encoding, parse_dates=["OBSERVATION DATE"])
    return df

# Fetch recent observations for each location and cache
def fetch_recent_observations():
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    combined = []
    for loc in EBIRD_LOCATIONS:
        url = f"https://api.ebird.org/v2/data/obs/{loc}/recent"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            df["locationId"] = loc
            combined.append(df)
    if combined:
        result = pd.concat(combined)
        result.to_csv(CACHE_PATH, index=False)
        return result
    return pd.DataFrame()

# Load cached or fetch new data if cache is outdated
def load_recent():
    if os.path.exists(CACHE_PATH):
        modified = datetime.fromtimestamp(os.path.getmtime(CACHE_PATH))
        if datetime.now() - modified > timedelta(days=3):
            return fetch_recent_observations()
        return pd.read_csv(CACHE_PATH)
    return fetch_recent_observations()

# Remove duplicate observations by species/date/count

def deduplicate_observations(df):
    return df.drop_duplicates(subset=["comName", "obsDt", "howMany"])

# Fetch bird thumbnail
@st.cache_data(show_spinner=False)
def get_thumbnail(species_code, common_name):
    try:
        url = f"https://api.ebird.org/v2/ref/media/{species_code}?q={common_name}&maxResults=1"
        headers = {"X-eBirdApiToken": EBIRD_API_KEY}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            media = response.json()
            if media:
                return media[0].get("previewUrl")
    except:
        return None
    return None

# UI
st.title("📊 Nature Notes Dashboard")
st.markdown("""
**Headwaters at Incarnate Word**  
_Built by Brooke Adam, Run by Kraken Security Operations_
""")

with st.sidebar:
    st.header("🔎 Filter Data")
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    end_date = st.date_input("End Date", datetime.now())
    view_mode = st.radio("View Mode", ["Recent Observations", "Compare Years"], horizontal=True)

# Load data
historical_df = load_checklist()
recent_df = load_recent()
recent_df = deduplicate_observations(recent_df)

# Format dates
historical_df["OBSERVATION DATE"] = pd.to_datetime(historical_df["OBSERVATION DATE"]).dt.date
recent_df["obsDt"] = pd.to_datetime(recent_df["obsDt"]).dt.date

# Display
if view_mode == "Recent Observations":
    st.subheader("🕊️ Recent Bird Observations")
    filtered = recent_df[(recent_df["obsDt"] >= pd.to_datetime(start_date).date()) &
                         (recent_df["obsDt"] <= pd.to_datetime(end_date).date())]
    if filtered.empty:
        st.warning("No observations in this date range.")
    else:
        for _, row in filtered.iterrows():
            col1, col2 = st.columns([1, 6])
            with col1:
                thumb = get_thumbnail(row.get("speciesCode", ""), row.get("comName", ""))
                if thumb:
                    st.image(thumb, width=80)
            with col2:
                st.markdown(f"**{row['comName']}** (_{row.get('sciName', '')}_)")
                st.markdown(f"Observed by **{row.get('userDisplayName', 'N/A')}** on **{row['obsDt']}**")
                st.markdown(f"Count: {row.get('howMany', 'N/A')}, Duration: {row.get('durationMinutes', 'N/A')} min, Distance: {row.get('effortDistanceKm', 'N/A')} km")

elif view_mode == "Compare Years":
    st.subheader("📆 Compare Yearly Observations")
    month = st.selectbox("Select Month", range(1, 13))
    year1 = st.selectbox("Year 1", sorted(historical_df["OBSERVATION DATE"].dt.year.unique()))
    year2 = st.selectbox("Year 2", sorted(historical_df["OBSERVATION DATE"].dt.year.unique()))

    df1 = historical_df[(historical_df["OBSERVATION DATE"].dt.year == year1) &
                        (historical_df["OBSERVATION DATE"].dt.month == month)]
    df2 = historical_df[(historical_df["OBSERVATION DATE"].dt.year == year2) &
                        (historical_df["OBSERVATION DATE"].dt.month == month)]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Species Count - " + str(year1), df1["COMMON NAME"].nunique())
        st.dataframe(df1[["COMMON NAME", "OBSERVATION COUNT", "OBSERVATION DATE"]])
    with col2:
        st.metric("Species Count - " + str(year2), df2["COMMON NAME"].nunique())
        st.dataframe(df2[["COMMON NAME", "OBSERVATION COUNT", "OBSERVATION DATE"]])

# Download
st.markdown("---")
st.download_button(
    "⬇️ Download Full Historical Data",
    data=historical_df.to_csv(index=False).encode("utf-8"),
    file_name="historical_checklists.csv",
    mime="text/csv"
)

st.download_button(
    "⬇️ Download Recent Observations",
    data=recent_df.to_csv(index=False).encode("utf-8"),
    file_name="recent_ebird_data.csv",
    mime="text/csv"
)

# Footer
st.markdown("""
---
🪶 _This dashboard supports wildlife tracking at the Headwaters Sanctuary._

**Credits:** Built by Brooke Adam • Suported by Kraken Security Operations • Powered by eBird + NOAA
""")
