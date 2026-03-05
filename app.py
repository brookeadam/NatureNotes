import streamlit as st
# Move imports to the top to prevent routing errors
from pages import _1_eBird_Dashboard as ebird
from pages import _2_Butterfly_Dashboard as butterfly
from pages import _3_Phenology_Dashboard as phenology

st.set_page_config(
    page_title="NatureNotes",
    page_icon="🌿",
    layout="wide"
)

# -------------------------
# SIDEBAR NAVIGATION
# -------------------------

st.sidebar.title("NatureNotes 🌿")

page = st.sidebar.radio(
    "Select Dashboard",
    ["eBird Dashboard", "Butterfly Dashboard", "Phenology Dashboard"]
)

# -------------------------
# PAGE ROUTING
# -------------------------
# We use st.container() to help force the wide layout across the full width
with st.container():
    if page == "eBird Dashboard":
        ebird.main()

    elif page == "Butterfly Dashboard":
        butterfly.main()

    elif page == "Phenology Dashboard":
        phenology.main()
