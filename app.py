import streamlit as st
import pandas as pd
import requests
import altair as alt
import datetime
from pathlib import Path
from dateutil.relativedelta import relativedelta

# === Constants ===
HEADWATERS_LOCATIONS = ["L1210588", "L1210849"]
LATITUDE = 29.4689
LONGITUDE = -98.4798
DATA_DIR = Path("data")
# Updated to use the CSV file
EBIRD_DATA_FILE = Path("historical_checklists.csv")

st.set_page_config(page_title="Nature Notes @ Headwaters", layout="wide")

# === API Fetch Functions ===
@st.cache_data
def fetch_weather_data(lat, lon, start, end):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "America/Chicago"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame({
            "Date": pd.to_datetime(data.get("daily", {}).get("time", [])),
            "temp_max": [
                (t * 9/5 + 32) if t is not None else None
                for t in data.get("daily", {}).get("temperature_2m_max", [])
            ],
            "temp_min": [
                (t * 9/5 + 32) if t is not None else None
                for t in data.get("daily", {}).get("temperature_2m_min", [])
            ],
            "precipitation": [
                (p * 0.0393701) if p is not None else None
                for p in data.get("daily", {}).get("precipitation_sum", [])
            ]
        })
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_ebird_data_from_file():
    if EBIRD_DATA_FILE.exists():
        df = pd.read_csv(EBIRD_DATA_FILE, encoding='cp1252', on_bad_lines='skip')
        cleaned_df = clean_ebird_data(df)
        return cleaned_df
    else:
        st.warning("Ebird data file not found. Please check if the GitHub Action ran successfully.")
        return pd.DataFrame()

@st.cache_data
def clean_ebird_data(df):
    """
    Cleans the eBird data by grouping entries and taking the max count
    for each unique observation to remove duplicate reports.
    """
    if df.empty:
        return df
    
    # Standardize column names for processing, including the correct time column
    df_cleaned = df.rename(columns={
        "COMMON NAME": "Species",
        "SCIENTIFIC NAME": "Scientific Name",
        "OBSERVATION COUNT": "Count",
        "OBSERVATION DATE": "Date",
        "TIME OBSERVATIONS STARTED": "Time"
    })
    
    # Convert date and count to proper types
    df_cleaned["Count"] = pd.to_numeric(df_cleaned["Count"], errors='coerce').fillna(0).astype(int)
    df_cleaned["Date"] = pd.to_datetime(df_cleaned["Date"])

    # Group by key fields and aggregate the counts
    cleaned_df = df_cleaned.groupby(
        ["Species", "Scientific Name", "Date", "Time"]
    ).agg(
        Count=('Count', 'max')
    ).reset_index()

    return cleaned_df
    
# === HEADER ===
st.markdown("<h1 style='text-align: center;'>🌳 Nature Notes: Headwaters at Incarnate Word 🌳</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: gray;'>Explore bird sightings and weather patterns side-by-side. Updated biweekly.</h4>", unsafe_allow_html=True)

# Define the minimum and maximum dates for filtering
MIN_DATE = datetime.date(1985, 1, 1)
MAX_DATE = datetime.date(2035, 12, 31)

# === Data Loading and Preprocessing ===
# Load data from files at the top of the script
ebird_df = load_ebird_data_from_file()

# Initialize merged_df to prevent NameError if ebird_df is empty
merged_df = pd.DataFrame(columns=["Species", "Scientific Name", "Count", "Date"])
if not ebird_df.empty:
    merged_df = ebird_df.rename(columns={
        "COMMON NAME": "Species",
        "SCIENTIFIC NAME": "Scientific Name",
        "OBSERVATION COUNT": "Count",
        "OBSERVATION DATE": "Date"
    })
    merged_df["Count"] = pd.to_numeric(merged_df["Count"], errors='coerce').fillna(0).astype(int)
    merged_df["Date"] = pd.to_datetime(merged_df["Date"])

# === Latest Checklist Section ===
st.subheader("🆕 Latest Checklist 🆕")

