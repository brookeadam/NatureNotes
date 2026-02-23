import streamlit as st
import pandas as pd
import requests
from datetime import datetime

def main():

    st.set_page_config(page_title="Nature Notes Butterfly Observations Dashboard for Headwaters at Incarnate Word", layout="wide")
    
    # -------------------------
    # LOAD HISTORICAL DATA
    # -------------------------
    
    historical_df = pd.read_csv("san_antonio_butterfly_counts_consolidated_2025.csv")
    
    historical_df.columns = historical_df.columns.str.strip().str.upper()
    
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
        col3.metric("Most Observed", most_common.index[0])
    
        st.dataframe(
            historical_df.sort_values("DATE"),
            use_container_width=True,
            hide_index=True
        )
    
    # -------------------------
    # TWO-DATE COMPARISON
    # -------------------------
    
    st.header("Date Comparison")
    
    historical_df["DATE"] = pd.to_datetime(historical_df["DATE"])
    
    unique_dates = sorted(historical_df["DATE"].unique())
    
    if len(unique_dates) != 2:
        st.warning("This dashboard is designed for exactly two survey dates.")
    else:
    
        date_a = unique_dates[0]
        date_b = unique_dates[1]
    
        st.subheader("Survey Dates Compared")
        st.write(f"Date A: {pd.to_datetime(date_a).date()}")
        st.write(f"Date B: {pd.to_datetime(date_b).date()}")
    
        df_a = historical_df[historical_df["DATE"] == date_a]
        df_b = historical_df[historical_df["DATE"] == date_b]
    
        grouped_a = df_a.groupby("COMMON NAME")["COUNT"].sum().to_frame("Date A")
        grouped_b = df_b.groupby("COMMON NAME")["COUNT"].sum().to_frame("Date B")
    
        comparison = grouped_a.join(grouped_b, how="outer").fillna(0)
    
        comparison["Difference"] = comparison["Date B"] - comparison["Date A"]
    
        st.subheader("Species Comparison")
    
        st.dataframe(
            comparison.sort_values("Difference", ascending=False),
            use_container_width=True,
            hide_index=True
        )
    
    # -------------------------
    # WEATHER SECTION
    # -------------------------

    st.header("Weather Comparison")

    unique_dates = sorted(historical_df["DATE"].dt.strftime("%Y-%m-%d").unique())

    if len(unique_dates) == 2:

        date1 = datetime.strptime(unique_dates[0], "%Y-%m-%d")
        date2 = datetime.strptime(unique_dates[1], "%Y-%m-%d")

        # ---- Replace this with your actual weather API call ----
        # Example placeholder weather values
        weather_data = {
            unique_dates[0]: {"temp": 92, "conditions": "Partly Cloudy"},
            unique_dates[1]: {"temp": 88, "conditions": "Sunny"},
        }

        col1, col2 = st.columns(2)

        with col1:
            st.subheader(unique_dates[0])
            st.metric("Temperature (°F)", weather_data[unique_dates[0]]["temp"])
            st.write(weather_data[unique_dates[0]]["conditions"])

        with col2:
            st.subheader(unique_dates[1])
            st.metric("Temperature (°F)", weather_data[unique_dates[1]]["temp"])
            st.write(weather_data[unique_dates[1]]["conditions"])

        temp_difference = (
            weather_data[unique_dates[1]]["temp"]
            - weather_data[unique_dates[0]]["temp"]
        )

        st.subheader("Temperature Difference")
        st.metric("Δ Temperature (°F)", temp_difference)

    else:
        st.warning("Weather comparison requires exactly two survey dates.")

    # === Footer ===
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Nature Notes for Headwaters at Incarnate Word • Developed with ❤️ by Brooke Adam and Kraken Security Operations 🌿"
        "</div>",
        unsafe_allow_html=True
    )
