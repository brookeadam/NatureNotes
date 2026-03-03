import streamlit as st
import pandas as pd
import datetime

# ============================================================
# Load & Clean Phenology Data
# ============================================================

@st.cache_data
def load_pheno_data():
    df = pd.read_csv("historical_pheno_data.csv", encoding="utf-8", on_bad_lines="skip")

    # Normalize column names
    df.columns = [c.strip().upper() for c in df.columns]

    # Expected columns
    required = ["OBSERVATIONDATETIME", "LOCATION", "WEDGE", "CATEGORY",
                "COMMONNAME", "SCIENTIFICNAME", "STATUS", "NOTES"]

    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {missing}")
        return pd.DataFrame()

    # Clean & convert
    df["OBSERVATIONDATETIME"] = pd.to_datetime(df["OBSERVATIONDATETIME"], errors="coerce")
    df = df.dropna(subset=["OBSERVATIONDATETIME"])

    df = df.rename(columns={
        "OBSERVATIONDATETIME": "Date",
        "COMMONNAME": "Common Name",
        "SCIENTIFICNAME": "Scientific Name",
        "CATEGORY": "Category",
        "LOCATION": "Location",
        "STATUS": "Status",
        "NOTES": "Notes",
        "WEDGE": "Wedge"
    })

    return df


# ============================================================
# Streamlit App
# ============================================================

def main():
    st.set_page_config(page_title="Headwaters Phenology Dashboard", layout="wide")

    st.markdown("<h1 style='text-align:center;'>🌿 Headwaters Phenology Dashboard 🌿</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;color:gray;'>Plants • Wildlife • Pollinators</h4>", unsafe_allow_html=True)

    df = load_pheno_data()

    if df.empty:
        st.stop()

    MIN_DATE = df["Date"].min().date()
    MAX_DATE = df["Date"].max().date()

    # ============================================================
    # Latest Observations
    # ============================================================

    st.subheader("🆕 Latest Observations")

    latest_date = df["Date"].max()
    latest_df = df[df["Date"] == latest_date].copy()

    st.write(f"**Latest observation date:** {latest_date.strftime('%Y-%m-%d')}")

    st.dataframe(
        latest_df[["Location", "Category", "Common Name", "Scientific Name", "Status", "Notes", "Wedge"]],
        hide_index=True,
        use_container_width=True
    )

    # ============================================================
    # Filter by Date Range
    # ============================================================

    st.subheader("⏱️ Filter by Date Range")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", MIN_DATE, min_value=MIN_DATE, max_value=MAX_DATE)
    with col2:
        end_date = st.date_input("End Date", MAX_DATE, min_value=MIN_DATE, max_value=MAX_DATE)

    filtered = df[(df["Date"] >= pd.to_datetime(start_date)) &
                  (df["Date"] <= pd.to_datetime(end_date))].copy()

    # Sorting controls
    sort_col = st.selectbox("Sort by", ["Date", "Location", "Category", "Common Name"])
    sort_order = st.radio("Order", ["Ascending", "Descending"], horizontal=True)

    filtered = filtered.sort_values(sort_col, ascending=(sort_order == "Ascending"))

    st.dataframe(
        filtered[["Date", "Location", "Category", "Common Name", "Scientific Name", "Status", "Notes", "Wedge"]],
        hide_index=True,
        use_container_width=True
    )

    # ============================================================
    # Compare Two Dates
    # ============================================================

    st.subheader("📝 Compare Specific Dates")

    unique_dates = sorted(df["Date"].dt.date.unique(), reverse=True)

    colA, colB = st.columns(2)
    with colA:
        dateA = st.selectbox("Select Date A", unique_dates)
    with colB:
        dateB = st.selectbox("Select Date B", unique_dates)

    if st.button("Compare Dates"):
        dfA = df[df["Date"].dt.date == dateA]
        dfB = df[df["Date"].dt.date == dateB]

        st.write(f"### 🐦 Comparison: {dateA} vs {dateB}")

        merged = pd.merge(
            dfA.groupby(["Category", "Common Name"]).size().reset_index(name="Count A"),
            dfB.groupby(["Category", "Common Name"]).size().reset_index(name="Count B"),
            on=["Category", "Common Name"],
            how="outer"
        ).fillna(0)

        merged["Difference"] = merged["Count B"] - merged["Count A"]

        st.dataframe(
            merged.sort_values("Difference", ascending=False),
            hide_index=True,
            use_container_width=True
        )

    # ============================================================
    # Compare Two Date Ranges
    # ============================================================

    st.subheader("📊 Compare Two Date Ranges")

    col1, col2 = st.columns(2)
    with col1:
        r1_start = st.date_input("Range 1 Start", MIN_DATE, key="r1s")
        r1_end = st.date_input("Range 1 End", MAX_DATE, key="r1e")
    with col2:
        r2_start = st.date_input("Range 2 Start", MIN_DATE, key="r2s")
        r2_end = st.date_input("Range 2 End", MAX_DATE, key="r2e")

    if st.button("Compare Ranges"):
        A = df[(df["Date"] >= pd.to_datetime(r1_start)) & (df["Date"] <= pd.to_datetime(r1_end))]
        B = df[(df["Date"] >= pd.to_datetime(r2_start)) & (df["Date"] <= pd.to_datetime(r2_end))]

        tableA = A.groupby(["Category", "Common Name"]).size().reset_index(name="Count A")
        tableB = B.groupby(["Category", "Common Name"]).size().reset_index(name="Count B")

        merged = pd.merge(tableA, tableB, on=["Category", "Common Name"], how="outer").fillna(0)
        merged["Difference"] = merged["Count B"] - merged["Count A"]

        st.dataframe(
            merged.sort_values("Difference", ascending=False),
            hide_index=True,
            use_container_width=True
        )

    # ============================================================
    # Footer
    # ============================================================

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:gray;'>Headwaters Phenology Dashboard • Built by Brooke 🌿</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

