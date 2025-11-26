import streamlit as st
import pandas as pd
from collections import defaultdict
import io

st.set_page_config(page_title="Kitchen Stock Checklist", layout="wide")

# Load Google Sheet CSV directly
@st.cache_data
def load_items():
    url = "https://docs.google.com/spreadsheets/d/1HGgv-EE6n3RSgSZxtCblIF51xqu80Y8j0_LORfK4ChU/export?format=csv"
    df = pd.read_csv(url)
    df.columns = ["Section", "Item", "SubItem", "MinQty", "DesiredQty"]
    df["SubItem"] = df["SubItem"].fillna("")   # <<< FIX HERE
    return df

df = load_items()

st.title("🏡 Kitchen Stock Checklist (Item/Sub-item Version)")

# Group by section and item
sections = defaultdict(lambda: defaultdict(list))

for _, row in df.iterrows():
    sections[row["Section"]][row["Item"]].append(row)

inputs = {}

with st.form("stock_form"):
    for section, items in sections.items():
        st.header(section)

        for item_name, rows in items.items():
            has_subitems = any(r["SubItem"] != "" for r in rows)

            if not has_subitems:
                # Single item
                only_row = rows[0]
                key = f"{section}-{item_name}"
