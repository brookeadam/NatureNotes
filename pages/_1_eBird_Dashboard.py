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
            return pd.DataFrame({
                "Date": pd.to_datetime(data.get("daily", {}).get("time", [])),
                "temp_max": [(t * 9/5 + 32) if t is not None else None for t in data.get("daily", {}).get("temperature_2m_max", [])],
                "temp_min": [(t * 9/5 + 32) if t is not None else None for t in data.get("daily", {}).get("temperature_2m_min", [])],
                "precipitation": [(p * 0.0393701) if p is not None else None for p in data.get("daily", {}).get("precipitation_sum", [])]
            })
        except Exception as e:
            st.error(f"Error fetching weather data: {e}")
            return pd.DataFrame(columns=["Date", "temp_max", "temp_min", "precipitation"])
    
    @st.cache_data
    def load_ebird_data_from_file():
        if EBIRD_DATA_FILE.exists():
            df = pd.read_csv(EBIRD_DATA_FILE, sep=None, engine="python", encoding="cp1252", on_bad_lines="skip")
            return clean_ebird_data(df)
        else:
            st.warning("eBird data file not found.")
            return pd.DataFrame()
    
    @st.cache_data
    def clean_ebird_data(df):
        if df.empty: 
            return df

        # Handle tab-delimited files
        if len(df.columns) == 1 and "\t" in df.columns[0]:
            df = df.iloc[:, 0].str.split("\t", expand=True)
            df.columns = [c.strip() for c in df.iloc[0]]
            df = df.iloc[1:].reset_index(drop=True)

        df.columns = [c.strip().upper() for c in df.columns]

        column_map = {
            "SPECIES": ["COMMON NAME", "SPECIES"],
            "SCIENTIFIC NAME": ["SCIENTIFIC NAME"],
            "COUNT": ["COUNT", "OBSERVATION COUNT", "HOW MANY", "NUMBER OBSERVED"],
            "DATE": ["OBSERVATION DATE", "DATE"],
            "TIME": ["TIME OBSERVATIONS STARTED", "TIME"]
        }

        resolved = {}
        for key, options in column_map.items():
            for opt in options:
                if opt in df.columns:
                    resolved[key] = opt
                    break

        # Require core columns; TIME optional
        required = ["SPECIES", "SCIENTIFIC NAME", "COUNT", "DATE"]
        if not all(k in resolved for k in required):
            return pd.DataFrame()

        # ⭐ FIX #1 — robust date parsing
        cleaned_dates = (
            df[resolved["DATE"]]
            .astype(str)
            .str.strip()
            .str.replace("T", " ", regex=False)
            .str.replace("/", "-", regex=False)
        )

        df_cleaned = pd.DataFrame({
            "Species": df[resolved["SPECIES"]],
            "Scientific Name": df[resolved["SCIENTIFIC NAME"]],
            "Date": pd.to_datetime(cleaned_dates, errors="coerce"),
            "Time": df[resolved["TIME"]] if "TIME" in resolved else None,
            "Count": pd.to_numeric(df[resolved["COUNT"]], errors="coerce").fillna(0).astype(int)
        })

        df_cleaned = df_cleaned.dropna(subset=["Date"])

        # ⭐ FIX #2 — dedupe by Date + Species
        df_cleaned = df_cleaned.drop_duplicates(subset=["Date", "Species"], keep="first")

        return df_cleaned
    
    # === HEADER ===
    st.markdown("<h1 style='text-align: center;'>🌳 Nature Notes: Headwaters at Incarnate Word 🌳</h1>", unsafe_allow_html=True)
    
    # === Data Loading ===
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
    st.write(f"**Checklist from:** {latest_date.strftime('%Y-%m-%d')}")
    st.dataframe(latest_df[["Species", "Scientific Name", "Count"]], use_container_width=True, hide_index=True)

    # === Weather ===
    weather_latest = fetch_weather_data(LATITUDE, LONGITUDE, latest_date.date(), latest_date.date())
    if not weather_latest.empty:
        st.subheader(f"Weather for {latest_date.date()}")
        st.dataframe(weather_latest, use_container_width=True, hide_index=True)

    # === Filtered View ===
    st.subheader("⏱️ Filter by Single Date Range ⏱️")
    d1 = st.date_input("Start Date", latest_date - datetime.timedelta(days=30))
    d2 = st.date_input("End Date", latest_date)
    
    filtered = ebird_df[(ebird_df["Date"] >= pd.to_datetime(d1)) & (ebird_df["Date"] <= pd.to_datetime(d2))]
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    st.subheader("⏱️ Filter by Two Date Ranges")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", MIN_DATE)
    with col2:
        end_date = st.date_input("End Date", MAX_DATE)

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

    st.dataframe(filtered[["Date", "Location", "Category", "Common Name", "Scientific Name", "Status", "Notes", "Wedge"]],
                 hide_index=True, use_container_width=True)

    st.subheader("🌡️ Weather for Filtered Range")
    weather_range = fetch_weather_data(LATITUDE, LONGITUDE, start_date, end_date)
    weather_range = weather_range.dropna(subset=["temp_max", "temp_min"])

    if not weather_range.empty:
        wc1, wc2 = st.columns(2)
        with wc1:
            max_row = weather_range.loc[weather_range["temp_max"].idxmax()]
            st.metric(f"Max Temp (°F) on {max_row['Date'].date()}", f"{max_row['temp_max']:.2f}")
        with wc2:
            min_row = weather_range.loc[weather_range["temp_min"].idxmin()]
            st.metric(f"Min Temp (°F) on {min_row['Date'].date()}", f"{min_row['temp_min']:.2f}")

        display_weather = weather_range.copy()
        display_weather["Date"] = display_weather["Date"].dt.strftime("%Y-%m-%d")
        display_weather = display_weather.rename(columns={
            "temp_max": "Max Temp °F", "temp_min": "Min Temp °F", "precipitation": "Total Precip in"
        })
        st.dataframe(display_weather, hide_index=True)

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
        dfA = df[(df["Date"].dt.date == dateA) & (df["Location"].isin(selected_locations)) & (df["Category"].isin(selected_categories))]
        dfB = df[(df["Date"].dt.date == dateB) & (df["Location"].isin(selected_locations)) & (df["Category"].isin(selected_categories))]

        merged = pd.merge(
            dfA.groupby(["Location", "Category", "Common Name", "Scientific Name"]).size().reset_index(name="Count A"),
            dfB.groupby(["Location", "Category", "Common Name", "Scientific Name"]).size().reset_index(name="Count B"),
            on=["Location", "Category", "Common Name", "Scientific Name"], how="outer"
        ).fillna(0)

        merged["Difference"] = merged["Count B"] - merged["Count A"]
        merged = merged.sort_values(sort_compare, ascending=(sort_compare_order == "Ascending"))
        st.dataframe(merged, hide_index=True, use_container_width=True)

        st.subheader("🌡️ Weather Comparison")
        w_a = fetch_weather_data(LATITUDE, LONGITUDE, dateA, dateA)
        w_b = fetch_weather_data(LATITUDE, LONGITUDE, dateB, dateB)
        
        st.write("**Date A Weather**")
        st.dataframe(w_a.rename(columns={"temp_max": "Max Temp °F", "temp_min": "Min Temp °F"}), hide_index=True)
        st.write("**Date B Weather**")
        st.dataframe(w_b.rename(columns={"temp_max": "Max Temp °F", "temp_min": "Min Temp °F"}), hide_index=True)

    st.markdown("---")
    st.subheader("📊 Compare Two Date Ranges")
    rc1, rc2 = st.columns(2)
    with rc1:
        r1_s = st.date_input("Range 1 Start", MIN_DATE, key="r1s")
        r1_e = st.date_input("Range 1 End", MAX_DATE, key="r1e")
    with rc2:
        r2_s = st.date_input("Range 2 Start", MIN_DATE, key="r2s")
        r2_e = st.date_input("Range 2 End", MAX_DATE, key="r2e")

    if st.button("Compare Ranges"):
        rangeA = df[(df["Date"] >= pd.to_datetime(r1_s)) & (df["Date"] <= pd.to_datetime(r1_e))]
        rangeB = df[(df["Date"] >= pd.to_datetime(r2_s)) & (df["Date"] <= pd.to_datetime(r2_e))]
        st.info("Range comparison logic executed.")

    
    # === Footer ===
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray;'>Nature Notes • Developed with ❤️ by Brooke Adam 🌿</div>", 
unsafe_allow_html=True)

if __name__ == "__main__":
    main()
