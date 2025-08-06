import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import datetime
from io import StringIO
from PIL import Image

# === CONFIG ===
st.set_page_config(page_title="Nature Notes – Headwaters", layout="wide")
st.title("🪶 Nature Notes – Headwaters at Incarnate Word")
st.markdown("_Live updates from Headwaters at Incarnate Word using eBird and local weather records._")

# === CONSTANTS ===
CHECKLIST_PATH = "historical_checklists.csv"
WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
LATITUDE = 29.4649
LONGITUDE = -98.4693
EBIRD_LOC_IDS = ["L1210588", "L1210849"]
EBIRD_API_KEY = "c49o0js5vkjb"

# === HELPERS ===
@st.cache_data
def load_checklist():
    return pd.read_csv(CHECKLIST_PATH, encoding="utf-8", parse_dates=["OBSERVATION DATE"])

@st.cache_data
def get_weather_data(start_date, end_date):
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": ["temperature_2m_min", "temperature_2m_max", "precipitation_sum"],
        "timezone": "auto"
    }
    r = requests.get(WEATHER_URL, params=params)
    r.raise_for_status()
    data = r.json()
    return pd.DataFrame({
        "date": data["daily"]["time"],
        "temp_min": data["daily"]["temperature_2m_min"],
        "temp_max": data["daily"]["temperature_2m_max"],
        "precip": data["daily"]["precipitation_sum"],
    })

@st.cache_data
def get_species_image(common_name):
    search_url = f"https://api.ebird.org/v2/ref/media/obs/{common_name.replace(' ', '%20')}"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    try:
        r = requests.get(search_url, headers=headers)
        if r.ok:
            results = r.json()
            for item in results:
                if "assets" in item and item["assets"]:
                    return item["assets"][0].get("url")
    except:
        return None
    return None

# === DATE SELECTION ===
today = datetime.date.today()
season_start = datetime.date(today.year, 3, 1) if today.month < 6 else datetime.date(today.year, 6, 1)
date_filter = st.sidebar.radio(
    "Select Date Range",
    ["Today", "Last 7 Days", "This Month", "This Season", "Custom Range"]
)

if date_filter == "Today":
    start_date = end_date = today
elif date_filter == "Last 7 Days":
    start_date = today - datetime.timedelta(days=6)
    end_date = today
elif date_filter == "This Month":
    start_date = today.replace(day=1)
    end_date = today
elif date_filter == "This Season":
    start_date = season_start
    end_date = today
else:
    start_date = st.sidebar.date_input("Start Date", value=today - datetime.timedelta(days=7))
    end_date = st.sidebar.date_input("End Date", value=today)

# === LOAD DATA ===
df = load_checklist()
df = df[(df["OBSERVATION DATE"] >= pd.to_datetime(start_date)) & (df["OBSERVATION DATE"] <= pd.to_datetime(end_date))]

# === METRICS ===
species_count = df["COMMON NAME"].nunique()
total_birds = df["OBSERVATION COUNT"].sum()
st.markdown("### 📊 Summary Metrics")
col1, col2 = st.columns(2)
col1.metric("Unique Species Observed", species_count)
col2.metric("Total Bird Count", total_birds)

# === WEATHER CHART ===
weather_df = get_weather_data(start_date, end_date)
fig = px.line(
    weather_df,
    x="date",
    y=["temp_min", "temp_max"],
    title="📈 Temperature Range",
    labels={"value": "°C", "date": "Date"},
)
st.plotly_chart(fig, use_container_width=True)

# === SPECIES LIST ===
st.markdown("### 🐦 Species Observed")
grouped = df.groupby("COMMON NAME").agg({
    "OBSERVATION COUNT": "sum",
    "SCIENTIFIC NAME": "first"
}).reset_index().sort_values("OBSERVATION COUNT", ascending=False)

for _, row in grouped.iterrows():
    with st.expander(f"{row['COMMON NAME']} ({int(row['OBSERVATION COUNT'])} birds)"):
        st.markdown(f"_Scientific name_: **{row['SCIENTIFIC NAME']}**")
        img_url = get_species_image(row["COMMON NAME"])
        if img_url:
            st.image(img_url, width=300, caption=row["COMMON NAME"])

# === COMPARISON TOOL PLACEHOLDER ===
st.markdown("### 🔄 Comparison Tool (Coming Soon)")
st.info("You’ll soon be able to compare species counts and weather metrics between two different date ranges.")

# === FOOTER ===
st.markdown("---")
st.markdown(
    """
    **Headwaters at Incarnate Word**  
    _A sanctuary in the heart of San Antonio dedicated to ecological education and stewardship._  
    Data provided by [eBird](https://ebird.org) and [Open-Meteo](https://open-meteo.com).
    """
)
