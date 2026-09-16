import streamlit as st
import pandas as pd
import requests
import datetime
from pathlib import Path

def main():
    # === Constants ===
    EBIRD_DATA_FILE = Path("historical_checklists.csv")
    LATITUDE = 29.4689
    LONGITUDE = -98.4798
    MIN_DATE = datetime.date(1985, 1, 1)
    MAX_DATE = datetime.date(2035, 12, 31)

    # === Load eBird data ===
    @st.cache_data
    def load_ebird_data_from_file():
        if not EBIRD_DATA_FILE.exists():
            st.error("eBird data file not found.")
            return pd.DataFrame()

        # Tab-delimited, with proper headers
        df = pd.read_csv(
            EBIRD_DATA_FILE,
            sep="\t",
            engine="python",
            dtype=str
        )

        return clean_ebird_data(df)

    @st.cache_data
    def clean_ebird_data(df: pd.DataFrame) -> pd.DataFrame:
        # Normalize column names
        cols = {c.strip().upper(): c for c in df.columns}

        def get(colnames):
            for name in colnames:
                if name in cols:
                    return cols[name]
            return None

        col_guid = get(["GLOBAL UNIQUE IDENTIFIER"])
        col_common = get(["COMMON NAME"])
        col_sci = get(["SCIENTIFIC NAME"])
        col_count = get(["COUNT", "OBSERVATION COUNT"])
        col_date = get(["OBSERVATION DATE", "DATE"])
        col_time = get(["TIME OBSERVATIONS STARTED", "TIME"])

        required = [col_common, col_sci, col_count, col_date]
        if any(c is None for c in required):
            st.error("Required columns not found in eBird file.")
            return pd.DataFrame()

        # Build cleaned frame
        out = pd.DataFrame()
        out["Species"] = df[col_common]
        out["Scientific Name"] = df[col_sci]

        # Parse count
        out["Count"] = pd.to_numeric(df[col_count], errors="coerce").fillna(0).astype(int)

        # Parse date (and optional time)
        if col_time is not None:
            dt_str = df[col_date].astype(str) + " " + df[col_time].astype(str)
            out["Date"] = pd.to_datetime(dt_str, errors="coerce", infer_datetime_format=True)
        else:
            out["Date"] = pd.to_datetime(df[col_date].astype(str), errors="coerce", infer_datetime_format=True)

        # Drop invalid dates
        out = out.dropna(subset=["Date"])

        # Deduplicate by Date + Species
        out = out.drop_duplicates(subset=["Date", "Species"], keep="first")

        return out

    # === Weather ===
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
            r = requests.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            df = pd.DataFrame({
                "Date": pd.to_datetime(data["daily"]["time"]).dt.strftime("%Y-%m-%d"),
                "temp_max": [(t * 9/5 + 32) for t in data["daily"]["temperature_2m_max"]],
                "temp_min": [(t * 9/5 + 32) for t in data["daily"]["temperature_2m_min"]],
                "precipitation": [(p * 0.0393701) for p in data["daily"]["precipitation_sum"]]
            })
            return df
        except Exception:
            return pd.DataFrame()

    # === Header ===
    st.markdown("<h1 style='text-align: center;'>🌳 Nature Notes: Headwaters at Incarnate Word 🌳</h1>", unsafe_allow_html=True)

    # === Load data ===
    ebird_df = load_ebird_data_from_file()
    if ebird_df.empty:
        st.error("No eBird data found after cleaning.")
        return

    # === Latest checklist ===
    st.subheader("🆕 Latest Checklist 🆕")
    latest_date = ebird_df["Date"].max()
    latest_df = ebird_df[ebird_df["Date"] == latest_date].copy()
    latest_df_display = latest_df.copy()
    latest_df_display["Date"] = latest_df_display["Date"].dt.strftime("%Y-%m-%d")

    st.write(f"**Checklist from:** {latest_date.strftime('%Y-%m-%d')}")
    st.dataframe(
        latest_df_display[["Species", "Scientific Name", "Count"]],
        use_container_width=True,
        hide_index=True
    )

    # === Weather for latest date ===
    weather_latest = fetch_weather_data(
        LATITUDE, LONGITUDE,
        latest_date.date(),
        latest_date.date()
    )
    if not weather_latest.empty:
        st.subheader(f"Weather for {latest_date.strftime('%Y-%m-%d')}")
        st.dataframe(weather_latest, use_container_width=True, hide_index=True)

    # === Single range filter ===
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

    # === Two-range + name filter ===
    st.subheader("⏱️ Filter by Two Date Ranges")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date (full range)", MIN_DATE)
    with col2:
        end_date = st.date_input("End Date (full range)", MAX_DATE)

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

    st.dataframe(
        filtered2_display[["Date", "Species", "Scientific Name", "Count"]],
        hide_index=True,
        use_container_width=True
    )

    # === Weather for filtered range ===
    st.subheader("🌡️ Weather for Filtered Range")
    safe_start = max(start_date, datetime.date(2000, 1, 1))
    safe_end = min(end_date, datetime.date.today())
    weather_range = fetch_weather_data(LATITUDE, LONGITUDE, safe_start, safe_end)
    if not weather_range.empty:
        st.dataframe(weather_range, hide_index=True)

    # === Compare specific dates ===
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
            on=["Species", "Scientific Name"],
            how="outer"
        ).fillna(0)

        merged["Difference"] = merged["Count B"] - merged["Count A"]
        merged = merged.sort_values(sort_compare, ascending=(sort_compare_order == "Ascending"))

        st.dataframe(merged, hide_index=True, use_container_width=True)

    # === Footer ===
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>Nature Notes • Developed with ❤️ by Brooke Adam 🌿</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
