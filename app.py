import streamlit as st
import pandas as pd
import altair as alt
import datetime as dt
import os

# ----------------------------
# Configuration
# ----------------------------
st.set_page_config(
    page_title="Nature Notes – Headwaters at Incarnate Word",
    layout="wide"
)

st.title("🪶 Nature Notes – Headwaters at Incarnate Word")
st.markdown("""
Live updates from Headwaters at Incarnate Word using eBird and local weather records.
""")

CHECKLIST_PATH = "historical_checklist.csv"

# ----------------------------
# Load and Clean Checklist Data
# ----------------------------
@st.cache_data
def load_checklist():
    df = pd.read_csv(CHECKLIST_PATH, parse_dates=["OBSERVATION DATE"])
    df.rename(columns={"OBSERVATION DATE": "obsDt"}, inplace=True)

    # Drop unnecessary columns like unnamed/empty trailing ones
    df = df.loc[:, ~df.columns.str.contains("^Unnamed|^Column1$", case=False)]
    
    # Optional: Normalize column names (strip whitespace)
    df.columns = df.columns.str.strip()

    return df

df = load_checklist()

# ----------------------------
# Sidebar Filters
# ----------------------------
st.sidebar.header("Filter Observations")

min_date = df["obsDt"].min().date()
max_date = df["obsDt"].max().date()
default_start = max_date - dt.timedelta(days=30)

date_range = st.sidebar.date_input(
    "Date Range",
    value=(default_start, max_date),
    min_value=min_date,
    max_value=max_date
)

selected_species = st.sidebar.multiselect(
    "Filter by Common Name",
    sorted(df["COMMON NAME"].unique()),
    default=None
)

# ----------------------------
# Apply Filters
# ----------------------------
filtered_df = df.copy()

if date_range:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered_df = filtered_df[
        (filtered_df["obsDt"] >= start_date) & (filtered_df["obsDt"] <= end_date)
    ]

if selected_species:
    filtered_df = filtered_df[filtered_df["COMMON NAME"].isin(selected_species)]

# ----------------------------
# Display Summary
# ----------------------------
st.subheader("Recent Bird Observations")

summary = filtered_df.groupby("COMMON NAME")["OBSERVATION COUNT"].sum().reset_index()
summary = summary.sort_values("OBSERVATION COUNT", ascending=False)

st.dataframe(summary, use_container_width=True)

# ----------------------------
# Visualize Sightings Over Time
# ----------------------------
st.subheader("Sightings Over Time")

time_chart_data = (
    filtered_df.groupby(["obsDt", "COMMON NAME"])["OBSERVATION COUNT"]
    .sum()
    .reset_index()
)

if not time_chart_data.empty:
    chart = alt.Chart(time_chart_data).mark_line().encode(
        x="obsDt:T",
        y="OBSERVATION COUNT:Q",
        color="COMMON NAME:N",
        tooltip=["obsDt:T", "COMMON NAME:N", "OBSERVATION COUNT:Q"]
    ).properties(
        width=800,
        height=400
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No data available for the selected filters.")

# ----------------------------
# Footer / Acknowledgment
# ----------------------------
st.markdown("""
---
**Nature Notes Dashboard**  
Data from [eBird](https://ebird.org/) • Project by Headwaters at Incarnate Word  
Created with ❤️ by Brooke Adam using Streamlit
""")
