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
# Weather API
# ============================================================

@st.cache_data(ttl=3600)
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
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame({
            "Date": pd.to_datetime(data.get("daily", {}).get("time", [])),
            "temp_max": [(t * 9/5 + 32) if t is not None else None for t in data.get("daily", {}).get("temperature_2m_max", [])],
            "temp_min": [(t * 9/5 + 32) if t is not None else None for t in data.get("daily", {}).get("temperature_2m_min", [])],
            "precipitation": [(p * 0.0393701) if p is not None else None for p in data.get("daily", {}).get("precipitation_sum", [])]
        })
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {e}")
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

weather_latest = fetch_weather_data(LATITUDE, LONGITUDE, latest_date.date(), latest_date.date())
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
    st.dataframe(
        display_latest_weather[["Max Temp °F", "Min Temp °F", "Total Precip in"]],
        hide_index=True
    )
else:
    st.warning("No weather data available for the latest observation date.")

# ============================================================
# Filter by Date Range + Location + Category + Weather
# ============================================================

st.subheader("⏱️ Filter by Date Range")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", MIN_DATE, min_value=MIN_DATE, max_value=MAX_DATE)
with col2:
    end_date = st.date_input("End Date", MAX_DATE, min_value=MIN_DATE, max_value=MAX_DATE)

st.subheader("🏞️ Filter by Location")
locations = sorted(df["Location"].dropna().unique())
selected_locations = st.multiselect(
    "Choose one or more locations:",
    options=locations,
    default=locations
)

st.subheader("🌱 Filter by Category")
categories = sorted(df["Category"].dropna().unique())
selected_categories = st.multiselect(
    "Choose one or more categories:",
    options=categories,
    default=categories
)

filtered = df[
    (df["Date"] >= pd.to_datetime(start_date)) &
    (df["Date"] <= pd.to_datetime(end_date)) &
    (df["Location"].isin(selected_locations)) &
    (df["Category"].isin(selected_categories))
].copy()

sort_col = st.selectbox("Sort by", ["Date", "Location", "Category", "Common Name"])
sort_order = st.radio("Order", ["Ascending", "Descending"], horizontal=True)

filtered = filtered.sort_values(sort_col, ascending=(sort_order == "Ascending"))

st.dataframe(
    filtered[["Date", "Location", "Category", "Common Name", "Scientific Name", "Status", "Notes", "Wedge"]],
    hide_index=True,
    use_container_width=True
)

st.subheader("🌡️ Weather Metrics for Filtered Range")

weather_range = fetch_weather_data(LATITUDE, LONGITUDE, start_date, end_date)
weather_range = weather_range.dropna(subset=["temp_max", "temp_min"])

