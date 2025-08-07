import streamlit as st
import pandas as pd
import requests
import os
import base64
from datetime import datetime, timedelta
from io import StringIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import chardet

# ---------- CONFIGURATION ----------
st.set_page_config(page_title="Nature Notes Dashboard", layout="wide")

# Paths
CHECKLIST_PATH = "data/weekly_checklist.csv"
WEATHER_PATH = "data/weather_data.csv"

# App Branding
st.markdown("""
<style>
    body, .stApp { background-color: #f5f2ec; }
    .main { background-color: #f5f2ec; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .css-18ni7ap.e8zbici2 { background-color: #e9e4d4; }
    h1, h2, h3, h4, h5, h6, .stMarkdown { color: #3e3e3c; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---------- FUNCTIONS ----------
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
    result = chardet.detect(raw_data)
    return result['encoding'] or 'utf-8'

def load_checklist():
    encoding = detect_encoding(CHECKLIST_PATH)
    df = pd.read_csv(CHECKLIST_PATH, encoding=encoding, parse_dates=["OBSERVATION DATE"])
    df = df.drop_duplicates(subset=["COMMON NAME", "OBSERVATION DATE", "OBSERVER ID"])
    df = df[df["LOCATION ID"].isin(["L1210588", "L1210849"])]
    return df

def load_weather():
    df = pd.read_csv(WEATHER_PATH, parse_dates=["date"])
    return df

def download_link(df, filename, label):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{label}</a>'
    return href

# ---------- SIDEBAR ----------
st.sidebar.header("🔎 Filter Data")
view_mode = st.sidebar.radio("View Mode", ["📊 Nature Notes Dashboard", "📋 Raw Data"])

# ---------- LOAD DATA ----------
bird_df = load_checklist()
weather_df = load_weather()

# ---------- HEADER ----------
st.title("📊 Nature Notes Dashboard")
st.markdown("### Headwaters at Incarnate Word")
st.caption("Built by Brooke Adam, Run by Kraken Security Operations")

# ---------- DATE FILTERING ----------
min_date = bird_df["OBSERVATION DATE"].min()
max_date = bird_df["OBSERVATION DATE"].max()

def_month = datetime.today().replace(day=1)
start_date = st.sidebar.date_input("Start Date", value=def_month, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", value=datetime.today(), min_value=min_date, max_value=max_date)

mask = (bird_df["OBSERVATION DATE"] >= pd.to_datetime(start_date)) & (bird_df["OBSERVATION DATE"] <= pd.to_datetime(end_date))
filtered_df = bird_df[mask]

# ---------- VIEW MODES ----------
if view_mode == "📊 Nature Notes Dashboard":
    st.subheader(f"🕊️ {len(filtered_df['COMMON NAME'].unique())} Bird Species Observed")
    daily_counts = filtered_df.groupby("OBSERVATION DATE")["COMMON NAME"].nunique()
    weather_filtered = weather_df[(weather_df["date"] >= pd.to_datetime(start_date)) & (weather_df["date"] <= pd.to_datetime(end_date))]

    fig, ax1 = plt.subplots(figsize=(12, 4))
    ax1.plot(daily_counts.index, daily_counts.values, marker="o", label="Species Count", color="tab:green")
    ax1.set_ylabel("Bird Species Count", color="tab:green")
    ax1.tick_params(axis='y', labelcolor="tab:green")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

    ax2 = ax1.twinx()
    ax2.plot(weather_filtered["date"], weather_filtered["avg_temp"], linestyle="--", label="Avg Temp", color="tab:orange")
    ax2.set_ylabel("Avg Temp (°F)", color="tab:orange")
    ax2.tick_params(axis='y', labelcolor="tab:orange")

    fig.autofmt_xdate()
    st.pyplot(fig)

    with st.expander("📸 Recent Observations"):
        for _, row in filtered_df.sort_values("OBSERVATION DATE", ascending=False).head(20).iterrows():
            st.markdown(f"**{row['COMMON NAME']}**  ")
            st.markdown(f"*{row['OBSERVATION DATE'].strftime('%b %d, %Y')} by {row['OBSERVER ID']}*")
            photo_url = f"https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{row['SPECIES CODE']}/512"
            st.image(photo_url, width=150)

    with st.expander("⬇️ Download Data"):
        st.markdown(download_link(filtered_df, "filtered_checklist.csv", "Download Filtered Checklist (CSV)"), unsafe_allow_html=True)

else:
    st.subheader("📋 Raw eBird Data")
    st.dataframe(filtered_df)

# ---------- FOOTER ----------
st.markdown("""
---
<center><sub>📍 Dashboard for Headwaters at Incarnate Word • Built by Brooke Adam, Run by Kraken Security Operations</sub></center>
""", unsafe_allow_html=True)
