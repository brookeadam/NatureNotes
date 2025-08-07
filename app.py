import streamlit as st
import pandas as pd
import requests
import altair as alt
import datetime
import os
from io import StringIO
from PIL import Image

# === Constants ===
EBIRD_API_KEY = "c49o0js5vkjb"
HEADWATERS_LOCATIONS = ["L1210588", "L1210849"]
CHECKLIST_PATH = "historical_checklists.csv"
WEATHER_PATH = "weather_data.csv"

# === Robust CSV Loader with Encoding Fallback ===
def robust_read_csv(path, **kwargs):
    encodings = ['utf-8', 'ISO-8859-1', 'latin1', 'cp1252']
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except Exception:
            continue
    raise UnicodeDecodeError(f"Unable to read {path} with fallback encodings.")

# === Load Historical Checklists ===
@st.cache_data
def load_checklists():
    df = robust_read_csv(CHECKLIST_PATH)
    df["Observation Date"] = pd.to_datetime(df["Observation Date"])
    return df

# === Load Weather Data ===
@st.cache_data
def load_weather():
    return robust_read_csv(WEATHER_PATH, parse_dates=["Date"])

# === eBird API Call ===
@st.cache_data
def get_ebird_data(loc_id):
    url = f"https://api.ebird.org/v2/data/obs/{loc_id}/recent"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    return pd.DataFrame()

# === Load All eBird Locations ===
@st.cache_data
def load_all_ebird_data():
    dfs = [get_ebird_data(loc) for loc in HEADWATERS_LOCATIONS]
    return pd.concat(dfs, ignore_index=True)

# === App Layout ===
st.set_page_config(page_title="Nature Notes @ Headwaters", layout="wide")

st.title("📒 Nature Notes Dashboard")
st.markdown("#### Headwaters at Incarnate Word — Real-time bird and weather insights")

# === Load Data ===
checklists_df = load_checklists()
weather_df = load_weather()
ebird_df = load_all_ebird_data()

# === Species Observed per Day ===
st.subheader("📊 Daily Species Observations (Historical)")
daily_species = checklists_df.groupby("Date")["Common Name"].nunique().reset_index()
daily_species_chart = alt.Chart(daily_species).mark_line().encode(
    x="Date:T",
    y=alt.Y("Common Name:Q", title="Unique Species Observed")
).properties(height=300)
st.altair_chart(daily_species_chart, use_container_width=True)

# === Recent Observations ===
st.subheader("🔎 Recent eBird Sightings")
if not ebird_df.empty:
    ebird_df["obsDt"] = pd.to_datetime(ebird_df["obsDt"])
    ebird_df = ebird_df.sort_values("obsDt", ascending=False)
    st.dataframe(ebird_df[["comName", "howMany", "obsDt", "locName"]].rename(columns={
        "comName": "Common Name",
        "howMany": "Count",
        "obsDt": "Date Observed",
        "locName": "Location"
    }))
else:
    st.warning("No recent observations available.")

# === Weather Chart ===
st.subheader("🌦️ Weather Trends")
weather_chart = alt.Chart(weather_df).transform_fold(
    ["temp_max", "temp_min", "precipitation"],
    as_=["Metric", "Value"]
).mark_line().encode(
    x="Date:T",
    y="Value:Q",
    color="Metric:N"
).properties(height=300)
st.altair_chart(weather_chart, use_container_width=True)

# === Summary Table ===
st.subheader("📋 Observation Summary")
summary = checklists_df.groupby("Common Name").agg(
    First_Seen=("Date", "min"),
    Last_Seen=("Date", "max"),
    Days_Seen=("Date", "nunique"),
    Total_Seen=("Count", "sum")
).reset_index()
st.dataframe(summary.sort_values("Days_Seen", ascending=False))

# === Footer ===
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Nature Notes for Headwaters at Incarnate Word • Developed with ❤️ by Brooke Adam and Kraken Security Operations 🌿"
    "</div>",
    unsafe_allow_html=True
)
