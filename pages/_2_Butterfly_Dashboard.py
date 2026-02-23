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

    historical_df["DATE"] = pd.to_datetime(
    historical_df["DATE"],
    errors="coerce",
    infer_datetime_format=True
)
    
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

            st.header("🌡️ Weather Comparison 🌡️")
            weather_a = fetch_weather_data(LATITUDE, LONGITUDE, date_a.date(), date_a.date())
            weather_b = fetch_weather_data(LATITUDE, LONGITUDE, date_b.date(), date_b.date())
            
            if not weather_a.empty:
                max_temp_row_a = weather_a.loc[weather_a["temp_max"].idxmax()]
                min_temp_row_a = weather_a.loc[weather_a["temp_min"].idxmin()]
                max_temp_a = max_temp_row_a["temp_max"]
                max_temp_date_a = max_temp_row_a["Date"].strftime("%Y-%m-%d")
                min_temp_a = min_temp_row_a["temp_min"]
                min_temp_date_a = min_temp_row_a["Date"].strftime("%Y-%m-%d")
                total_precip_a = weather_a['precipitation'].sum()
                st.write(f"**Weather Summary: Checklist A ({selected_checklist_a}):** Max Temp: {max_temp_a:.2f}°F on {max_temp_date_a}, Min Temp: {min_temp_a:.2f}°F on {min_temp_date_a}, Total Precip: {total_precip_a:.4f} in")
                
                renamed_a = weather_a.copy()
                renamed_a["Date"] = renamed_a["Date"].dt.strftime("%Y-%m-%d")
                renamed_a = renamed_a.rename(columns={
                    "temp_max": "Max Temp °F",
                    "temp_min": "Min Temp °F",
                    "precipitation": "Total Precip in"
                })
                st.dataframe(
                    renamed_a.style.set_properties(**{'text-align': 'left'}).format(
                        {
                            'Max Temp °F': '{:.2f}',
                            'Min Temp °F': '{:.2f}',
                            'Total Precip in': '{:.4f}'
                        }
                    ),
                    use_container_width=True
                )
            else:
                st.info(f"No weather data available for Checklist A ({selected_checklist_a}).")
                
            if not weather_b.empty:
                max_temp_row_b = weather_b.loc[weather_b["temp_max"].idxmax()]
                min_temp_row_b = weather_b.loc[weather_b["temp_min"].idxmin()]
                max_temp_b = max_temp_row_b["temp_max"]
                max_temp_date_b = max_temp_row_b["Date"].strftime("%Y-%m-%d")
                min_temp_b = min_temp_row_b["temp_min"]
                min_temp_date_b = min_temp_row_b["Date"].strftime("%Y-%m-%d")
                total_precip_b = weather_b['precipitation'].sum()
                st.write(f"**Weather Summary: Checklist B ({selected_checklist_b}):** Max Temp: {max_temp_b:.2f}°F on {max_temp_date_b}, Min Temp: {min_temp_b:.2f}°F on {min_temp_date_b}, Total Precip: {total_precip_b:.4f} in")
                
                renamed_b = weather_b.copy()
                renamed_b["Date"] = renamed_b["Date"].dt.strftime("%Y-%m-%d")
                renamed_b = renamed_b.rename(columns={
                    "temp_max": "Max Temp °F",
                    "temp_min": "Min Temp °F",
                    "precipitation": "Total Precip in"
                })
                st.dataframe(
                    renamed_b.style.set_properties(**{'text-align': 'left'}).format(
                        {
                            'Max Temp °F': '{:.2f}',
                            'Min Temp °F': '{:.2f}',
                            'Total Precip in': '{:.4f}'
                        }
                    ),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(f"No weather data available for Checklist B ({selected_checklist_b}).")


    # === Footer ===
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Nature Notes for Headwaters at Incarnate Word • Developed with ❤️ by Brooke Adam and Kraken Security Operations 🌿"
        "</div>",
        unsafe_allow_html=True
    )
