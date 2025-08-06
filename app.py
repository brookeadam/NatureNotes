import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# Constants
CHECKLIST_PATH = "historical_checklists.csv"

# App Configuration
st.set_page_config(
    page_title="Nature Notes – Headwaters at Incarnate Word",
    layout="wide",
)

st.title("🪶 Nature Notes – Headwaters at Incarnate Word")
st.caption("Live updates from Headwaters at Incarnate Word using eBird and local weather records.")

# Data loading
@st.cache_data
def load_checklist():
    return pd.read_csv(CHECKLIST_PATH, encoding="utf-8", parse_dates=["OBSERVATION DATE"])

df = load_checklist()

# Sidebar Filters
with st.sidebar:
    st.header("Filters")
    years = sorted(df["OBSERVATION DATE"].dt.year.unique())
    selected_year = st.selectbox("Year", options=years, index=len(years)-1)

    months = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }

    selected_month = st.selectbox("Month", options=months.keys(), format_func=lambda x: months[x])

# Filter data
df_filtered = df[
    (df["OBSERVATION DATE"].dt.year == selected_year) &
    (df["OBSERVATION DATE"].dt.month == selected_month)
]

# Summary stats
st.subheader(f"📊 Summary for {months[selected_month]} {selected_year}")
col1, col2 = st.columns(2)
with col1:
    st.metric("Unique Species", df_filtered["COMMON NAME"].nunique())
with col2:
    st.metric("Total Observations", df_filtered["OBSERVATION COUNT"].sum())

# Species Table
st.subheader("📋 Species Observed")
species_summary = (
    df_filtered.groupby("COMMON NAME")["OBSERVATION COUNT"]
    .sum()
    .reset_index()
    .sort_values(by="OBSERVATION COUNT", ascending=False)
)
st.dataframe(species_summary, use_container_width=True)

# Time series visualization
st.subheader("📈 Observations Over Time")
time_series = (
    df_filtered.groupby("OBSERVATION DATE")["OBSERVATION COUNT"]
    .sum()
    .reset_index()
    .sort_values("OBSERVATION DATE")
)

fig, ax = plt.subplots()
ax.plot(time_series["OBSERVATION DATE"], time_series["OBSERVATION COUNT"], marker="o")
ax.set_xlabel("Date")
ax.set_ylabel("Total Observations")
ax.set_title(f"Daily Observation Counts – {months[selected_month]} {selected_year}")
ax.grid(True)
st.pyplot(fig)

# Footer / Acknowledgments
st.markdown("---")
st.caption("📍 Powered by [eBird](https://ebird.org) and real-time weather integration. Data visualized for Headwaters at Incarnate Word.")
