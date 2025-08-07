import streamlit as st
import pandas as pd
import requests
import altair as alt
import datetime
import os
from io import StringIO
from PIL import Image

# Constants
CHECKLIST_PATH = "historical_checklists.csv"
WEATHER_PATH = "weather_data.csv"

# Set page config
st.set_page_config(
    page_title="Nature Notes Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom style
st.markdown(
    """
    <style>
        html, body, [class*="css"]  {
            font-family: 'Arial', sans-serif;
            background-color: #f5f5f2;
        }
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #f5f5f2;
            color: #333333;
            text-align: center;
            padding: 10px;
            font-size: 12px;
        }
    </style>
    <div class="footer">
        📊 Nature Notes Dashboard | Headwaters at Incarnate Word<br>
        Built by Brooke Adam | Run by Kraken Security Operations
    </div>
    """,
    unsafe_allow_html=True
)

# Load weather data with fallback
@st.cache_data

def load_weather():
    try:
        return pd.read_csv(WEATHER_PATH, parse_dates=["Date"])
    except ValueError:
        return pd.read_csv(WEATHER_PATH, parse_dates=["date"])  # fallback for lowercase

# Load bird checklist with encoding fallback
@st.cache_data

def load_checklist():
    encodings = ['utf-8', 'ISO-8859-1', 'cp1252']
    for encoding in encodings:
        try:
            return pd.read_csv(CHECKLIST_PATH, encoding=encoding, parse_dates=["OBSERVATION DATE"])
        except Exception:
            continue
    st.error("❌ Failed to load checklist CSV. Please check file encoding.")
    return pd.DataFrame()

# Load data
weather_df = load_weather()
bird_df = load_checklist()

# Sidebar
st.sidebar.header("🔎 Filter Data")
view_mode = st.sidebar.radio("View Mode", ["📅 Single Date", "📆 Date Range"], index=1)

# Placeholder filters — full implementation continues below...

st.title("📊 Nature Notes Dashboard")
st.subheader("Built by Brooke Adam, supposrted by Kraken Security Operations")
