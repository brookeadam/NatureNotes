import streamlit as st
import pandas as pd
import requests
import datetime
from pathlib import Path

def main():
    EBIRD_DATA_FILE = Path("historical_checklists.csv")
    LATITUDE = 29.4689
    LONGITUDE = -98.4798
    MIN_DATE = datetime.date(1985, 1, 1)
    MAX_DATE = datetime.date(2035, 12, 31)

    @st.cache_data
    def load_ebird_data_from_file():
        if not EBIRD_DATA_FILE.exists():
            st.error("eBird data file not found.")
            return pd.DataFrame()

        # Your fixed file is TAB-delimited
        df = pd.read_csv(
            EBIRD_DATA_FILE,
            sep="\t",
            engine="python",
            dtype=str
        )

        return clean_ebird_data(df)

    @st.cache_data
    def clean_ebird_data(df):

        # Normalize column names
        df.columns = [c.strip().upper() for c in df.columns]

        def col(*names):
            for n in names:
                if n in df.columns:
                    return n
            return None

        col_common = col("COMMON NAME")
        col_sci = col("SCIENTIFIC NAME")
        col_count = col("COUNT", "OBSERVATION COUNT")
        col_date = col("OBSERVATION DATE", "DATE")
        col_time = col("TIME OBSERVATIONS STARTED", "TIME")

        # Build output
        out = pd.DataFrame()
        out["Species"] = df[col_common]
        out["Scientific Name"] = df[col_sci]
        out["Count"] = pd.to_numeric(df[col_count], errors="coerce").fillna(0).astype(int)

        # Robust datetime parsing
        dates = df[col_date].astype(str)

        if col_time:
            times = df[col_time].astype(str)
        else:
            times = [""] * len(df)

        parsed = []
        for d, t in zip(dates, times):
            # Remove trailing junk like "possible Broad-Winged Hawk"
            t_clean = t.split()[0] if ":" in t else ""

            try:
                if t_clean:
                    parsed.append(pd.to_datetime(f"{d} {t_clean}", errors="coerce"))
                else:
                    parsed.append(pd.to_datetime(d, errors="coerce"))
            except:
                parsed.append(pd.NaT)

        out["Date"] = parsed
        out = out.dropna(subset=["Date"])

        # Deduplicate
        out = out.drop_duplicates(subset=["Date", "Species"], keep="first")

        return out

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
        except:
            return pd.DataFrame()

    # === UI ===
    st.markdown("<h1 style='text-align: center;'>🌳 Nature Notes: Headwaters at Incarnate Word 🌳</h1>", unsafe_allow_html=True)

    ebird_df = load_ebird_data_from_file()
    if ebird_df.empty:
        st.error("No eBird data found after cleaning.")
        return

    # Latest checklist
    latest_date = ebird_df["Date"].max()
    latest_df = ebird_df[ebird_df["Date"] == latest_date].copy()
    latest_df["Date"] = latest_df["Date"].dt.strftime("%Y-%m-%d")

    st.subheader("Latest Checklist")
    st.write(f"Date: {latest_date.strftime('%Y-%m-%d')}")
    st.dataframe(latest_df[["Species", "Scientific Name", "Count"]], hide_index=True)

    # Weather
    weather_latest = fetch_weather_data(LATITUDE, LONGITUDE, latest_date.date(), latest_date.date())
    if not weather_latest.empty:
        st.subheader("Weather")
        st.dataframe(weather_latest, hide_index=True)

    # Filters
    st.subheader("Filter by Date Range")
    start = st.date_input("Start", latest_date.date() - datetime.timedelta(days=30))
    end = st.date_input("End", latest_date.date())

    filtered = ebird_df[
        (ebird_df["Date"] >= pd.to_datetime(start)) &
        (ebird_df["Date"] <= pd.to_datetime(end))
    ].copy()
    filtered["Date"] = filtered["Date"].dt.strftime("%Y-%m-%d")
    st.dataframe(filtered, hide_index=True)

    # === Footer ===
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>Nature Notes • Developed with ❤️ by Brooke Adam 🌿</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
