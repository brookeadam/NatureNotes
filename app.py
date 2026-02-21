import streamlit as st

st.set_page_config(
    page_title="NatureNotes",
    page_icon="🌿",
    layout="wide"
)

st.title("NatureNotes Ecological Dashboard 🌿")

st.markdown("""
Welcome to **NatureNotes**.

Use the sidebar to navigate between:

- 🐦 eBird Observation Dashboard  
- 🦋 Butterfly Observation Dashboard  

""")

st.info("Select a page from the sidebar to begin.")

st.sidebar.write("Sidebar is active")
st.write("Main page")
