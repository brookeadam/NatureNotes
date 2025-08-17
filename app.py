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

# === Species Count Comparison ===
st.markdown("## 📊 Species and Weather Comparison by Date Range")

col1, col2 = st.columns(2)
with col1:
    range1_start = st.date_input("Range 1 Start")
    range1_end = st.date_input("Range 1 End")
with col2:
    range2_start = st.date_input("Range 2 Start")
    range2_end = st.date_input("Range 2 End")

if st.button("Compare Species and Weather") and range1_start and range1_end and range2_start and range2_end:
    # Save date ranges to session state
    st.session_state["range_a"] = (pd.to_datetime(range1_start), pd.to_datetime(range1_end))
    st.session_state["range_b"] = (pd.to_datetime(range2_start), pd.to_datetime(range2_end))

    # Filter bird data
    range_a_birds = merged_df[(merged_df["Date"] >= st.session_state["range_a"][0]) &
                              (merged_df["Date"] <= st.session_state["range_a"][1])]
    range_b_birds = merged_df[(merged_df["Date"] >= st.session_state["range_b"][0]) &
                              (merged_df["Date"] <= st.session_state["range_b"][1])]

    # Summary stats
    unique_species_a = range_a_birds["Species"].nunique()
    unique_species_b = range_b_birds["Species"].nunique()
    total_birds_a = range_a_birds["Count"].sum()
    total_birds_b = range_b_birds["Count"].sum()

    st.markdown("### 🔢 Bird Summary")
    st.write(f"**Range A:** {unique_species_a} unique species, {total_birds_a} total birds")
    st.write(f"**Range B:** {unique_species_b} unique species, {total_b_b} total birds")

    # Species comparison table
    table_a = range_a_birds.groupby("Species")["Count"].sum().reset_index()
    table_b = range_b_birds.groupby("Species")["Count"].sum().reset_index()

    col_a = f"Birds {range1_start}–{range1_end}"
    col_b = f"Birds {range2_start}–{range2_end}"
    table_a.rename(columns={"Count": col_a}, inplace=True)
    table_b.rename(columns={"Count": col_b}, inplace=True)

    comparison_df = pd.merge(table_a, table_b, on="Species", how="outer").fillna(0)
    comparison_df["Difference"] = comparison_df[col_b] - comparison_df[col_a]

    st.markdown("### 🐦 Species Comparison Table")
    st.dataframe(comparison_df)

# === Altair Weather Trends (Detailed) ===
st.subheader("🌦️ Weather Trends (Detailed)")

# Make sure range_a and range_b exist before trying to use them
if "range_a" in locals() and "range_b" in locals() and range_a and range_b:
    # Filter weather data for each date range
    weather_range_a = weather_df[
        (weather_df["date"] >= range_a[0]) & (weather_df["date"] <= range_a[1])
    ]
    weather_range_b = weather_df[
        (weather_df["date"] >= range_b[0]) & (weather_df["date"] <= range_b[1])
    ]

    if not weather_range_a.empty:
        st.markdown("**Range A Weather Data**")
        st.dataframe(weather_range_a.reset_index(drop=True), use_container_width=True)

        # Summary line for Range A
        summary_a = {
            "Max Temp (°F)": weather_range_a["tmax"].max(),
            "Min Temp (°F)": weather_range_a["tmin"].min(),
            "Precipitation (in)": weather_range_a["prcp"].sum(),
        }
        st.write("**Summary (Range A):**", summary_a)

    if not weather_range_b.empty:
        st.markdown("**Range B Weather Data**")
        st.dataframe(weather_range_b.reset_index(drop=True), use_container_width=True)

        # Summary line for Range B
        summary_b = {
            "Max Temp (°F)": weather_range_b["tmax"].max(),
            "Min Temp (°F)": weather_range_b["tmin"].min(),
            "Precipitation (in)": weather_range_b["prcp"].sum(),
        }
        st.write("**Summary (Range B):**", summary_b)

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