if not merged_df.empty:
    latest_date = merged_df["Date"].max()
    latest_checklist_df = merged_df[merged_df["Date"] == latest_date].copy()
    
    if not latest_checklist_df.empty:
        st.write(f"**Checklist from:** {latest_date.strftime('%Y-%m-%d')}")
        
        # Display the table of species from the latest checklist
        latest_checklist_table = latest_checklist_df.sort_values(
            "Count", ascending=False
        ).copy()
        
        st.dataframe(
    display_weather_df.style.set_properties(**{'text-align': 'left'}).format(
        {
            'Max Temp °F': '{:.2f}',
            'Min Temp °F': '{:.2f}',
            'Total Precip in': '{:.4f}'
        }
    ),
    use_container_width=True,
    hide_index=True
)

        # Find and display the weather metrics for the latest checklist date
        weather_df = fetch_weather_data(LATITUDE, LONGITUDE, latest_date.date(), latest_date.date())
        weather_filtered = weather_df.copy()
        weather_filtered["Date"] = pd.to_datetime(weather_filtered["Date"])
        weather_filtered = weather_filtered.dropna(subset=["temp_max", "temp_min"])

        if not weather_filtered.empty:
            st.subheader(f"Weather for {latest_date.date()}")
            display_latest_weather_df = weather_filtered.copy()
            display_latest_weather_df["Date"] = display_latest_weather_df["Date"].dt.strftime("%Y-%m-%d")
            
            display_latest_weather_df = display_latest_weather_df.rename(columns={
                "temp_max": "Max Temp °F",
                "temp_min": "Min Temp °F",
                "precipitation": "Total Precip in"
            })
            
st.dataframe(
    display_weather_df.style.set_properties(**{'text-align': 'left'}).format(
        {
            'Max Temp °F': '{:.2f}',
            'Min Temp °F': '{:.2f}',
            'Total Precip in': '{:.4f}'
        }
    ),
    use_container_width=True,
    hide_index=True
)
# === Recent eBird Sightings Section (User-Filtered) ===
st.subheader("🔎 Recent eBird Sightings 🔎")
st.subheader("⏱️ Filter by Date Range ⏱️")

main_start_date = st.date_input("Start Date", key="main_start", min_value=MIN_DATE, max_value=MAX_DATE)
main_end_date = st.date_input("End Date", key="main_end", min_value=MIN_DATE, max_value=MAX_DATE)

# Load weather data based on the selected date range
weather_df = fetch_weather_data(LATITUDE, LONGITUDE, main_start_date, main_end_date)
weather_filtered = weather_df.copy()
weather_filtered["Date"] = pd.to_datetime(weather_filtered["Date"])
weather_filtered = weather_filtered.dropna(subset=["temp_max", "temp_min"])

if not merged_df.empty:
    filtered_ebird_df = merged_df[(merged_df["Date"] >= pd.to_datetime(main_start_date)) &
                                 (merged_df["Date"] <= pd.to_datetime(main_end_date))]
    
    if not filtered_ebird_df.empty:
        filtered_ebird_df = filtered_ebird_df.sort_values("Date", ascending=False).copy()
        filtered_ebird_df["Date"] = filtered_ebird_df["Date"].dt.strftime("%Y-%m-%d")
        
        table_df = filtered_ebird_df[["Species", "Scientific Name", "Count", "Date"]].rename(columns={
            "Species": "COMMON NAME",
            "Scientific Name": "SCIENTIFIC NAME",
            "Count": "OBSERVATION COUNT",
            "Date": "OBSERVATION DATE",
        })
        
        styled_table = table_df.style.set_properties(**{'text-align': 'left'})
        st.dataframe(styled_table, use_container_width=True)
    else:
        st.warning("No recent observations available for the selected date range.")

---
# === Weather Metrics Section (User-Filtered) ===
st.subheader("🌡️ Weather Metrics 🌡️")

