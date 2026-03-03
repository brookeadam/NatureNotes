import streamlit as st
import pandas as pd
import requests
import datetime

# ============================================================
# Constants
# ============================================================

LATITUDE = 29.4689
LONGITUDE = -98.4798

# ============================================================
# Helpers
# ============================================================

def to_date(x):
    """Safely convert various date-like objects to a Python date."""
    if isinstance(x, datetime.datetime):
        return x.date()
    if isinstance(x, datetime.date):
        return x
    return pd.to_datetime(x).date()

# ============================================================
# Weather API
# ============================================================

@st.cache_data(ttl=3600)
def fetch_weather_data(lat, lon, start, end):
    start = to_date(start)
    end = to_date(end)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "America/Chicago"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame({
            "Date": pd.to_datetime(data.get("daily", {}).get("time", [])),
            "temp_max": [(t * 9/5 + 32) if t is not None else None for t in data.get("daily", {}).get("temperature_2m_max", [])],
            "temp_min": [(t * 9/5 + 32) if t is not None else None for t in data.get("daily", {}).get("temperature_2m_min", [])],
            "precipitation": [(p * 0.0393701) if p is not None else None for p in data.get("daily", {}).get("precipitation_sum", [])]
        })

        return df

    except Exception as e:
        st.error(f"Weather API error: {e}")
        return pd.DataFrame(columns=["Date", "temp_max", "temp_min", "precipitation"])

# ============================================================
# Load & Clean Phenology Data
# ============================================================

@st.cache_data
def load_pheno_data():
    df = pd.read_csv("historical_pheno_data.csv", encoding="utf-8", on_bad_lines="skip")

    df.columns = [c.strip().upper() for c in df.columns]

    required = ["OBSERVATIONDATETIME", "LOCATION", "WEDGE", "CATEGORY",
                "COMMONNAME", "SCIENTIFICNAME", "STATUS", "NOTES"]

    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {missing}")
        return pd.DataFrame()

    df["OBSERVATIONDATETIME"] = pd.to_datetime(df["OBSERVATIONDATETIME"], errors="coerce")
    df = df.dropna(subset=["OBSERVATIONDATETIME"])

    df = df.rename(columns={
        "OBSERVATIONDATETIME": "Date",
        "COMMONNAME": "Common Name",
        "SCIENTIFICNAME": "Scientific Name",
        "CATEGORY": "Category",
        "LOCATION": "Location",
        "STATUS": "Status",
        "NOTES": "Notes",
        "WEDGE": "Wedge"
    })

    return df

# ============================================================
# Page Setup
# ============================================================

st.set_page_config(page_title="Headwaters Phenology Dashboard", layout="wide")

st.markdown("<h1 style='text-align:center;'>🌿 Headwaters Phenology Dashboard 🌿</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center;color:gray;'>Plants • Wildlife • Pollinators</h4>", unsafe_allow_html=True)

df = load_pheno_data()
if df.empty:
    st.stop()

MIN_DATE = df["Date"].min().date()
MAX_DATE = df["Date"].max().date()

# ============================================================
# Latest Observations + Weather
# ============================================================

st.subheader("🆕 Latest Observations")

latest_date = df["Date"].max()
latest_df = df[df["Date"] == latest_date].copy()

st.write(f"**Latest observation date:** {latest_date.strftime('%Y-%m-%d')}")

st.dataframe(
    latest_df[["Location", "Category", "Common Name", "Scientific Name", "Status", "Notes", "Wedge"]],
    hide_index=True,
    use_container_width=True
)

weather_latest = fetch_weather_data(LATITUDE, LONGITUDE, latest_date, latest_date)
weather_latest = weather_latest.dropna(subset=["temp_max", "temp_min"])

if not weather_latest.empty:
    st.subheader(f"Weather for {latest_date.date()}")
    display_latest_weather = weather_latest.copy()
    display_latest_weather["Date"] = display_latest_weather["Date"].dt.strftime("%Y-%m-%d")
    display_latest_weather = display_latest_weather.rename(columns={
        "temp_max": "Max Temp °F",
        "temp_min": "Min Temp °F",
        "precipitation": "Total Precip in"
    })
    st.dataframe(display_latest_weather, hide_index=True)
