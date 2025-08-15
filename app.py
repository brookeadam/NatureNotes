import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# -----------------------------
# CONFIG
# -----------------------------
EBIRD_API_KEY = "c49o0js5vkjb"
LOCATION_IDS = ["L1210588", "L1210849"]

# -----------------------------
# WEATHER FETCH FUNCTION (Open-Meteo)
# -----------------------------
def fetch_weather_data(lat, lon, start, end):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "auto"
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Check if "daily" exists in response
    if "daily" not in data or not data["daily"].get("time"):
        return pd.DataFrame(columns=["Date", "Max Temp (°F)", "Min Temp (°F)", "Precipitation (in)"])

    return pd.DataFrame({
        "Date": data["daily"]["time"],
        "Max Temp (°F)": [t * 9/5 + 32 for t in data["daily"]["temperature_2m_max"]],
        "Min Temp (°F)": [t * 9/5 + 32 for t in data["daily"]["temperature_2m_min"]],
        "Precipitation (in)": [p / 25.4 for p in data["daily"]["precipitation_sum"]]
    })

# -----------------------------
# EBIRD FETCH
# -----------------------------
def fetch_ebird_data(loc_id, start_date, end_date):
    url = f"https://api.ebird.org/v2/data/obs/{loc_id}/historic/{start_date.strftime('%Y/%m/%d')}"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        df = pd.DataFrame(response.json())
        if not df.empty:
            df["locId"] = loc_id
        return df
    return pd.DataFrame()

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("Nature Notes Dashboard")
start_date = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=30))
end_date = st.sidebar.date_input("End Date", datetime.now())

# -----------------------------
# WEATHER DATA (API instead of CSV)
# -----------------------------
weather_df = fetch_weather_data(
    lat=29.4689,
    lon=-98.4794,
    start=start_date,
    end=end_date
)

# -----------------------------
# EBIRD DATA
# -----------------------------
ebird_data = []
for loc in LOCATION_IDS:
    df = fetch_ebird_data(loc, start_date, end_date)
    if not df.empty:
        ebird_data.append(df)

if ebird_data:
    ebird_df = pd.concat(ebird_data)
else:
    ebird_df = pd.DataFrame()

# -----------------------------
# DISPLAY
# -----------------------------
st.title("Nature Notes: Headwaters at Incarnate Word")

st.subheader("Weather Trends")
if not weather_df.empty:
    st.line_chart(weather_df.set_index("Date")[["Max Temp (°F)", "Min Temp (°F)"]])
    st.bar_chart(weather_df.set_index("Date")[["Precipitation (in)"]])
else:
    st.write("No weather data available.")

st.subheader("Bird Observations")
if not ebird_df.empty:
    st.write(f"Total observations: {len(ebird_df)}")
    st.dataframe(ebird_df)
else:
    st.write("No bird observation data available.")

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.markdown(
    "Headwaters at Incarnate Word • Nature Notes Dashboard"
)
