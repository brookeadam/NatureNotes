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

st.set_page_config(page_title="Nature Notes @ Headwaters", layout="wide")

# === Robust CSV Loader ===
def robust_read_csv(path, **kwargs):
    encodings = ['utf-8', 'ISO-8859-1', 'latin1', 'cp1252']
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except Exception:
            continue
    raise UnicodeDecodeError(f"Unable to read {path} with fallback encodings.")

# === Loaders ===
@st.cache_data
def load_checklists():
    df = robust_read_csv(CHECKLIST_PATH)
    df["OBSERVATION DATE"] = pd.to_datetime(df["OBSERVATION DATE"])
    return df

@st.cache_data
def load_weather():
    return robust_read_csv(WEATHER_PATH, parse_dates=["Date"])

@st.cache_data
def get_ebird_data(loc_id):
    url = f"https://api.ebird.org/v2/data/obs/{loc_id}/recent"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    return pd.DataFrame()

@st.cache_data
def load_all_ebird_data():
    dfs = [get_ebird_data(loc) for loc in HEADWATERS_LOCATIONS]
    return pd.concat(dfs, ignore_index=True)

# === Load Data ===
checklists_df = load_checklists()
weather_df = load_weather()
ebird_df = load_all_ebird_data()

# === Sidebar Filters ===
st.sidebar.header("⏱️ Filter by Date Range")
quick_range = st.sidebar.radio("Select Range", ["Last 7 Days", "This Month", "Custom Range"], index=1)

if quick_range == "Last 7 Days":
    start_date = datetime.date.today() - datetime.timedelta(days=7)
    end_date = datetime.date.today()
elif quick_range == "This Month":
    today = datetime.date.today()
    start_date = today.replace(day=1)
    end_date = today
else:
    start_date = st.sidebar.date_input("Start Date", datetime.date(2025, 1, 1))
    end_date = st.sidebar.date_input("End Date", datetime.date.today())

# === Filtered Data ===
obs_filtered = checklists_df[
    (checklists_df["OBSERVATION DATE"] >= pd.to_datetime(start_date)) &
    (checklists_df["OBSERVATION DATE"] <= pd.to_datetime(end_date))
]

weather_filtered = weather_df[
    (weather_df["Date"] >= pd.to_datetime(start_date)) &
    (weather_df["Date"] <= pd.to_datetime(end_date))
]

# === HEADER ===
st.title("🌳 Nature Notes: Headwaters at Incarnate Word")
st.caption("Explore bird sightings and weather patterns side-by-side. Updated biweekly.")

# === Metrics ===
col1, col2, col3, col4 = st.columns(4)

# Show the highest max temp and date
max_temp_row = weather_filtered.loc[weather_filtered["Max Temp (F)"].idxmax()]
max_temp_value = max_temp_row["Max Temp (F)"]
max_temp_date = max_temp_row["Date"]

# Show the lowest min temp and date
min_temp_row = weather_filtered.loc[weather_filtered["Min Temp (F)"].idxmin()]
min_temp_value = min_temp_row["Min Temp (F)"]
min_temp_date = min_temp_row["Date"]

# Display metrics side by side
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Observations", obs_filtered["OBSERVATION COUNT"].sum())
with col2:
    st.metric("Total Species", len(obs_filtered["COMMON NAME"].unique()))
with col3:
    st.metric(label="Max Temp (°F)", value=f"{max_temp:.1f}", delta=str(max_temp_date.date()))
with col4:
    st.metric(label="Min Temp (°F)", value=f"{min_temp:.1f}", delta=str(min_temp_date.date()))    

# === Daily Species Observations ===
st.subheader("📊 Daily Species Observations")
daily_species = obs_filtered.groupby("OBSERVATION DATE")["COMMON NAME"].nunique().reset_index()
chart = alt.Chart(daily_species).mark_line().encode(
    x="OBSERVATION DATE:T",
    y=alt.Y("COMMON NAME:Q", title="Species Observed")
).properties(height=300)
st.altair_chart(chart, use_container_width=True)

# === Recent eBird Sightings ===
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

# === Weather Charts ===
st.subheader("☀️ Weather Trends")
st.line_chart(weather_filtered.set_index("Date")["Temperature Avg (F)"])
st.bar_chart(weather_filtered.set_index("Date")["Precipitation (in)"])

# === Altair Weather Trends (Detailed) ===
st.subheader("🌦️ Weather Trends (Detailed)")
expected_cols = {"Date", "temp_max", "temp_min", "precipitation"}
if expected_cols.issubset(weather_filtered.columns):
    alt_chart = alt.Chart(weather_filtered).transform_fold(
        ["temp_max", "temp_min", "precipitation"],
        as_=["Metric", "Value"]
    ).mark_line().encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Value:Q", title="Metric Value"),
        color="Metric:N"
    ).properties(height=300)
    st.altair_chart(alt_chart, use_container_width=True)
else:
    st.warning("⚠️ Skipping detailed weather chart – required columns missing.")

# === Summary Table ===
st.subheader("📋 Observation Summary")
summary = obs_filtered.groupby("COMMON NAME").agg(
    First_Seen=("OBSERVATION DATE", "min"),
    Last_Seen=("OBSERVATION DATE", "max"),
    Days_Seen=("OBSERVATION DATE", "nunique"),
    Total_Seen=("OBSERVATION COUNT", "sum")
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