else:
    st.warning("No weather data available for the latest observation date.")

# ============================================================
# Filter Section
# ============================================================

st.subheader("⏱️ Filter by Date Range")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", MIN_DATE)
with col2:
    end_date = st.date_input("End Date", MAX_DATE)

st.subheader("🏞️ Filter by Location")
locations = sorted(df["Location"].dropna().unique())
selected_locations = st.multiselect("Choose locations:", locations, default=locations)

st.subheader("🌱 Filter by Category")
categories = sorted(df["Category"].dropna().unique())
selected_categories = st.multiselect("Choose categories:", categories, default=categories)

st.subheader("🔍 Filter by Name")
common_search = st.text_input("Search Common Name")
scientific_search = st.text_input("Search Scientific Name")

filtered = df[
    (df["Date"] >= pd.to_datetime(start_date)) &
    (df["Date"] <= pd.to_datetime(end_date)) &
    (df["Location"].isin(selected_locations)) &
    (df["Category"].isin(selected_categories))
].copy()

if common_search:
    filtered = filtered[filtered["Common Name"].str.contains(common_search, case=False, na=False)]

if scientific_search:
    filtered = filtered[filtered["Scientific Name"].str.contains(scientific_search, case=False, na=False)]

sort_col = st.selectbox("Sort by", ["Date", "Location", "Category", "Common Name", "Scientific Name"])
sort_order = st.radio("Order", ["Ascending", "Descending"], horizontal=True)

filtered = filtered.sort_values(sort_col, ascending=(sort_order == "Ascending"))

st.dataframe(
    filtered[["Date", "Location", "Category", "Common Name", "Scientific Name", "Status", "Notes", "Wedge"]],
    hide_index=True,
    use_container_width=True
)

# ============================================================
# Weather for Filtered Range
# ============================================================

st.subheader("🌡️ Weather for Filtered Range")

weather_range = fetch_weather_data(LATITUDE, LONGITUDE, start_date, end_date)
weather_range = weather_range.dropna(subset=["temp_max", "temp_min"])

if not weather_range.empty:
    col1, col2 = st.columns(2)
    with col1:
        max_row = weather_range.loc[weather_range["temp_max"].idxmax()]
        st.metric(f"Max Temp (°F) on {max_row['Date'].date()}", f"{max_row['temp_max']:.2f}")
    with col2:
        min_row = weather_range.loc[weather_range["temp_min"].idxmin()]
        st.metric(f"Min Temp (°F) on {min_row['Date'].date()}", f"{min_row['temp_min']:.2f}")

    display_weather = weather_range.copy()
    display_weather["Date"] = display_weather["Date"].dt.strftime("%Y-%m-%d")
    display_weather = display_weather.rename(columns={
        "temp_max": "Max Temp °F",
        "temp_min": "Min Temp °F",
        "precipitation": "Total Precip in"
    })

    st.dataframe(display_weather, hide_index=True)
else:
    st.warning("No weather data available for this range.")

# ============================================================
# Compare Specific Dates (with filters + scientific name + sorting)
# ============================================================

st.markdown("---")
st.subheader("📝 Compare Specific Dates")

unique_dates = sorted(df["Date"].dt.date.unique(), reverse=True)

colA, colB = st.columns(2)
with colA:
    dateA = st.selectbox("Select Date A", unique_dates)
with colB:
    dateB = st.selectbox("Select Date B", unique_dates)

sort_compare = st.selectbox("Sort comparison by", ["Category", "Common Name", "Scientific Name", "Location"])
sort_compare_order = st.radio("Comparison order", ["Ascending", "Descending"], horizontal=True)

