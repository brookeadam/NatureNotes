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

# Build merged_df for comparisons
if not ebird_df.empty:
    merged_df = ebird_df.rename(columns={
        "comName": "Species",
        "howMany": "Count",
        "obsDt": "Date"
    })
    merged_df["Date"] = pd.to_datetime(merged_df["Date"])
else:
    merged_df = pd.DataFrame(columns=["Species", "Count", "Date"])

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

# === Recent eBird Sightings ===
st.subheader("🔎 Recent eBird Sightings")
if not ebird_df.empty:
    ebird_df = ebird_df.sort_values("obsDt", ascending=False).copy()

    # Convert obsDt to datetime and format as YYYY-MM-DD
    ebird_df["obsDt"] = pd.to_datetime(ebird_df["obsDt"]).dt.strftime("%Y-%m-%d")

    table_df = ebird_df[["comName", "sciName", "howMany", "obsDt"]].rename(columns={
        "comName": "COMMON NAME",
        "sciName": "SCIENTIFIC NAME",
        "howMany": "OBSERVATION COUNT",
        "obsDt": "OBSERVATION DATE",
    })

    # Force left alignment on all columns
    styled_table = table_df.style.set_properties(**{'text-align': 'left'})

    st.dataframe(styled_table, use_container_width=True)
else:
    st.warning("No recent observations available.")

# === Species Count Comparison ==
st.subheader("📊 Species Comparison by Date Range")

col1, col2 = st.columns(2)
with col1:
    range_a = st.date_input("Select Range A", [])
with col2:
    range_b = st.date_input("Select Range B", [])

if len(range_a) == 2 and len(range_b) == 2:
    range_a_df = ebird_df[
        (ebird_df["obsDt"] >= str(range_a[0])) &
        (ebird_df["obsDt"] <= str(range_a[1]))
    ]
    range_b_df = ebird_df[
        (ebird_df["obsDt"] >= str(range_b[0])) &
        (ebird_df["obsDt"] <= str(range_b[1]))
    ]

    unique_species_a = range_a_df["comName"].nunique()
    unique_species_b = range_b_df["comName"].nunique()

    total_a = range_a_df["howMany"].sum()
    total_b = range_b_df["howMany"].sum()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Range A Unique Species", unique_species_a)
        st.metric("Range A Total Birds", total_a)
    with col2:
        st.metric("Range B Unique Species", unique_species_b)
        st.metric("Range B Total Birds", total_b)

    # 🔹 Combined summary line (left-aligned)
    st.markdown(
        f"<div style='text-align:left;'>"
        f"<b>Range A:</b> {unique_species_a} unique species, {total_a} total birds &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Range B:</b> {unique_species_b} unique species, {total_b} total birds"
        f"</div>",
        unsafe_allow_html=True
    )
else:
    st.info("Select two date ranges above to compare species.")
    
# === Altair Weather Trends (Detailed) ===
st.subheader("🌡️ Weather Data by Date Range")

if len(range_a) == 2 and len(range_b) == 2:
    weather_range_a = weather_df[
        (weather_df["date"] >= pd.to_datetime(range_a[0])) &
        (weather_df["date"] <= pd.to_datetime(range_a[1]))
    ]
    weather_range_b = weather_df[
        (weather_df["date"] >= pd.to_datetime(range_b[0])) &
        (weather_df["date"] <= pd.to_datetime(range_b[1]))
    ]

    if not weather_range_a.empty:
        st.write("### Range A Weather Data")
        st.dataframe(weather_range_a, use_container_width=True)

        max_temp_a = weather_range_a["max_temp_f"].max()
        min_temp_a = weather_range_a["min_temp_f"].min()
        precip_a = weather_range_a["precip_in"].sum()

        st.markdown(
            f"<div style='text-align:left;'>"
            f"<b>Summary (Range A):</b> Max Temp: {max_temp_a}°F, "
            f"Min Temp: {min_temp_a}°F, "
            f"Precipitation: {precip_a:.2f} in"
            f"</div>",
            unsafe_allow_html=True
        )

    if not weather_range_b.empty:
        st.write("### Range B Weather Data")
        st.dataframe(weather_range_b, use_container_width=True)

        max_temp_b = weather_range_b["max_temp_f"].max()
        min_temp_b = weather_range_b["min_temp_f"].min()
        precip_b = weather_range_b["precip_in"].sum()

        st.markdown(
            f"<div style='text-align:left;'>"
            f"<b>Summary (Range B):</b> Max Temp: {max_temp_b}°F, "
            f"Min Temp: {min_temp_b}°F, "
            f"Precipitation: {precip_b:.2f} in"
            f"</div>",
            unsafe_allow_html=True
        )
else:
    st.info("Select two date ranges above to compare detailed weather data.")
# === Footer ===
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Nature Notes for Headwaters at Incarnate Word • Developed with ❤️ by Brooke Adam and Kraken Security Operations 🌿"
    "</div>",
    unsafe_allow_html=True
)
