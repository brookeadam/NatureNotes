import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# -------------------------
# WEATHER HELPER & CONSTANTS
# -------------------------
LATITUDE = 29.4678 
LONGITUDE = -98.4750

def fetch_weather_data(lat, lon, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "timezone": "America/Chicago"
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            return pd.DataFrame({
                "Date": pd.to_datetime(daily.get("time", [])),
                "temp_max": daily.get("temperature_2m_max", []),
                "temp_min": daily.get("temperature_2m_min", []),
                "precipitation": daily.get("precipitation_sum", [])
            })
    except Exception:
        pass
    return pd.DataFrame()

def main():

    st.set_page_config(
        page_title="Nature Notes Butterfly Observations Dashboard",
        layout="wide"
    )

    # -------------------------
    # LOAD HISTORICAL DATA
    # -------------------------

    historical_df = pd.read_csv("san_antonio_butterfly_counts_consolidated_2025.csv")
    historical_df.columns = historical_df.columns.str.strip().str.upper()
    historical_df["DATE"] = pd.to_datetime(historical_df["DATE"], errors="coerce")

    required_cols = ["COMMON NAME", "SCIENTIFIC NAME", "COUNT", "DATE"]
    missing = [col for col in required_cols if col not in historical_df.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
    else:
        st.header("Historical Summary")

        total_species = historical_df["COMMON NAME"].nunique()
        total_individuals = historical_df["COUNT"].sum()

        most_common = (
            historical_df.groupby("COMMON NAME")["COUNT"]
            .sum()
            .sort_values(ascending=False)
            .head(1)
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Species", total_species)
        col2.metric("Total Individuals", total_individuals)
        if not most_common.empty:
            col3.metric("Most Observed", most_common.index[0])

        # Formatting Date for display (removes 00:00:00)
        display_df = historical_df.copy()
        display_df["DATE"] = display_df["DATE"].dt.strftime("%Y-%m-%d")

        st.dataframe(
            display_df.sort_values("DATE"),
            use_container_width=True,
            hide_index=True
        )

        # -------------------------
        # TWO-DATE COMPARISON
        # -------------------------

        st.header("Date Comparison")
        unique_dates = sorted(historical_df["DATE"].dropna().unique())

        if len(unique_dates) < 2:
            st.warning("This dashboard is designed for at least two survey dates.")
        else:
            date_a = unique_dates[0]
            date_b = unique_dates[1]
            
            selected_checklist_a = pd.to_datetime(date_a).date()
            selected_checklist_b = pd.to_datetime(date_b).date()

            st.subheader("Survey Dates Compared")
            st.write(f"Date A: {selected_checklist_a}")
            st.write(f"Date B: {selected_checklist_b}")

            df_a = historical_df[historical_df["DATE"] == date_a]
            df_b = historical_df[historical_df["DATE"] == date_b]

            col_label_a = "2025-07-10"
            col_label_b = "2025-10-15"

            grouped_a = df_a.groupby("COMMON NAME")["COUNT"].sum().to_frame(col_label_a)
            grouped_b = df_b.groupby("COMMON NAME")["COUNT"].sum().to_frame(col_label_b)

            comparison = grouped_a.join(grouped_b, how="outer").fillna(0)
            comparison["Difference"] = comparison[col_label_b] - comparison[col_label_a]

            st.subheader("Species Comparison")
            st.dataframe(
                comparison.sort_values("Difference", ascending=False),
                use_container_width=True
            )

            # -------------------------
            # WEATHER SECTION
            # -------------------------

            st.header("🌡️ Weather Comparison 🌡️")

            weather_a = fetch_weather_data(LATITUDE, LONGITUDE, selected_checklist_a, selected_checklist_a)
            weather_b = fetch_weather_data(LATITUDE, LONGITUDE, selected_checklist_b, selected_checklist_b)

            # Dictionary to map technical names to your preferred labels
            weather_labels = {
                "temp_max": "Max Temp",
                "temp_min": "Min Temp",
                "precipitation": "Precipitation"
            }

            if not weather_a.empty:
                max_temp_val_a = weather_a["temp_max"].max()
                min_temp_val_a = weather_a["temp_min"].min()
                precip_val_a = weather_a["precipitation"].sum()
                
                st.write(f"**Weather Summary ({selected_checklist_a}):** Max: {max_temp_val_a:.2f}°F, Min: {min_temp_val_a:.2f}°F, Precip: {precip_val_a:.2f} in")
                
                # Format and rename columns for display
                weather_display_a = weather_a.copy()
                weather_display_a["Date"] = weather_display_a["Date"].dt.strftime("%Y-%m-%d")
                weather_display_a = weather_display_a.rename(columns=weather_labels)
                
                st.dataframe(weather_display_a, use_container_width=True, hide_index=True)

            if not weather_b.empty:
                max_temp_val_b = weather_b["temp_max"].max()
                min_temp_val_b = weather_b["temp_min"].min()
                precip_val_b = weather_b["precipitation"].sum()
                
                st.write(f"**Weather Summary ({selected_checklist_b}):** Max: {max_temp_val_b:.2f}°F, Min: {min_temp_val_b:.2f}°F, Precip: {precip_val_b:.2f} in")
                
                # Format and rename columns for display
                weather_display_b = weather_b.copy()
                weather_display_b["Date"] = weather_display_b["Date"].dt.strftime("%Y-%m-%d")
                weather_display_b = weather_display_b.rename(columns=weather_labels)
                
                st.dataframe(weather_display_b, use_container_width=True, hide_index=True)

    # === Footer ===
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Nature Notes for Headwaters at Incarnate Word • Developed with ❤️ by Brooke Adam and Kraken Security Operations 🌿"
        "</div>",
        unsafe_allow_html=True,
    )

if __name__ == "__main__":
    main()