if st.button("Compare Dates"):
    dfA = df[
        (df["Date"].dt.date == dateA) &
        (df["Location"].isin(selected_locations)) &
        (df["Category"].isin(selected_categories))
    ]
    dfB = df[
        (df["Date"].dt.date == dateB) &
        (df["Location"].isin(selected_locations)) &
        (df["Category"].isin(selected_categories))
    ]

    merged = pd.merge(
        dfA.groupby(["Location", "Category", "Common Name", "Scientific Name"]).size().reset_index(name="Count A"),
        dfB.groupby(["Location", "Category", "Common Name", "Scientific Name"]).size().reset_index(name="Count B"),
        on=["Location", "Category", "Common Name", "Scientific Name"],
        how="outer"
    ).fillna(0)

    merged["Difference"] = merged["Count B"] - merged["Count A"]
    merged = merged.sort_values(sort_compare, ascending=(sort_compare_order == "Ascending"))

    st.dataframe(merged, hide_index=True, use_container_width=True)

    st.subheader("🌡️ Weather Comparison")

    weather_a = fetch_weather_data(LATITUDE, LONGITUDE, dateA, dateA)
    weather_b = fetch_weather_data(LATITUDE, LONGITUDE, dateB, dateB)

    st.write("**Date A Weather**")
    st.dataframe(weather_a, hide_index=True)

    st.write("**Date B Weather**")
    st.dataframe(weather_b, hide_index=True)

# ============================================================
# Compare Two Date Ranges (with filters + scientific name + sorting)
# ============================================================

st.markdown("---")
st.subheader("📊 Compare Two Date Ranges")

col1, col2 = st.columns(2)
with col1:
    r1_start = st.date_input("Range 1 Start", MIN_DATE, key="r1s")
    r1_end = st.date_input("Range 1 End", MAX_DATE, key="r1e")
with col2:
    r2_start = st.date_input("Range 2 Start", MIN_DATE, key="r2s")
    r2_end = st.date_input("Range 2 End", MAX_DATE, key="r2e")

sort_range = st.selectbox("Sort range comparison by", ["Category", "Common Name", "Scientific Name", "Location"])
sort_range_order = st.radio("Range comparison order", ["Ascending", "Descending"], horizontal=True)

if st.button("Compare Ranges"):
    A = df[
        (df["Date"] >= pd.to_datetime(r1_start)) &
        (df["Date"] <= pd.to_datetime(r1_end)) &
        (df["Location"].isin(selected_locations)) &
        (df["Category"].isin(selected_categories))
    ]
    B = df[
        (df["Date"] >= pd.to_datetime(r2_start)) &
        (df["Date"] <= pd.to_datetime(r2_end)) &
        (df["Location"].isin(selected_locations)) &
        (df["Category"].isin(selected_categories))
    ]

    merged_ranges = pd.merge(
        A.groupby(["Location", "Category", "Common Name", "Scientific Name"]).size().reset_index(name="Count A"),
        B.groupby(["Location", "Category", "Common Name", "Scientific Name"]).size().reset_index(name="Count B"),
        on=["Location", "Category", "Common Name", "Scientific Name"],
        how="outer"
    ).fillna(0)

    merged_ranges["Difference"] = merged_ranges["Count B"] - merged_ranges["Count A"]
    merged_ranges = merged_ranges.sort_values(sort_range, ascending=(sort_range_order == "Ascending"))

    st.dataframe(merged_ranges, hide_index=True, use_container_width=True)

    st.subheader("🌡️ Weather Trends")

    weather_a = fetch_weather_data(LATITUDE, LONGITUDE, r1_start, r1_end)
    weather_b = fetch_weather_data(LATITUDE, LONGITUDE, r2_start, r2_end)

    st.write("**Range A Weather**")
    st.dataframe(weather_a, hide_index=True)

    st.write("**Range B Weather**")
    st.dataframe(weather_b, hide_index=True)

# ============================================================
# Footer
# ============================================================

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:gray;'>Headwaters Phenology Dashboard • Built with ❤️ by Brooke 🌿</div>",
    unsafe_allow_html=True
)
