import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px

# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(
    page_title="Nature Notes: Headwaters",
    page_icon="🌿",
    layout="wide"
)

# --------------------------
# TITLE
# --------------------------
st.title("🌳 Nature Notes: Headwaters at Incarnate Word")
st.caption("Explore bird sightings and weather patterns side-by-side. Updated biweekly.")

# --------------------------
# DATE FILTERS
# --------------------------
today = datetime.today().date()
last_7_days = today - timedelta(days=7)
first_of_month = today.replace(day=1)

filter_option = st.sidebar.radio("⏱️ Filter by Date Range", ["Last 7 Days", "This Month", "Custom Range"])

if filter_option == "Last 7 Days":
    start_date = last_7_days
    end_date = today
elif filter_option == "This Month":
    start_date = first_of_month
    end_date = today
else:
    start_date = st.sidebar.date_input("Start Date", value=last_7_days)
    end_date = st.sidebar.date_input("End Date", value=today)

# --------------------------
# FETCH WEATHER DATA FROM OPEN-METEO
# --------------------------
def fetch_weather_data(lat, lon, start, end):
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={start}&end_date={end}"
        "&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum"
        "&temperature_unit=fahrenheit&timezone=auto"
    )
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame({
        "Date": pd.to_datetime(data["daily"]["time"]),
        "Temperature Max (F)": data["daily"]["temperature_2m_max"],
        "Temperature Min (F)": data["daily"]["temperature_2m_min"],
        "Temperature Avg (F)": data["daily"]["temperature_2m_mean"],
        "Precipitation (in)": [p * 0.0393701 for p in data["daily"]["precipitation_sum"]]
    })
    return df

# Fetch historical weather for San Antonio (Headwaters)
weather_df = fetch_weather_data(
    lat=29.4689,
    lon=-98.4833,
    start=start_date,
    end=end_date
)

# --------------------------
# WEATHER FILTERING
# --------------------------
weather_filtered = weather_df[
    (weather_df["Date"].dt.date >= start_date) &
    (weather_df["Date"].dt.date <= end_date)
]

st.subheader("🛠️ Filtered Weather Data")
if not weather_filtered.empty:
    st.dataframe(weather_filtered)
else:
    st.write("No weather data available for the selected date range.")

# --------------------------
# WEATHER METRICS
# --------------------------
if not weather_filtered.empty:
    max_temp = weather_filtered["Temperature Max (F)"].max()
    max_temp_date = weather_filtered.loc[weather_filtered["Temperature Max (F)"].idxmax(), "Date"]

    min_temp = weather_filtered["Temperature Min (F)"].min()
    min_temp_date = weather_filtered.loc[weather_filtered["Temperature Min (F)"].idxmin(), "Date"]

    st.metric(label="Max Temp (F)", value=f"{max_temp:.1f}", delta=str(max_temp_date.date()))
    st.metric(label="Min Temp (F)", value=f"{min_temp:.1f}", delta=str(min_temp_date.date()))

# --------------------------
# WEATHER CHARTS
# --------------------------
if not weather_filtered.empty:
    st.subheader("☀️ Weather Trends")
    fig_temp = px.line(weather_filtered, x="Date", y="Temperature Avg (F)", title="Average Daily Temperature (F)")
    st.plotly_chart(fig_temp, use_container_width=True)

    st.subheader("🌦️ Weather Trends (Detailed)")
    fig_temp_detail = px.line(weather_filtered, x="Date", y=["Temperature Max (F)", "Temperature Min (F)"],
                              title="Daily Max & Min Temperatures (F)")
    st.plotly_chart(fig_temp_detail, use_container_width=True)

# --------------------------
# EBIRD DATA SECTION (unchanged)
# --------------------------
# Placeholder for eBird data fetching code
st.subheader("📊 Daily Species Observations")
st.write("Coming soon: eBird species observations here...")

st.subheader("🔎 Recent eBird Sightings")
st.write("No recent observations available.")

st.subheader("📋 Observation Summary")
st.caption("Nature Notes for Headwaters at Incarnate Word • Developed with ❤️ by Brooke Adam and Kraken Security Operations 🌿")