if not weather_range.empty:
    col1, col2 = st.columns(2)
    with col1:
        max_row = weather_range.loc[weather_range["temp_max"].idxmax()]
        st.metric(
            label=f"Max Temp (°F) on {max_row['Date'].date()}",
            value=f"{max_row['temp_max']:.2f}"
        )
    with col2:
        min_row = weather_range.loc[weather_range["temp_min"].idxmin()]
        st.metric(
            label=f"Min Temp (°F) on {min_row['Date'].date()}",
            value=f"{min_row['temp_min']:.2f}"
        )

    st.subheader("Daily Weather Data (Filtered Range)")
    display_weather = weather_range.copy()
    display_weather["Date"] = display_weather["Date"].dt.strftime("%Y-%m-%d")
    display_weather = display_weather.rename(columns={
        "temp_max": "Max Temp °F",
        "temp_min": "Min Temp °F",
        "precipitation": "Total Precip in"
    })
    st.dataframe(
        display_weather.style.set_properties(**{'text-align': 'left'}).format(
            {
                "Max Temp °F": "{:.2f}",
                "Min Temp °F": "{:.2f}",
                "Total Precip in": "{:.4f}"
            }
        ),
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("No weather data available for the selected date range.")

# ============================================================
# Compare Two Dates + Weather
# ============================================================

st.markdown("---")
st.subheader("📝 Compare Specific Dates")

unique_dates = sorted(df["Date"].dt.date.unique(), reverse=True)

colA, colB = st.columns(2)
with colA:
    dateA = st.selectbox("Select Date A", unique_dates)
with colB:
    dateB = st.selectbox("Select Date B", unique_dates)

if st.button("Compare Dates"):
    dfA = df[df["Date"].dt.date == dateA]
    dfB = df[df["Date"].dt.date == dateB]

    st.subheader("Phenology Comparison")
    merged_pheno = pd.merge(
        dfA.groupby(["Category", "Common Name"]).size().reset_index(name="Count A"),
        dfB.groupby(["Category", "Common Name"]).size().reset_index(name="Count B"),
        on=["Category", "Common Name"],
        how="outer"
    ).fillna(0)
    merged_pheno["Difference"] = merged_pheno["Count B"] - merged_pheno["Count A"]

    st.dataframe(
        merged_pheno.sort_values("Difference", ascending=False),
        hide_index=True,
        use_container_width=True
    )

    st.subheader("🌡️ Weather Comparison")

    weather_a = fetch_weather_data(LATITUDE, LONGITUDE, dateA, dateA)
    weather_b = fetch_weather_data(LATITUDE, LONGITUDE, dateB, dateB)

    if not weather_a.empty:
        max_row_a = weather_a.loc[weather_a["temp_max"].idxmax()]
        min_row_a = weather_a.loc[weather_a["temp_min"].idxmin()]
        total_precip_a = weather_a["precipitation"].sum()
        st.write(
            f"**Weather Summary: Date A ({dateA}):** "
            f"Max Temp: {max_row_a['temp_max']:.2f}°F, "
            f"Min Temp: {min_row_a['temp_min']:.2f}°F, "
            f"Total Precip: {total_precip_a:.4f} in"
        )
        disp_a = weather_a.copy()
        disp_a["Date"] = disp_a["Date"].dt.strftime("%Y-%m-%d")
        disp_a = disp_a.rename(columns={
            "temp_max": "Max Temp °F",
            "temp_min": "Min Temp °F",
            "precipitation": "Total Precip in"
        })
        st.dataframe(
            disp_a.style.set_properties(**{'text-align': 'left'}).format(
                {
                    "Max Temp °F": "{:.2f}",
                    "Min Temp °F": "{:.2f}",
                    "Total Precip in": "{:.4f}"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(f"No weather data available for Date A ({dateA}).")

    if not weather_b.empty:
        max_row_b = weather_b.loc[weather_b["temp_max"].idxmax()]
        min_row_b = weather_b.loc[weather_b["temp_min"].idxmin()]
        total_precip_b = weather_b["precipitation"].sum()
        st.write(
            f"**Weather Summary: Date B ({dateB}):** "
            f"Max Temp: {max_row_b['temp_max']:.2f}°F, "
            f"Min Temp: {min_row_b['temp_min']:.2f}°F, "
            f"Total Precip: {total_precip_b:.4f} in"
        )
        disp_b = weather_b.copy()
        disp_b["Date"] = disp_b["Date"].dt.strftime("%Y-%m-%d")
        disp_b = disp_b.rename(columns={
            "temp_max": "Max Temp °F",
            "temp_min": "Min Temp °F",
            "precipitation": "Total Precip in"
        })
        st.dataframe(
            disp_b.style.set_properties(**{'text-align': 'left'}).format(
                {
                    "Max Temp °F": "{:.2f}",
                    "Min Temp °F": "{:.2f}",
                    "Total Precip in": "{:.4f}"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(f"No weather data available for Date B ({dateB}).")

# ============================================================
# Compare Two Date Ranges + Weather
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

if st.button("Compare Ranges"):
    A = df[(df["Date"] >= pd.to_datetime(r1_start)) & (df["Date"] <= pd.to_datetime(r1_end))]
    B = df[(df["Date"] >= pd.to_datetime(r2_start)) & (df["Date"] <= pd.to_datetime(r2_end))]

    st.subheader("Phenology Range Comparison")

    tableA = A.groupby(["Category", "Common Name"]).size().reset_index(name="Count A")
    tableB = B.groupby(["Category", "Common Name"]).size().reset_index(name="Count B")

    merged_ranges = pd.merge(tableA, tableB, on=["Category", "Common Name"], how="outer").fillna(0)
    merged_ranges["Difference"] = merged_ranges["Count B"] - merged_ranges["Count A"]

    st.dataframe(
        merged_ranges.sort_values("Difference", ascending=False),
        hide_index=True,
        use_container_width=True
    )

    st.subheader("🌡️ Weather Trends (Ranges)")

    weather_a = fetch_weather_data(LATITUDE, LONGITUDE, r1_start, r1_end)
    weather_b = fetch_weather_data(LATITUDE, LONGITUDE, r2_start, r2_end)

    if not weather_a.empty:
        max_row_a = weather_a.loc[weather_a["temp_max"].idxmax()]
        min_row_a = weather_a.loc[weather_a["temp_min"].idxmin()]
        total_precip_a = weather_a["precipitation"].sum()
        st.write(
            f"**Weather Summary: Range A ({r1_start}–{r1_end}):** "
            f"Max Temp: {max_row_a['temp_max']:.2f}°F on {max_row_a['Date'].strftime('%Y-%m-%d')}, "
            f"Min Temp: {min_row_a['temp_min']:.2f}°F on {min_row_a['Date'].strftime('%Y-%m-%d')}, "
            f"Total Precip: {total_precip_a:.4f} in"
        )
        disp_a = weather_a.copy()
        disp_a["Date"] = disp_a["Date"].dt.strftime("%Y-%m-%d")
        disp_a = disp_a.rename(columns={
            "temp_max": "Max Temp °F",
            "temp_min": "Min Temp °F",
            "precipitation": "Total Precip in"
        })
        st.dataframe(
            disp_a.style.set_properties(**{'text-align': 'left'}).format(
                {
                    "Max Temp °F": "{:.2f}",
                    "Min Temp °F": "{:.2f}",
                    "Total Precip in": "{:.4f}"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No weather data for Range A.")

    if not weather_b.empty:
        max_row_b = weather_b.loc[weather_b["temp_max"].idxmax()]
        min_row_b = weather_b.loc[weather_b["temp_min"].idxmin()]
        total_precip_b = weather_b["precipitation"].sum()
        st.write(
            f"**Weather Summary: Range B ({r2_start}–{r2_end}):** "
            f"Max Temp: {max_row_b['temp_max']:.2f}°F on {max_row_b['Date'].strftime('%Y-%m-%d')}, "
            f"Min Temp: {min_row_b['temp_min']:.2f}°F on {min_row_b['Date'].strftime('%Y-%m-%d')}, "
            f"Total Precip: {total_precip_b:.4f} in"
        )
        disp_b = weather_b.copy()
        disp_b["Date"] = disp_b["Date"].dt.strftime("%Y-%m-%d")
        disp_b = disp_b.rename(columns={
            "temp_max": "Max Temp °F",
            "temp_min": "Min Temp °F",
            "precipitation": "Total Precip in"
        })
        st.dataframe(
            disp_b.style.set_properties(**{'text-align': 'left'}).format(
                {
                    "Max Temp °F": "{:.2f}",
                    "Min Temp °F": "{:.2f}",
                    "Total Precip in": "{:.4f}"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No weather data for Range B.")

# ============================================================
# Footer
# ============================================================

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:gray;'>Headwaters Phenology Dashboard • Built with ❤️ by Brooke 🌿</div>",
    unsafe_allow_html=True
)
