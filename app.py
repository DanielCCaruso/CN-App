import streamlit as st
import pandas as pd
import requests
import io

st.title("Kitchen Checklist – Dynamic Google Sheet")

# === 1) Load Google Sheet dynamically ===
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1HGgv-EE6n3RSgSZxtCblIF51xqu80Y8j0_LORfK4ChU/export?format=csv"

@st.cache_data(ttl=0)   # always re-download unless the user manually refreshes
def load_sheet():
    content = requests.get(SHEET_CSV_URL).content
    df = pd.read_csv(io.BytesIO(content))
    return df

df = load_sheet()

# REQUIRED COLUMNS:
# B = Item
# C = Sub-item
# D = Minimum
# E = Desired

# Clean data
df = df.rename(columns=lambda x: x.strip())  # remove accidental spaces

# Remove NaN sub-items by replacing with empty string
df["Sub-item"] = df["Sub-item"].fillna("")

# === 2) Build nested structure ===
# Group by item
items = {}

for _, row in df.iterrows():
    item = row["Item"]
    sub = row["Sub-item"]
    minimum = row["Minimum"]
    desired = row["Desired"]

    if item not in items:
        items[item] = []

    # Only append sub-items if a sub-item exists
    if sub.strip() != "":
        items[item].append({
            "sub": sub,
            "minimum": minimum,
            "desired": desired
        })
    else:
        # Item only (no subitems)
        items[item].append({
            "sub": None,
            "minimum": minimum,
            "desired": desired
        })

# === 3) Render form ===
# === 3) Render form ===
st.header("Checklist Form")

output_rows = []

for item, subitems in items.items():
    with st.expander(item, expanded=True):

        # One horizontal row for all sub-items
        cols = st.columns(len(subitems))

        for col, entry in zip(cols, subitems):
            sub = entry["sub"]

            label = sub if sub else item

            with col:
                qty = st.number_input(
                    label,
                    min_value=0,
                    value=int(entry["minimum"]) if not pd.isna(entry["minimum"]) else 0,
                    step=1
                )

            output_rows.append({
                "Item": item,
                "Sub-item": sub if sub else "",
                "Quantity": qty
            })


# === 4) Export ===
st.header("Download Checklist Results")

output_df = pd.DataFrame(output_rows)

csv = output_df.to_csv(index=False)

st.download_button(
    "Download CSV",
    csv,
    "checklist_output.csv",
    "text/csv"
)

