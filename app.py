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
    
# === Species Count Comparison ===
st.markdown("## 📊 Species Comparison by Date Range")

col1, col2 = st.columns(2)
with col1:
    start_a = st.date_input("Start Date (Range A)", pd.to_datetime("2023-08-01"))
    end_a = st.date_input("End Date (Range A)", pd.to_datetime("2023-08-31"))
with col2:
    start_b = st.date_input("Start Date (Range B)", pd.to_datetime("2025-08-01"))
    end_b = st.date_input("End Date (Range B)", pd.to_datetime("2025-08-31"))

if st.button("Compare Species"):
    
    # Filter data
    range_a = merged_df[(merged_df["Date"] >= pd.to_datetime(start_a)) & (merged_df["Date"] <= pd.to_datetime(end_a))]
    range_b = merged_df[(merged_df["Date"] >= pd.to_datetime(start_b)) & (merged_df["Date"] <= pd.to_datetime(end_b))]

    # Unique species counts
    unique_species_a = range_a["Species"].nunique()
    unique_species_b = range_b["Species"].nunique()

    # Total bird counts
    total_birds_a = range_a["Count"].sum()
    total_birds_b = range_b["Count"].sum()

    # Bird count per species
    table_a = range_a.groupby("Species")["Count"].sum().reset_index()
    table_b = range_b.groupby("Species")["Count"].sum().reset_index()

    # Rename columns based on selected date ranges
    col_a = f"Birds {start_a.strftime('%b %Y')}–{end_a.strftime('%b %Y')}"
    col_b = f"Birds {start_b.strftime('%b %Y')}–{end_b.strftime('%b %Y')}"
    table_a.rename(columns={"Count": col_a}, inplace=True)
    table_b.rename(columns={"Count": col_b}, inplace=True)

    # Merge
    comparison_df = pd.merge(table_a, table_b, on="Species", how="outer").fillna(0)

    # Calculate difference
    comparison_df["Difference"] = comparison_df[col_b] - comparison_df[col_a]

    # Sort: increases on top, decreases on bottom
    comparison_df = comparison_df.sort_values("Difference", ascending=False)

    # Color coding
    def highlight_diff(val):
        if val > 0:
            return "background-color: lightgreen"
        elif val < 0:
            return "background-color: lightcoral"
        else:
            return "background-color: white"

    # Display summary
    st.markdown("### 🔢 Summary")
    st.write(f"**Range A:** {unique_species_a} unique species, {total_birds_a} total birds")
    st.write(f"**Range B:** {unique_species_b} unique species, {total_birds_b} total birds")

    # Display comparison table
    st.markdown("### 🐦 Species Comparison Table")
    st.dataframe(comparison_df.style.applymap(highlight_diff, subset=["Difference"]))

# === Recent eBird Sightings ===
# === Recent eBird Sightings ===
st.subheader("🔎 Recent eBird Sightings")
if not ebird_df.empty:
    ebird_df = ebird_df.sort_values("obsDt", ascending=False)
    table_df = (
        ebird_df[["comName", "sciName", "howMany", "obsDt"]]
        .rename(columns={
            "comName": "COMMON NAME",
            "sciName": "SCIENTIFIC NAME",
            "howMany": "OBSERVATION COUNT",
            "obsDt": "OBSERVATION DATE",
        })
        .reset_index(drop=True)
    )

    # Use st.table instead of st.dataframe to hide the index
    st.table(table_df)
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