if not weather_filtered.empty:
    col1, col2 = st.columns(2)
    with col1:
        max_temp_row = weather_filtered.loc[weather_filtered["temp_max"].idxmax()]
        max_temp = max_temp_row["temp_max"]
        max_temp_date = max_temp_row["Date"]
        st.metric(label=f"Max Temp (F) on {max_temp_date.date()}", value=f"{max_temp:.2f}")
    with col2:
        min_temp_row = weather_filtered.loc[weather_filtered["temp_min"].idxmin()]
        min_temp = min_temp_row["temp_min"]
        min_temp_date = min_temp_row["Date"]
        st.metric(label=f"Min Temp (F) on {min_temp_date.date()}", value=f"{min_temp:.2f}")
        
    st.subheader("Daily Weather Data")
    display_weather_df = weather_filtered.copy()
    display_weather_df["Date"] = display_weather_df["Date"].dt.strftime("%Y-%m-%d")
    
    display_weather_df = display_weather_df.rename(columns={
        "temp_max": "Max Temp °F",
        "temp_min": "Min Temp °F",
        "precipitation": "Total Precip in"
    })
    
    st.dataframe(
        display_weather_df.style.set_properties(**{'text-align': 'left'}).format(
            {
                'Max Temp °F': '{:.2f}',
                'Min Temp °F': '{:.2f}',
                'Total Precip in': '{:.4f}'
            }
        ),
        use_container_width=True
    )
else:
    st.warning("No weather data available for the selected date range.")

---
# === Species Count Comparison ==
st.subheader("📊 Species Comparison by Date Range 📊")

col1, col2 = st.columns(2)
with col1:
    range1_start = st.date_input("Range 1 Start", key="range1_start", min_value=MIN_DATE, max_value=MAX_DATE)
    range1_end = st.date_input("Range 1 End", key="range1_end", min_value=MIN_DATE, max_value=MAX_DATE)
with col2:
    range2_start = st.date_input("Range 2 Start", key="range2_start", min_value=MIN_DATE, max_value=MAX_DATE)
    range2_end = st.date_input("Range 2 End", key="range2_end", min_value=MIN_DATE, max_value=MAX_DATE)

if st.button("Compare Species and Weather"):
    # Filter bird data
    range_a_birds = merged_df[
        (merged_df["Date"] >= pd.to_datetime(range1_start)) &
        (merged_df["Date"] <= pd.to_datetime(range1_end))
    ]
    range_b_birds = merged_df[
        (merged_df["Date"] >= pd.to_datetime(range2_start)) &
        (merged_df["Date"] <= pd.to_datetime(range2_end))
    ]

    # Summary stats
    unique_species_a = range_a_birds["Species"].nunique()
    unique_species_b = range_b_birds["Species"].nunique()
    total_birds_a = range_a_birds["Count"].sum()
    total_birds_b = range_b_birds["Count"].sum()

    st.subheader("🔢 Bird Summary 🔢")
    st.write(f"**Range A ({range1_start}–{range1_end}):** {unique_species_a} unique species, {total_birds_a} total birds")
    st.write(f"**Range B ({range2_start}–{range2_end}):** {unique_species_b} unique species, {total_birds_b} total birds")
    
    # Species comparison table
    table_a = range_a_birds.groupby(["Species", "Scientific Name"])["Count"].sum().reset_index()
    table_b = range_b_birds.groupby(["Species", "Scientific Name"])["Count"].sum().reset_index()

    col_a = f"Birds ({range1_start}–{range1_end})"
    col_b = f"Birds ({range2_start}–{range2_end})"
    comparison_df = pd.merge(table_a.rename(columns={"Count": col_a}),
                             table_b.rename(columns={"Count": col_b}),
                             on=["Species", "Scientific Name"], how="outer").fillna(0)
    comparison_df["Difference"] = comparison_df[col_b] - comparison_df[col_a]

    st.subheader("🐦 Species Comparison Table 🐦")
    st.dataframe(
        comparison_df.style.set_properties(**{'text-align': 'left'}).format(
            {
                col_a: '{:.0f}',
                col_b: '{:.0f}',
                'Difference': '{:.0f}'
            }
        ),
        use_container_width=True
    )
    # Weather comparison
    st.subheader("🌡️ Weather Trends (Detailed) 🌡️")
    weather_range_a = fetch_weather_data(LATITUDE, LONGITUDE, range1_start, range1_end)
    weather_range_b = fetch_weather_data(LATITUDE, LONGITUDE, range2_start, range2_end)

    if not weather_range_a.empty:
        max_temp_row_a = weather_range_a.loc[weather_range_a["temp_max"].idxmax()]
        min_temp_row_a = weather_range_a.loc[weather_range_a["temp_min"].idxmin()]
        max_temp_a = max_temp_row_a["temp_max"]
        max_temp_date_a = max_temp_row_a["Date"].strftime("%Y-%m-%d")
        min_temp_a = min_temp_row_a["temp_min"]
        min_temp_date_a = min_temp_row_a["Date"].strftime("%Y-%m-%d")
        total_precip_a = weather_range_a['precipitation'].sum()
        st.write(f"**Weather Summary: Range A ({range1_start}–{range1_end}):** Max Temp: {max_temp_a:.2f}°F on {max_temp_date_a}, Min Temp: {min_temp_a:.2f}°F on {min_temp_date_a}, Total Precip: {total_precip_a:.4f} in")
        
        renamed_a = weather_range_a.copy()
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
        st.info("No weather data for Range A.")

    if not weather_range_b.empty:
        max_temp_row_b = weather_range_b.loc[weather_range_b["temp_max"].idxmax()]
        min_temp_row_b = weather_range_b.loc[weather_range_b["temp_min"].idxmin()]
        max_temp_b = max_temp_row_b["temp_max"]
        max_temp_date_b = max_temp_row_b["Date"].strftime("%Y-%m-%d")
        min_temp_b = min_temp_row_b["temp_min"]
        min_temp_date_b = min_temp_row_b["Date"].strftime("%Y-%m-%d")
        total_precip_b = weather_range_b['precipitation'].sum()
        st.write(f"**Weather Summary: Range B ({range2_start}–{range2_end}):** Max Temp: {max_temp_b:.2f}°F on {max_temp_date_b}, Min Temp: {min_temp_b:.2f}°F on {min_temp_date_b}, Total Precip: {total_precip_b:.4f} in")
        
        renamed_b = weather_range_b.copy()
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
            use_container_width=True
        )
    else:
        st.info("No weather data for Range B.")

