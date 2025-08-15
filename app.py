import streamlit as st
import pandas as pd
import requests
import altair as alt
import datetime

# === Constants ===
EBIRD_API_KEY = "c49o0js5vkjb"
HEADWATERS_LOCATIONS = ["L1210588", "L1210849"]

st.set_page_config(page_title="Nature Notes @ Headwaters", layout="wide")

# === API Fetch: Weather (Open-Meteo) ===
@st.cache_data
def fetch_weather_data(lat, lon, start, end):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "America/Chicago"
    }
    response = requests.get(url, params=params)
    data = response.json()

    return pd.DataFrame({
        "Date": pd.to_datetime(data.get("daily", {}).get("time", [])),
        "temp_max": [
            (t * 9/5 + 32) if t is not None else None
            for t in data.get("daily", {}).get("temperature_2m_max", [])
        ],
        "temp_min": [
            (t * 9/5 + 32) if t is not None else None
            for t in data.get("daily", {}).get("temperature_2m_min", [])
        ],
        "precipitation": [
            (p * 0.0393701) if p is not None else None
            for p in data.get("daily", {}).get("precipitation_sum", [])
        ]
    })

# === API Fetch: eBird ===
@st.cache_data
def fetch_ebird_data(loc_id, start_date):
    url = f"https://api.ebird.org/v2/data/obs/{loc_id}/historic/{start_date.strftime('%Y/%m/%d')}"
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    return pd.DataFrame()

@st.cache_data
def load_all_ebird_data(start_date, end_date):
    dfs = []
    date_range = pd.date_range(start_date, end_date)
    for loc in HEADWATERS_LOCATIONS:
        for date in date_range:
            df = fetch_ebird_data(loc, date)
            if not df.empty:
                dfs.append(df)
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

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

# === Load Data from APIs ===
weather_df = fetch_weather_data(29.4689, -98.4794, start_date, end_date)
ebird_df = load_all_ebird_data(start_date, end_date)

# === HEADER ===
st.title("🌳 Nature Notes: Headwaters at Incarnate Word")
st.caption("Explore bird sightings and weather patterns side-by-side. Updated biweekly.")

# === Weather Metrics ===
weather_filtered = weather_df[
    (weather_df["Date"] >= pd.to_datetime(start_date)) &
    (weather_df["Date"] <= pd.to_datetime(end_date))
]

if not weather_filtered.empty:
    weather_filtered = weather_filtered.dropna(subset=["temp_max", "temp_min"])

    if not weather_filtered.empty:
        max_temp_row = weather_filtered.loc[weather_filtered["temp_max"].idxmax()]
        max_temp = max_temp_row["temp_max"]
        max_temp_date = max_temp_row["Date"]

        min_temp_row = weather_filtered.loc[weather_filtered["temp_min"].idxmin()]
        min_temp = min_temp_row["temp_min"]
        min_temp_date = min_temp_row["Date"]

        st.metric(label="Max Temp (F)", value=f"{max_temp:.1f}", delta=str(max_temp_date.date()))
        st.metric(label="Min Temp (F)", value=f"{min_temp:.1f}", delta=str(min_temp_date.date()))
    else:
        st.warning("No valid temperature data in selected range.")
else:
    st.warning("No weather data available for the selected date range.")   

# === Daily Species Observations ===
if not ebird_df.empty:
    ebird_df["obsDt"] = pd.to_datetime(ebird_df["obsDt"])
    obs_filtered = ebird_df[
        (ebird_df["obsDt"].dt.date >= start_date) &
        (ebird_df["obsDt"].dt.date <= end_date)
    ]
    daily_species = obs_filtered.groupby(obs_filtered["obsDt"].dt.date)["comName"].nunique().reset_index()
    daily_species.columns = ["OBSERVATION DATE", "Species Observed"]

    st.subheader("📊 Daily Species Observations")
    chart = alt.Chart(daily_species).mark_line().encode(
        x="OBSERVATION DATE:T",
        y=alt.Y("Species Observed:Q", title="Species Observed")
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)
else:
    st.warning("No bird observation data available.")

# === Recent eBird Sightings ===
st.subheader("🔎 Recent eBird Sightings")
if not ebird_df.empty:
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
if "precipitation" in weather_filtered.columns:
    st.bar_chart(weather_filtered.set_index("Date")["precipitation"])
else:
    st.warning("Precipitation data not available.")

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

# === Footer ===
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Nature Notes for Headwaters at Incarnate Word • Developed with ❤️ by Brooke Adam and Kraken Security Operations 🌿"
    "</div>",
    unsafe_allow_html=True
)
