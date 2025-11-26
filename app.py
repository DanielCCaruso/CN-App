import streamlit as st
import pandas as pd
import requests
import io

st.title("Kitchen Checklist – Dynamic Google Sheet")

# === 1) Load Google Sheet dynamically ===
SHEET_CSV_URL = "PASTE_YOUR_GOOGLE_SHEET_CSV_URL_HERE"

@st.cache_data(ttl=0)   # always re-download unless the user manually refreshes
def load_sheet():
    content = requests.get(SHEET_CSV_URL).content
    df = pd.read_csv(io.BytesIO(co_
