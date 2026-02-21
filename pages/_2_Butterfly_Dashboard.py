import streamlit as st

def main():
    # ---- your butterfly dashboard code here ----
    
import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.title("San Antonio Butterfly Observation Dashboard 🦋")

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
# UPLOAD NEW LIST
# -------------------------

st.header("Compare New Butterfly List")

uploaded_file = st.file_uploader("Upload New Butterfly CSV", type=["csv"])

if uploaded_file:
    new_df = pd.read_csv(uploaded_file)
    new_df.columns = new_df.columns.str.strip().str.upper()

    if not all(col in new_df.columns for col in required_cols):
        st.error("Uploaded file missing required columns.")
    else:

        comparison = (
            historical_df.groupby("COMMON NAME")["COUNT"].sum()
            .to_frame("Historical")
            .join(
                new_df.groupby("COMMON NAME")["COUNT"].sum()
                .to_frame("New"),
                how="outer"
            )
            .fillna(0)
        )

        comparison["Difference"] = comparison["New"] - comparison["Historical"]

        st.subheader("Species Comparison")

        st.dataframe(
            comparison.sort_values("Difference", ascending=False),
            use_container_width=True,
            hide_index=True
        )

# -------------------------
# WEATHER SECTION
# -------------------------

st.header("Weather Data")

weather_date = st.date_input("Select Date for Weather")

if weather_date:
    formatted_date = weather_date.strftime("%Y-%m-%d")

    # Example placeholder — replace with your weather API call
    st.write(f"Weather data pull for {formatted_date} goes here.")
