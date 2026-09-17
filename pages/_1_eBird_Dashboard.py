import streamlit as st
import pandas as pd
import requests
import altair as alt
import datetime
import re
from pathlib import Path

def main():
    HEADWATERS_LOCATIONS = ["L1210588", "L1210849"]
    LATITUDE = 29.4689
    LONGITUDE = -98.4798
    DATA_DIR = Path("data")
    EBIRD_DATA_FILE = Path("historical_checklists.csv")

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
        except Exception:
            return pd.DataFrame(columns=["Date", "temp_max", "temp_min", "precipitation"])

    @st.cache_data
    def load_ebird_data_from_file():
        if EBIRD_DATA_FILE.exists():
            df = pd.read_csv(
                EBIRD_DATA_FILE,
                sep=",",
                engine="python",
                dtype=str
            )
            return clean_ebird_data(df)
        else:
            return pd.DataFrame()

    @st.cache_data
    def clean_ebird_data(df):
        df.columns = [str(c).replace("\ufeff", "").strip().upper() for c in df.columns]

        def col(*names):
            for n in names:
                if n in df.columns:
                    return n
            return None

        col_common = col("COMMON NAME")
        col_sci = col("SCIENTIFIC NAME")
        col_count = col("OBSERVATION COUNT", "COUNT")
        col_date = col("OBSERVATION DATE", "DATE")
        col_time = col("TIME OBSERVATIONS STARTED", "TIME")

        out = pd.DataFrame()
        out["Species"] = df[col_common]
        out["Scientific Name"] = df[col_sci]
        out["Count"] = pd.to_numeric(df[col_count], errors="coerce").fillna(0).astype(int)

        dates = df[col_date].astype(str)

        time_pattern = re.compile(r"\d{1,2}:\d{2}:\d{2}\s*(AM|PM)", re.IGNORECASE)
        times = []

        if col_time:
            for raw in df[col_time]:
                raw = str(raw) if raw is not None else ""
                m = time_pattern.search(raw)
                if m:
                    times.append(m.group(0))
                else:
                    times.append("")
        else:
            times = [""] * len(df)

        parsed = []
        for d, t in zip(dates, times):
            try:
                if t:
                    parsed.append(pd.to_datetime(f"{d} {t}", errors="coerce"))
                else:
                    parsed.append(pd.to_datetime(d, errors="coerce"))
            except:
                parsed.append(pd.NaT)

        out["Date"] = parsed
        out = out.dropna(subset=["Date"])
        out = out.drop_duplicates(subset=["Date", "Species"], keep="first")

        return out

    st.markdown("<h1 style='text-align: center;'>🌳 Nature Notes: Headwaters at Incarnate Word 🌳</h1>", unsafe_allow_html=True)

    MIN_DATE = datetime.date(1985, 1, 1)
    MAX_DATE = datetime.date(2035, 12, 31)
    ebird_df = load_ebird_data_from_file()

    if ebird_df.empty:
        st.error("No eBird data found.")
        return

    st.subheader("🆕 Latest Checklist 🆕")
    latest_date = ebird_df["Date"].max()
    latest_df = ebird_df[ebird_df["Date"] == latest_date].copy()

    latest_df_display = latest_df.copy()
    latest_df_display["Date"] = latest_df_display["Date"].dt.strftime("%Y-%m-%d")

    st.write(f"**Checklist from:** {latest_date.strftime('%Y-%m-%d')}")
    st.dataframe(latest_df_display[["Species", "Scientific Name", "Count"]], use_container_width=True, hide_index=True)

    weather_latest = fetch_weather_data(
        LATITUDE, LONGITUDE,
        latest_date.date(),
        latest_date.date()
    )

    if not weather_latest.empty:
        st.subheader(f"Weather for {latest_date.strftime('%Y-%m-%d')}")
        st.dataframe(weather_latest, use_container_width=True, hide_index=True)

    st.subheader("⏱️ Filter by Single Date Range ⏱️")
    d1 = st.date_input("Start Date", latest_date.date() - datetime.timedelta(days=30))
    d2 = st.date_input("End Date", latest_date.date())

    filtered = ebird_df[
        (ebird_df["Date"] >= pd.to_datetime(d1)) &
        (ebird_df["Date"] <= pd.to_datetime(d2))
    ].copy()

    filtered_display = filtered.copy()
    filtered_display["Date"] = filtered_display["Date"].dt.strftime("%Y-%m-%d")

    # ⭐ ONLY CHANGE YOU REQUESTED ⭐
    st.dataframe(
        filtered_display[["Date", "Species", "Scientific Name", "Count"]],
        use_container_width=True,
        hide_index=True
    )

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

    st.subheader("🌡️ Weather for Filtered Range")

    safe_start = max(start_date, datetime.date(2000, 1, 1))
    safe_end = min(end_date, datetime.date.today())

    weather_range = fetch_weather_data(LATITUDE, LONGITUDE, safe_start, safe_end)

    if not weather_range.empty:
        st.dataframe(weather_range, hide_index=True)

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

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray;'>Nature Notes • Developed with ❤️ by Brooke Adam 🌿</div>",
                unsafe_allow_html=True)

if __name__ == "__main__":
    main()
