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
            df = pd.read_csv(
                EBIRD_DATA_FILE,
                sep=None,
                engine="python",
                encoding="cp1252",
                on_bad_lines="skip"
            )
            return clean_ebird_data(df)
        else:
            st.warning("eBird data file not found.")
            return pd.DataFrame()
    
    @st.cache_data
    def clean_ebird_data(df):
        if df.empty:
            return df

        # --- Handle tab-delimited files ---
        if len(df.columns) == 1 and "\t" in df.columns[0]:
            df = df.iloc[:, 0].str.split("\t", expand=True)
            df.columns = [c.strip() for c in df.iloc[0]]
            df = df.iloc[1:].reset_index(drop=True)

        # --- Normalize column names ---
        df.columns = [c.strip().upper() for c in df.columns]

        # --- Flexible column resolver ---
        def resolve_column(possible_names):
            for name in possible_names:
                if name in df.columns:
                    return name
            return None

        col_species = resolve_column(["SPECIES", "COMMON NAME"])
        col_sci = resolve_column(["SCIENTIFIC NAME"])
        col_count = resolve_column(["COUNT", "OBSERVATION COUNT", "HOW MANY", "NUMBER OBSERVED"])
        col_date = resolve_column(["DATE", "OBSERVATION DATE", "CHECKLIST DATE"])
        col_time = resolve_column(["TIME", "TIME OBSERVATIONS STARTED", "START TIME"])

        if not all([col_species, col_sci, col_count, col_date]):
            st.error("Could not resolve required columns. Columns found:")
            st.write(df.columns.tolist())
            return pd.DataFrame()

        # --- Clean date column aggressively ---
        date_series = (
            df[col_date]
            .astype(str)
            .str.strip()
            .str.replace("T", " ", regex=False)
            .str.replace("/", "-", regex=False)
            .str.replace(r"[^\w\s\-:]", "", regex=True)
        )

        parsed_dates = pd.to_datetime(date_series, errors="coerce")

        df_cleaned = pd.DataFrame({
            "Species": df[col_species].astype(str).str.strip(),
            "Scientific Name": df[col_sci].astype(str).str.strip(),
            "Date": parsed_dates,
            "Count": pd.to_numeric(df[col_count], errors="coerce").fillna(0).astype(int)
        })

        df_cleaned = df_cleaned.dropna(subset=["Date"])

        # --- Normalize species fields to ensure dedupe works ---
        df_cleaned["Species"] = df_cleaned["Species"].str.upper()
        df_cleaned["Scientific Name"] = df_cleaned["Scientific Name"].str.upper()

        # --- Remove duplicates: one species per date ---
        df_cleaned = df_cleaned.drop_duplicates(
            subset=["Date", "Species"],
            keep="first"
        )

        return df_cleaned
    
    # === HEADER ===
    st.markdown(
        "<h1 style='text-align: center;'>🌳 Nature Notes: Headwaters at Incarnate Word 🌳</h1>",
        unsafe_allow_html=True
    )
    
    # === Data Loading ===
    ebird_df = load_ebird_data_from_file()
    
    if ebird_df.empty:
        st.error("No eBird data found.")
        return

    # === Latest Checklist ===
    st.subheader("🆕 Latest Checklist 🆕")
    latest_date = ebird_df["Date"].max()

    latest_df = ebird_df[ebird_df["Date"] == latest_date].copy()
    latest_df = latest_df.drop_duplicates(subset=["Species"], keep="first")

    st.write(f"**Checklist from:** {latest_date.strftime('%Y-%m-%d')}")
    st.dataframe(
        latest_df[["Species", "Scientific Name", "Count"]],
        use_container_width=True,
        hide_index=True
    )

    # === Weather ===
    weather_latest = fetch_weather_data(LATITUDE, LONGITUDE, latest_date.date(), latest_date.date())
    if not weather_latest.empty:
        st.subheader(f"Weather for {latest_date.date()}")
        st.dataframe(weather_latest, use_container_width=True, hide_index=True)

    # === Filtered View ===
    st.subheader("⏱️ Filter by Single Date Range ⏱️")
    d1 = st.date_input("Start Date", latest_date - datetime.timedelta(days=30))
    d2 = st.date_input("End Date", latest_date)
    
    filtered = ebird_df[
        (ebird_df["Date"] >= pd.to_datetime(d1)) &
        (ebird_df["Date"] <= pd.to_datetime(d2))
    ]

    filtered = filtered.drop_duplicates(subset=["Date", "Species"], keep="first")

    st.dataframe(filtered, use_container_width=True, hide_index=True)

    # === Comparison Section ===
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>📊 Comparison Between Dates</h2>", unsafe_allow_html=True)

    available_dates = sorted(ebird_df["Date"].dt.date.unique(), reverse=True)

    if len(available_dates) >= 2:
        date_a = available_dates[1]
        date_b = available_dates[0]

        st.markdown(
            f"<p style='text-align: center;'>Comparing <b>{date_a}</b> (A) vs <b>{date_b}</b> (B)</p>",
            unsafe_allow_html=True
        )

        df_a = ebird_df[ebird_df["Date"].dt.date == date_a].copy()
        df_b = ebird_df[ebird_df["Date"].dt.date == date_b].copy()

        df_a = df_a.drop_duplicates(subset=["Species"], keep="first")
        df_b = df_b.drop_duplicates(subset=["Species"], keep="first")

        df_a_grouped = df_a.groupby("Species")["Count"].sum()
        df_b_grouped = df_b.groupby("Species")["Count"].sum()

        comp_df = pd.DataFrame({
            f"Count ({date_a})": df_a_grouped,
            f"Count ({date_b})": df_b_grouped
        }).fillna(0)

        comp_df["Difference"] = comp_df[f"Count ({date_b})"] - comp_df[f"Count ({date_a})"]

        _, cent_col, _ = st.columns([1, 6, 1])
        with cent_col:
            st.dataframe(
                comp_df.sort_values("Difference", ascending=False),
                use_container_width=True,
                hide_index=True
            )

    # === Footer ===
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>Nature Notes • Developed with ❤️ by Brooke Adam 🌿</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
