import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# -------------------------
# WEATHER HELPER & CONSTANTS
# -------------------------
LATITUDE = 29.4678
LONGITUDE = -98.4750

@st.cache_data
def fetch_weather_data(lat, lon, date_obj):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_obj.strftime('%Y-%m-%d'),
        "end_date": date_obj.strftime('%Y-%m-%d'),
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "timezone": "America/Chicago"
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            return pd.DataFrame({
                "Max Temp": daily.get("temperature_2m_max", []),
                "Min Temp": daily.get("temperature_2m_min", []),
                "Precipitation": daily.get("precipitation_sum", [])
            })
    except:
        pass
    return pd.DataFrame()

def main():

    # === HEADER (Centered HTML) ===
    st.markdown("<h1 style='text-align: center;'>🌳 Nature Notes: Headwaters at Incarnate Word 🌳</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray;'>Explore butterfly sightings and weather patterns side-by-side. Updated monthly.</h4>", unsafe_allow_html=True)

    # -------------------------
    # LOAD DATA
    # -------------------------
    try:
        # Load the specific 2025 butterfly CSV
        df = pd.read_csv("san_antonio_butterfly_counts_consolidated_2025.csv")
        df.columns = df.columns.str.strip().str.upper()
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
        df = df.dropna(subset=["DATE"])
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return

    # -------------------------
    # SELECT SPECIFIC CHECKLIST SECTION
    # -------------------------
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>📋 Select Specific Checklist</h2>", unsafe_allow_html=True)
    
    # Get the unique dates (July 10 and Oct 15)
    available_dates = sorted(df["DATE"].dt.date.unique(), reverse=True)
    
    # Dropdown to select between the two dates
    _, col_selector, _ = st.columns([2, 2, 2])
    with col_selector:
        selected_date = st.selectbox("Choose a survey date to view details:", available_dates)

    if selected_date:
        # Filter sightings for the selected date only
        checklist_df = df[df["DATE"].dt.date == selected_date].copy()
        
        # --- Summary Metrics for the Selected Date ---
        st.markdown(f"<h3 style='text-align: center;'>Summary for {selected_date}</h3>", unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        spec_count = checklist_df["COMMON NAME"].nunique()
        indiv_count = checklist_df["COUNT"].sum()
        
        # Calculate most frequent species for the metrics
        if not checklist_df.empty:
            top_bug = checklist_df.groupby("COMMON NAME")["COUNT"].sum().idxmax()
        else:
            top_bug = "N/A"

        m1.metric("Species Found", spec_count)
        m2.metric("Total Individuals", int(indiv_count))
        m3.metric("Most Observed", top_bug)

        # --- Details: Sightings & Weather side-by-side ---
        st.markdown("<br>", unsafe_allow_html=True)
        col_list, col_weather = st.columns([2, 1])
        
        with col_list:
            st.subheader(f"🦋 Butterfly List ({selected_date})")
            display_list = checklist_df[["COMMON NAME", "SCIENTIFIC NAME", "COUNT"]].sort_values("COUNT", ascending=False)
            st.dataframe(display_list, use_container_width=True, hide_index=True)
            
        with col_weather:
            st.subheader("🌡️ Weather Conditions")
            weather_data = fetch_weather_data(LATITUDE, LONGITUDE, selected_date)
            if not weather_data.empty:
                # Transpose the weather table so it looks like a list
                st.table(weather_data.T.rename(columns={0: "Value"}))
            else:
                st.info("Weather data unavailable for this date.")

    # -------------------------
    # COMPARISON SECTION
    # -------------------------
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>📊 Comparison Between Dates</h2>", unsafe_allow_html=True)
    
    # Default to comparing the two available dates
    if len(available_dates) >= 2:
        date_a = available_dates[1] # July 10
        date_b = available_dates[0] # Oct 15
        
        st.markdown(f"<p style='text-align: center;'>Comparing <b>{date_a}</b> (A) vs <b>{date_b}</b> (B)</p>", unsafe_allow_html=True)
        
        df_a = df[df["DATE"].dt.date == date_a].groupby("COMMON NAME")["COUNT"].sum()
        df_b = df[df["DATE"].dt.date == date_b].groupby("COMMON NAME")["COUNT"].sum()
        
        comp_df = pd.DataFrame({
            f"Count ({date_a})": df_a,
            f"Count ({date_b})": df_b
        }).fillna(0)
        
        comp_df["Difference"] = comp_df[f"Count ({date_b})"] - comp_df[f"Count ({date_a})"]
        
        _, cent_col, _ = st.columns([1, 6, 1])
        with cent_col:
            st.dataframe(comp_df.sort_values("Difference", ascending=False), use_container_width=True)

    # === Footer ===
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray;'>Nature Notes • Headwaters at Incarnate Word 🌿</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
