import streamlit as st
import pandas as pd
import plotly.express as px
import datetime as dt
import requests
import io
import chardet

st.set_page_config(page_title="Nature Notes Dashboard", layout="wide")

st.markdown("# 📊 Nature Notes Dashboard")
st.markdown("### Headwaters at Incarnate Word")
st.caption("Built by Brooke Adam, Run by Kraken Security Operations")

CHECKLIST_PATH = "checklist_data.csv"
WEATHER_PATH = "weather_data.csv"

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
        return result['encoding'] or 'utf-8'

@st.cache_data
def load_checklist():
    encoding = detect_encoding(CHECKLIST_PATH)
    df = pd.read_csv(CHECKLIST_PATH, encoding=encoding, parse_dates=["OBSERVATION DATE"])
    return df

@st.cache_data
def load_weather():
    return pd.read_csv(WEATHER_PATH, parse_dates=["date"])

bird_df = load_checklist()
weather_df = load_weather()

# UI Filters
with st.sidebar:
    st.markdown("## 🔎 Filter Data")
    view_mode = st.radio("View Mode", ["📅 Date Range", "🕒 Quick Filters"], index=0)

    if view_mode == "📅 Date Range":
        min_date = bird_df["OBSERVATION DATE"].min()
        max_date = bird_df["OBSERVATION DATE"].max()
        date_range = st.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
    else:
        quick_filter = st.selectbox("Select Timeframe", ["Last 7 Days", "This Month", "This Season", "All Time"])

# Filter Data Based on UI
def filter_data():
    if view_mode == "📅 Date Range":
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        today = pd.to_datetime("today")
        if quick_filter == "Last 7 Days":
            start, end = today - pd.Timedelta(days=7), today
        elif quick_filter == "This Month":
            start = today.replace(day=1)
            end = today
        elif quick_filter == "This Season":
            month = today.month
            if month in [12, 1, 2]:
                start = pd.to_datetime(f"{today.year if month != 12 else today.year-1}-12-01")
            elif month in [3, 4, 5]:
                start = pd.to_datetime(f"{today.year}-03-01")
            elif month in [6, 7, 8]:
                start = pd.to_datetime(f"{today.year}-06-01")
            else:
                start = pd.to_datetime(f"{today.year}-09-01")
            end = today
        else:
            start, end = bird_df["OBSERVATION DATE"].min(), bird_df["OBSERVATION DATE"].max()
    bird_filtered = bird_df[(bird_df["OBSERVATION DATE"] >= start) & (bird_df["OBSERVATION DATE"] <= end)]
    weather_filtered = weather_df[(weather_df["date"] >= start) & (weather_df["date"] <= end)]
    return bird_filtered, weather_filtered, start, end

bird_filtered, weather_filtered, start_date, end_date = filter_data()

# Summary Metrics
total_species = bird_filtered["COMMON NAME"].nunique()
total_observations = bird_filtered.shape[0]
most_common = bird_filtered["COMMON NAME"].value_counts().idxmax()

col1, col2, col3 = st.columns(3)
col1.metric("Unique Species", total_species)
col2.metric("Observations", total_observations)
col3.metric("Most Common Species", most_common)

# Daily Species Chart
st.subheader("📈 Species Count Over Time")
daily_counts = bird_filtered.groupby("OBSERVATION DATE")["COMMON NAME"].nunique().reset_index()
fig = px.line(daily_counts, x="OBSERVATION DATE", y="COMMON NAME", labels={"COMMON NAME": "Species Count"})
st.plotly_chart(fig, use_container_width=True)

# Species and Temperature Overlay
st.subheader("🌡️ Species vs Temperature")
combined_df = pd.merge(
    bird_filtered.groupby("OBSERVATION DATE")["COMMON NAME"].nunique().reset_index(name="Species Count"),
    weather_filtered[["date", "avg_temp"]],
    left_on="OBSERVATION DATE", right_on="date", how="left"
).dropna()

fig2 = px.scatter(combined_df, x="avg_temp", y="Species Count", trendline="ols",
                  labels={"avg_temp": "Avg Temp (°F)", "Species Count": "Species Count"})
st.plotly_chart(fig2, use_container_width=True)

# Checklist View
st.subheader("📝 Recent Checklists")
latest_checklists = bird_filtered.sort_values("OBSERVATION DATE", ascending=False).head(10)
st.dataframe(latest_checklists[["OBSERVATION DATE", "COMMON NAME", "COUNT", "LOCATION NAME", "OBSERVER ID"]])

# Footer
st.markdown("---")
st.markdown(
    "### Headwaters at Incarnate Word  \n"
    "_A sanctuary for people and nature in the heart of San Antonio._  \n"
    "Data presented here is collected through eBird and NOAA services.  \n"
    "Dashboard designed by **Brooke Adam** | Operated by **Kraken Security Operations**"
)