---
# === Compare Specific Checklists ===
st.markdown("---")
st.subheader("📝 Compare Specific Checklists 📝")

if not merged_df.empty:
    unique_dates = sorted(merged_df["Date"].unique(), reverse=True)
    formatted_dates = [d.strftime("%Y-%m-%d") for d in unique_dates]
    
    col1, col2 = st.columns(2)
    with col1:
        selected_checklist_a = st.selectbox(
            "Select Checklist A",
            options=formatted_dates,
            key="checklist_a"
        )
    with col2:
        selected_checklist_b = st.selectbox(
            "Select Checklist B",
            options=formatted_dates,
            key="checklist_b"
        )

    if st.button("Compare Checklists"):
        date_a = pd.to_datetime(selected_checklist_a)
        date_b = pd.to_datetime(selected_checklist_b)
        
        checklist_a_birds = merged_df[merged_df["Date"] == date_a]
        checklist_b_birds = merged_df[merged_df["Date"] == date_b]
        
        st.subheader("🐦 Species Comparison 🐦")
        table_a = checklist_a_birds.groupby(["Species", "Scientific Name"])["Count"].sum().reset_index()
        table_b = checklist_b_birds.groupby(["Species", "Scientific Name"])["Count"].sum().reset_index()
        
        col_a_name = f"Birds ({selected_checklist_a})"
        col_b_name = f"Birds ({selected_checklist_b})"
        
        comparison_df_checklist = pd.merge(table_a.rename(columns={"Count": col_a_name}),
                                         table_b.rename(columns={"Count": col_b_name}),
                                         on=["Species", "Scientific Name"], how="outer").fillna(0)
        comparison_df_checklist["Difference"] = comparison_df_checklist[col_b_name] - comparison_df_checklist[col_a_name]

        st.dataframe(
            comparison_df_checklist.style.set_properties(**{'text-align': 'left'}).format(
                {
                    col_a_name: '{:.0f}',
                    col_b_name: '{:.0f}',
                    'Difference': '{:.0f}'
                }
            ),
            use_container_width=True
        )
        
        st.subheader("🌡️ Weather Comparison 🌡️")
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
                use_container_width=True
            )
        else:
            st.info(f"No weather data available for Checklist B ({selected_checklist_b}).")
else:
    st.info("Ebird data is not available to create a checklist comparison.")
    
# === Footer ===
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Nature Notes for Headwaters at Incarnate Word • Developed with ❤️ by Brooke Adam and Kraken Security Operations 🌿"
    "</div>",
    unsafe_allow_html=True
)
