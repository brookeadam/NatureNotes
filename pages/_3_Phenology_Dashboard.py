import streamlit as st
import pandas as pd
import requests
import datetime

def main():
    # This is a test to ensure the connection works
    st.write("### Phenology Dashboard is Loading...")
    
    # Define the functions inside main so they are locally scoped
    @st.cache_data
    def load_pheno_data():
        try:
            return pd.read_csv("historical_pheno_data.csv")
        except:
            return pd.DataFrame()

    df = load_pheno_data()
    
    if not df.empty:
        st.success("Data loaded successfully!")
        st.dataframe(df.head())
    else:
        st.error("Could not find historical_pheno_data.csv in the root folder.")

# Ensure the function is available at the top level
if __name__ == "__main__":
    main()
