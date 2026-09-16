import streamlit as st
import pandas as pd
import requests
import altair as alt
import datetime
from pathlib import Path
from dateutil.relativedelta import relativedelta

def main():
    # === Constants ===
    HEADWATERS_LOCATIONS = ["L1210588", "L1210849"]
    LATITUDE = 29.4689
    LONGITUDE = -98.4798
    DATA_DIR = Path("data")
    EBIRD_DATA_FILE = Path("historical_checklists.csv")
    
    # === API Fetch Functions ===
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
            df = pd.DataFrame({
                "Date": pd.to_datetime(data.get("daily", {}).get("time", [])),
                "temp_max": [(t * 9/5 + 32) if t is not None else None for t in data.get("daily", {}).get("temperature_2m_max", [])],
                "temp_min": [(t * 9/5 + 32) if t is not None else None for t in data.get("daily", {}).get("temperature_2m_min", [])],
                "precipitation": [(p * 0.0393701) if p is not None else None for p in data.get("daily", {}).get("precipitation_sum", [])]
            })
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
            return df
        except Exception as e:
            st.error(f"Error fetching weather data: {e}")
            return pd.DataFrame(columns=["Date", "temp_max", "temp_min", "precipitation"])
    
    # === Load eBird Data ===
    @st.cache_data
    def load_ebird_data_from_file():
        if EBIRD_DATA_FILE.exists():
            # Your file is space-delimited, not comma-delimited
            df = pd.read_csv(
                EBIRD_DATA_FILE,
                delim_whitespace=True,
                header=None,
                names=[
                    "GUID",
                    "Species",
                    "Scientific Name",
                    "Count",
                    "Location",
                    "Date",
                    "Time",
                    "Observer",
                    "Protocol",
                    "Duration",
                    "Distance",
                    "NumObservers"
                ],
                engine="python"
            )
            return clean_ebird_data(df)
        else:
            st.warning("eBird data file not found.")
            return pd.DataFrame()
    
    # === Clean eBird Data ===
    @st.cache_data
    def clean_ebird_data(df):
        # Parse dates
        df["Date"] = pd.to_datetime(
            df["Date"].astype(str),
            errors="coerce",
            infer_datetime_format=True
        )

        # Drop invalid dates
        df = df.dropna(subset=["Date"])

        # Convert Count to int
        df["Count"] = pd.to_numeric(df["Count"], errors="coerce").fillna(0).astype(int)

        # Deduplicate by Date + Species
        df = df.drop_duplicates(subset=["Date", "Species"], keep="first")

        return df
    
    # === HEADER ===
    st.markdown("<h1 style='text-align: center;'>🌳 Nature Notes: Headwaters at Incarnate Word 🌳</h1>", unsafe_allow_html=True)
    
    # === Load Data ===
    MIN_DATE = datetime.date(1985, 1, 1)
    MAX_DATE = datetime.date(2035, 12, 31)
    ebird_df = load_ebird_data_from_file()
    
    if ebird_df.empty:
        st.error("No eBird data found.")
        return

    # === Latest Checklist ===
    st.subheader("🆕 Latest Checklist 🆕")
    latest_date = ebird_df["Date"].max()
    latest_df = ebird_df[ebird_df["Date"] == latest_date].copy()

    latest_df_display = latest_df.copy()
    latest_df_display["Date"] = latest_df_display["Date"].dt.strftime("%Y-%m-%d")

    st.write(f"**Checklist from:** {latest_date.strftime('%Y-%m-%d')}")
    st.dataframe(latest_df_display[["Species", "Scientific Name", "Count"]], use_container_width=True, hide_index=True)

    # === Weather for Latest Date ===
    weather_latest = fetch_weather_data(
        LATITUDE, LONGITUDE,
        latest_date.date(),
        latest_date.date()
    )

    if not weather_latest.empty:
        st.subheader(f"Weather for {latest_date.strftime('%Y-%m-%d')}")
        st.dataframe(weather_latest, use_container_width=True, hide_index=True)

    # === Filter by Single Date Range ===
    st.subheader("⏱️ Filter by Single Date Range ⏱️")
    d1 = st.date_input("Start Date", latest_date.date() - datetime.timedelta(days=30))
    d2 = st.date_input("End Date", latest_date.date())

    filtered = ebird_df[
        (ebird_df["Date"] >= pd.to_datetime(d1)) &
        (ebird_df["Date"] <= pd.to_datetime(d2))
    ].copy()

    filtered_display = filtered.copy()
    filtered_display["Date"] = filtered_display["Date"].dt.strftime("%Y-%m-%d")

    st.dataframe(filtered_display, use_container_width=True, hide_index=True)

    # === Filter by Two Date Ranges ===
    st.subheader("⏱️ Filter by Two Date Ranges")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", MIN_DATE)
    with col2:
        end_date = st.date_input("End Date", MAX_DATE)

    st.subheader("🔍 Filter by Name")
    common_search = st.text_input("Search Common Name")
    scientific_search = st.text_input("Search Scientific Name")

    filtered2 = ebird_df[
        (ebird_df["Date"] >= pd.to_datetime(start_date)) &
        (ebird_df["Date"] <= pd.to_datetime(end_date))
    ].copy()

    if common_search:
        filtered2 = filtered2[filtered2["Species"].str.contains(common_search, case=False, na=False)]
    if scientific_search:
        filtered2 = filtered2[filtered2["Scientific Name"].str.contains(scientific_search, case=False, na=False)]

    filtered2_display = filtered2.copy()
    filtered2_display["Date"] = filtered2_display["Date"].dt.strftime("%Y-%m-%d")

    sort_col = st.selectbox("Sort by", ["Date", "Species", "Scientific Name", "Count"])
    sort_order = st.radio("Order", ["Ascending", "Descending"], horizontal=True)
    filtered2_display = filtered2_display.sort_values(sort_col, ascending=(sort_order == "Ascending"))

    st.dataframe(filtered2_display[["Date", "Species", "Scientific Name", "Count"]],
                 hide_index=True, use_container_width=True)

    # === Weather for Filtered Range ===
    st.subheader("🌡️ Weather for Filtered Range")

    safe_start = max(start_date, datetime.date(2000, 1, 1))
    safe_end = min(end_date, datetime.date.today())

    weather_range = fetch_weather_data(LATITUDE, LONGITUDE, safe_start, safe_end)

    if not weather_range.empty:
        st.dataframe(weather_range, hide_index=True)

    # === Compare Specific Dates ===
    st.markdown("---")
    st.subheader("📝 Compare Specific Dates")
    unique_dates = sorted(ebird_df["Date"].dt.date.unique(), reverse=True)
    colA, colB = st.columns(2)
    with colA:
        dateA = st.selectbox("Select Date A", unique_dates)
    with colB:
        dateB = st.selectbox("Select Date B", unique_dates)

    sort_compare = st.selectbox("Sort comparison by", ["Species", "Scientific Name", "Count"])
    sort_compare_order = st.radio("Comparison order", ["Ascending", "Descending"], horizontal=True)

    if st.button("Compare Dates"):
        dfA = ebird_df[ebird_df["Date"].dt.date == dateA]
        dfB = ebird_df[ebird_df["Date"].dt.date == dateB]

        merged = pd.merge(
            dfA.groupby(["Species", "Scientific Name"])["Count"].sum().reset_index(name="Count A"),
            dfB.groupby(["Species", "Scientific Name"])["Count"].sum().reset_index(name="Count B"),
            on=["Species", "Scientific Name"], how="outer"
        ).fillna(0)

        merged["Difference"] = merged["Count B"] - merged["Count A"]
        merged = merged.sort_values(sort_compare, ascending=(sort_compare_order == "Ascending"))

        st.dataframe(merged, hide_index=True, use_container_width=True)

    # === Footer ===
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray;'>Nature Notes • Developed with ❤️ by Brooke Adam 🌿</div>", 
unsafe_allow_html=True)

if __name__ == "__main__":
    main()
