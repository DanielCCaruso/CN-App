import streamlit as st
import pandas as pd
import requests
import io

st.title("CN Kitchen Checklist")

# === Load Google Sheet ===
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1HGgv-EE6n3RSgSZxtCblIF51xqu80Y8j0_LORfK4ChU/export?format=csv"

@st.cache_data(ttl=0)
def load_sheet():
    content = requests.get(SHEET_CSV_URL).content
    df = pd.read_csv(io.BytesIO(content))
    return df

df = load_sheet()
df = df.rename(columns=lambda x: x.strip())
df["Sub-Item"] = df["Sub-Item"].fillna("")

# === Build nested structure ===
items = {}
for _, row in df.iterrows():
    item = row["Item"]
    sub = row["Sub-Item"]
    minimum = row["Minimum"]
    desired = row["Desired"]
    if item not in items:
        items[item] = []
    items[item].append({
        "sub": sub if sub.strip() else None,
        "minimum": minimum,
        "desired": desired
    })

# === Section navigation ===
if "section_index" not in st.session_state:
    st.session_state.section_index = 0

sections = list(items.keys())
current_section = sections[st.session_state.section_index]

st.header(f"Section {st.session_state.section_index+1} of {len(sections)}: {current_section}")

# Render only the current section
subitems = items[current_section]
cols = st.columns(len(subitems))
for col, entry in zip(cols, subitems):
    sub = entry["sub"]
    label = sub if sub else current_section
    widget_key = f"{current_section}_{sub if sub else 'main'}"
    with col:
        st.number_input(
            label,
            key=widget_key,
            min_value=0,
            value=int(entry["minimum"]) if not pd.isna(entry["minimum"]) else 0,
