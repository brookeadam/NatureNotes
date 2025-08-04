import streamlit as st
import pandas as pd

st.set_page_config(page_title="Nature Notes | Headwaters", layout="wide")

st.title("🌿 Nature Notes Dashboard – Headwaters at Incarnate Word")

st.markdown("This dashboard is under active development. Below is a preview of loaded data.")

# Load eBird and weather data
@st.cache_data
def load_data():
    ebird = pd.read_csv("ebird_data.csv")
    weather = pd.read_csv("weather_data.csv")
    return ebird, weather

ebird_df, weather_df = load_data()

# Preview sections
st.subheader("🦉 eBird Data Preview")
st.dataframe(ebird_df.head())

st.subheader("🌤️ Weather Data Preview")
st.dataframe(weather_df.head())
