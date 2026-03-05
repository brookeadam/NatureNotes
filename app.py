import streamlit as st

# MUST be the first Streamlit command
st.set_page_config(
    page_title="NatureNotes",
    page_icon="🌿",
    layout="wide"
)

# --- FORCE WIDE LAYOUT CSS ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 5rem;
            padding-right: 5rem;
        }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.title("NatureNotes 🌿")

page = st.sidebar.radio(
    "Select Dashboard",
    ["eBird Dashboard", "Butterfly Dashboard", "Phenology Dashboard"]
)

# -------------------------
# PAGE ROUTING
# -------------------------
# We import inside the IF blocks to prevent the "disappearing" error
if page == "eBird Dashboard":
    from pages import _1_eBird_Dashboard as ebird
    ebird.main()

elif page == "Butterfly Dashboard":
    from pages import _2_Butterfly_Dashboard as butterfly
    butterfly.main()

elif page == "Phenology Dashboard":
    from pages import _3_Phenology_Dashboard as phenology
    phenology.main()
