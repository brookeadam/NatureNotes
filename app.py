import streamlit as st

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
    ["eBird Dashboard", "Butterfly Dashboard"]
)

# -------------------------
# PAGE ROUTING
# -------------------------

if page == "eBird Dashboard":
    from pages import _1_eBird_Dashboard as ebird
    ebird.main()

elif page == "Butterfly Dashboard":
    from pages import _2_Butterfly_Dashboard as butterfly
    butterfly.main()
