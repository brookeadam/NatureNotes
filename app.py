import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from meteomatics import MeteomaticsAPI  # If you're using Meteomatics (optional)

# --- CONFIG ---
st.set_page_config(page_title="Nature Notes", layout="wide")

# --- FUNCTIONS ---
def fetch_weather_data(lat, lon, start, end):
    """Fetch historical weather data from Open-Meteo API."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "America/Chicago",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # Ensure we have valid precipitation data
    precip_data = data.get("daily", {}).get("precipitation_sum", [])
    precip_inches = [
        (p * 0.0393701 if isinstance(p, (int, float)) else None) for p in precip_data
    ]

    return pd.DataFrame({
        "Date": pd.to_datetime(data["daily"]["time"]),
        "Max Temp (F)": [t * 9/5 + 32 for t in data["daily"]["temperature_2m_max"]],
        "Min Temp (F)": [t * 9/5 + 32 for t in data["daily"]["temperature_2m_min"]],
        "Precipitation (in)": precip_inches
    })

# --- DATE RANGE FILTER ---
st.subheader("⏱️ Filter by Date Range")
date_filter = st.selectbox("Select Range", ["Last 7 Days", "This Month", "Custom Range"])

if date_filter == "Last 7 Days":
    end_date = datetime.today()
    start_date = end_date - timedelta(days=6)
elif date_filter == "This Month":
    end_date = datetime.today()
    start_date = datetime(end_date.year, end_date.month, 1)
else:
    start_date = st.date_input("Start Date", datetime.today() - timedelta(days=30))
    end_date = st.date_input("End Date", datetime.today())
    if start_date > end_date:
        st.error("Start date must be before end date.")

# --- FETCH WEATHER ---
weather_df = fetch_weather_data(
    lat=29.4689,
    lon=-98.4799,
    start=start_date,
    end=end_date
)

# --- DISPLAY WEATHER ---
st.title("🌳 Nature Notes: Headwaters at Incarnate Word")
st.write("Explore bird sightings and weather patterns side-by-side. Updated biweekly.")

st.subheader("🛠️ Filtered Weather Data")
if not weather_df.empty:
    st.dataframe(weather_df)
else:
    st.warning("No weather data available for the selected date range.")

# --- WEATHER TRENDS ---
if not weather_df.empty:
    fig, ax = plt.subplots()
    ax.plot(weather_df["Date"], weather_df["Max Temp (F)"], label="Max Temp (F)", color="red")
    ax.plot(weather_df["Date"], weather_df["Min Temp (F)"], label="Min Temp (F)", color="blue")
    ax.set_xlabel("Date")
    ax.set_ylabel("Temperature (°F)")
    ax.legend()
    st.pyplot(fig)

# --- FOOTER ---
st.markdown(
    "<div style='text-align:center; font-size:14px;'>Nature Notes for Headwaters at Incarnate Word • Developed with ❤️ by Brooke Adam and Kraken Security Operations 🌿</div>",
    unsafe_allow_html=True
)
