import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Nature Notes: Headwaters Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Branding
st.title("🪶 Nature Notes: Headwaters at Incarnate Word")
st.markdown("##### eBird & Weather Dashboard")
st.info("This dashboard is under construction. Please check back soon for live eBird and weather data visualizations for the Headwaters at Incarnate Word.")

# Placeholder layout
with st.expander("About this Dashboard"):
    st.markdown("""
    This app will compare eBird observations and local weather conditions from:
    - 📍 Headwaters Main Campus (L1210588)
    - 📍 Headwaters Sanctuary (L1210849)

    You'll be able to:
    - View bird sightings across custom timeframes
    - Analyze bird activity trends with temperature and precipitation
    - Export the data to Excel
    - Support local education and conservation efforts
    """)

st.markdown("### 🔧 Components still being finalized:")
st.markdown("""
- Interactive species lists and heatmaps
- Weather overlays by season and year
- Downloadable reports
- Live filters and comparisons
""")

st.success("Check back soon or contact mrsbrookeadam for project updates.")

# Footer
st.markdown("---")
st.caption("Nature Notes powered by Streamlit • Data from eBird and NOAA • Built for Headwaters at Incarnate Word")
