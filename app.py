# Nature Notes App – Version: 2025.08.06.0
# Baseline confirmed version – DO NOT EDIT DIRECTLY
# Built by Brooke Adam, Run by Kraken Security Operations

import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import datetime
from PIL import Image
import chardet

st.set_page_config(page_title="Nature Notes Dashboard", layout="wide")

# --- CONSTANTS ---
CHECKLIST_PATH = "historical_checklists.csv"
LOGO_PATH = "headwaters_logo.png"

LOCATION_LABELS = {
    "L1210588": "Headwaters Sanctuary Entrance",
    "L1210849": "Blue Hole Spring Trail"
}

# --- FUNCTIONS ---
def detect_encoding(filepath):
    with open(filepath, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def load_checklist():
    encoding = detect_encoding(CHECKLIST_PATH)
    df = pd.read_csv(CHECKLIST_PATH, encoding=encoding, parse_dates=["OBSERVATION DATE"])
    df = df[df["LOC ID"].isin(LOCATION_LABELS.keys())]
    df = df[df["CATEGORY"] != ""]
    df["COMMON NAME"] = df["COMMON NAME"].str.title()
    return df

def filter_data(df, location_filter, date_range):
    filtered = df.copy()
    if location_filter != "All":
        loc_id = [k for k, v in LOCATION_LABELS.items() if v == location_filter][0]
        filtered = filtered[filtered["LOC ID"] == loc_id]
    if date_range:
        start, end = date_range
        filtered = filtered[(filtered["OBSERVATION DATE"] >= start) & (filtered["OBSERVATION DATE"] <= end)]
    return filtered

# --- LOAD DATA ---
bird_df = load_checklist()

# --- SIDEBAR ---
st.sidebar.header("🔎 Filter Data")
location_selection = st.sidebar.selectbox("View Location", ["All"] + list(LOCATION_LABELS.values()))

min_date = bird_df["OBSERVATION DATE"].min()
max_date = bird_df["OBSERVATION DATE"].max()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

filtered_df = filter_data(bird_df, location_selection, date_range)

# --- HEADER ---
st.markdown("""
    <h1 style='text-align: center;'>📊 Nature Notes Dashboard</h1>
    <h3 style='text-align: center;'>Headwaters at Incarnate Word</h3>
""", unsafe_allow_html=True)

# --- SUMMARY STATS ---
total_species = filtered_df["COMMON NAME"].nunique()
total_observations = filtered_df.shape[0]
latest_date = filtered_df["OBSERVATION DATE"].max().strftime("%B %d, %Y")

col1, col2, col3 = st.columns(3)
col1.metric("Species Count", total_species)
col2.metric("Total Observations", total_observations)
col3.metric("Most Recent Observation", latest_date)

# --- SPECIES TABLE ---
st.subheader("📋 Recent Bird Observations")
latest_obs = filtered_df.sort_values(by="OBSERVATION DATE", ascending=False).head(20)
st.dataframe(latest_obs[["OBSERVATION DATE", "COMMON NAME", "SCIENTIFIC NAME", "HOW MANY"]].rename(columns={
    "OBSERVATION DATE": "Date",
    "COMMON NAME": "Species",
    "SCIENTIFIC NAME": "Scientific Name",
    "HOW MANY": "Count"
}), use_container_width=True)

# --- CHART ---
st.subheader("📈 Observation Trends Over Time")
time_series = (
    filtered_df.groupby(filtered_df["OBSERVATION DATE"].dt.to_period("M"))
    .agg({"COMMON NAME": "nunique", "OBSERVATION DATE": "count"})
    .rename(columns={"COMMON NAME": "Unique Species", "OBSERVATION DATE": "Total Observations"})
    .reset_index()
)
time_series["OBSERVATION DATE"] = time_series["OBSERVATION DATE"].dt.to_timestamp()

line_chart = alt.Chart(time_series).transform_fold(
    ["Unique Species", "Total Observations"],
    as_=["Metric", "Value"]
).mark_line().encode(
    x="OBSERVATION DATE:T",
    y="Value:Q",
    color="Metric:N"
).properties(
    width=800,
    height=400
)

st.altair_chart(line_chart, use_container_width=True)

# --- FOOTER ---
st.markdown("""
    <hr>
    <div style='text-align: center; font-size: 0.9em;'>
        Built by Brooke Adam, Run by Kraken Security Operations
    </div>
""", unsafe_allow_html=True)
