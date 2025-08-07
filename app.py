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

# === HEADER ===
st.title("🌳 Nature Notes: Headwaters at Incarnate Word")
st.caption("Explore bird sightings and weather patterns side-by-side. Updated biweekly.")

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
    df["OBSERVATION DATE"] = pd.to_datetime(df["OBSERVATION DATE"])
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

st.title("🌿 Nature Notes Dashboard")
st.markdown("#### Headwaters at Incarnate Word — Real-time bird and weather insights")

# === Load Data ===
checklists_df = load_checklists()
weather_df = load_weather()
ebird_df = load_all_ebird_data()

# === Species Observed per Day ===
st.subheader("📊 Daily Species Observations (Historical)")
daily_species = checklists_df.groupby("OBSERVATION DATE")["COMMON NAME"].nunique().reset_index()
daily_species_chart = alt.Chart(daily_species).mark_line().encode(
    x="OBSERVATION DATE:T",
    y=alt.Y("COMMON NAME:Q", title="SPECIES OBSERVED")
).properties(height=300)
st.altair_chart(daily_species_chart, use_container_width=True)

# === Recent Observations ===
st.subheader("🔎 Recent eBird Sightings")
if not ebird_df.empty:
    ebird_df["obsDt"] = pd.to_datetime(ebird_df["obsDt"])
    ebird_df = ebird_df.sort_values("obsDt", ascending=False)
    st.dataframe(ebird_df[["comName", "howMany", "obsDt", "locName"]].rename(columns={
        "comName": "COMMON NAME",
        "howMany": "OBSERVATION COUNT",
        "obsDt": "OBSERVATION DATE",
        "locName": "LOCATION"
    }))
else:
    st.warning("No recent observations available.")

# === Weather Summary ===
with col2:
    st.subheader("☀️ Weather Trends")
    st.line_chart(weather_filtered.set_index("Date")["Temperature Avg (F)"])
    st.bar_chart(weather_filtered.set_index("Date")["Precipitation (in)"])

# === Weather Chart (Altair) ===
st.subheader("🌦️ Weather Trends")
if not weather_filtered.empty:
    weather_chart = alt.Chart(weather_filtered).transform_fold(
        ["Temperature Max (F)", "Temperature Min (F)", "Precipitation (in)"],
        as_=["Metric", "Value"]
    ).mark_line().encode(
        x="Date:T",
        y="Value:Q",
        color="Metric:N"
    ).properties(height=300)
    st.altair_chart(weather_chart, use_container_width=True)
else:
    st.warning("No weather data available for selected date range.")

# === Summary Table ===
st.subheader("📋 Observation Summary")
summary = checklists_df.groupby("COMMON NAME").agg(
    First_Seen=("OBSERVATION DATE", "min"),
    Last_Seen=("OBSERVATION DATE", "max"),
    Days_Seen=("OBSERVATION DATE", "nunique"),
    Total_Seen=("OBSERVATION COUNT", "sum")
).reset_index()
st.dataframe(summary.sort_values("Days_Seen", ascending=False))

# === Sidebar Filters ===
st.sidebar.header("\u23f0 Filter by Date Range")
quick_range = st.sidebar.radio("Select Range", ["Last 7 Days", "This Month", "Custom Range"], index=1)

if quick_range == "Last 7 Days":
    start_date = datetime.date.today() - datetime.timedelta(days=7)
    end_date = datetime.date.today()
elif quick_range == "This Month":
    today = datetime.date.today()
    start_date = today.replace(day=1)
    end_date = today
else:
    start_date = st.sidebar.date_input("Start Date", datetime.date(1, 1, 2025))
    end_date = st.sidebar.date_input("End Date", datetime.date.today())

# === Filtered Data ===
obs_filtered = checklists_df[(checklists_df["Date"] >= pd.to_datetime(start_date)) & (checklists_df["Date"] <= pd.to_datetime(end_date))]
weather_filtered = weather_df[(weather_df["Date"] >= pd.to_datetime(start_date)) & (weather_df["OBSERVATION DATE"] <= pd.to_datetime(end_date))]

# === Footer ===
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Nature Notes for Headwaters at Incarnate Word • Developed with ❤️ by Brooke Adam and Kraken Security Operations 🌿"
    "</div>",
    unsafe_allow_html=True
)
