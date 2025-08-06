import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# -------------------- Configuration --------------------

st.set_page_config(
    page_title="Nature Notes – Headwaters at Incarnate Word",
    layout="wide",
)

st.title("🪶 Nature Notes – Headwaters at Incarnate Word")
st.caption("Live updates from Headwaters at Incarnate Word using eBird and local weather records.")

CHECKLIST_PATH = "historical_checklists.csv"

# -------------------- Load Data --------------------

@st.cache_data
def load_checklist():
    try:
        return pd.read_csv(CHECKLIST_PATH, encoding="utf-8", parse_dates=["OBSERVATION DATE"])
    except UnicodeDecodeError:
        return pd.read_csv(CHECKLIST_PATH, encoding="latin1", parse_dates=["OBSERVATION DATE"])

df = load_checklist()

# -------------------- Filters --------------------

with st.sidebar:
    st.header("🔍 Filter Observations")
    years = sorted(df["OBSERVATION DATE"].dt.year.unique(), reverse=True)
    selected_year = st.selectbox("Select Year", years, index=0)

    months = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }

    month_options = sorted(df[df["OBSERVATION DATE"].dt.year == selected_year]["OBSERVATION DATE"].dt.month.unique())
    selected_month = st.selectbox("Select Month", [months[m] for m in month_options])

# -------------------- Filter Data --------------------

month_num = [k for k, v in months.items() if v == selected_month][0]
filtered_df = df[
    (df["OBSERVATION DATE"].dt.year == selected_year) &
    (df["OBSERVATION DATE"].dt.month == month_num)
]

# -------------------- Summary Stats --------------------

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Species Observed", filtered_df["COMMON NAME"].nunique())
with col2:
    st.metric("Total Individual Birds", int(filtered_df["OBSERVATION COUNT"].sum()))

# -------------------- Species Counts --------------------

species_counts = (
    filtered_df.groupby("COMMON NAME")["OBSERVATION COUNT"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
    .rename(columns={"COMMON NAME": "Species", "OBSERVATION COUNT": "Count"})
)

st.subheader(f"📋 Top Species in {selected_month} {selected_year}")
st.dataframe(species_counts, use_container_width=True)

# -------------------- Time Series --------------------

st.subheader("📈 Species Observed per Day")
daily_counts = (
    filtered_df.groupby(filtered_df["OBSERVATION DATE"].dt.date)["COMMON NAME"]
    .nunique()
    .reset_index()
)
daily_counts.columns = ["Date", "Unique Species"]

fig, ax = plt.subplots()
sns.lineplot(data=daily_counts, x="Date", y="Unique Species", marker="o", ax=ax)
ax.set_title(f"Unique Species Observed Daily – {selected_month} {selected_year}")
ax.set_ylabel("Number of Species")
ax.set_xlabel("Date")
plt.xticks(rotation=45)
st.pyplot(fig)

# -------------------- Footer --------------------

st.markdown("---")
st.markdown(
    """
    **Nature Notes** is a collaborative project of [Headwaters at Incarnate Word](https://www.headwaters-iw.org/)  
    using publicly available data from [eBird](https://ebird.org/) and local weather stations.

    _Built by Brooke Adam. Updated automatically._
    """
)
