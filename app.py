import streamlit as st
import pandas as pd
import requests
import io

st.title("CN Kitchen Checklist")

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
    sub = row["Sub-Item"]
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
st.header("Checklist Form")

output_rows = []

for item, subitems in items.items():
    with st.expander(item, expanded=True):

        cols = st.columns(len(subitems))

        for col, entry in zip(cols, subitems):

            sub = entry["sub"]
            label = sub if sub else item
            widget_key = f"{item}_{sub if sub else 'main'}"

            with col:
                qty = st.number_input(
                    label,
                    key=widget_key,
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
    csv_buffer = io.StringIO()
    pd.DataFrame(output_rows, columns=["Section", "Item", "Sub-Item", "Quantity"]).to_csv(
        csv_buffer, index=False
    )
    csv_data = csv_buffer.getvalue()

    st.download_button(
        label="📥 Download CSV Report",
        data=csv_data,
        file_name="kitchen_stock_output.csv",
        mime="text/csv"
    )

    # Results
    st.header("📉 Items Below Minimum (Red)")
    for section, items in below_min.items():
        st.subheader(section)
        for item, sub, qty, minq in items:
            if sub == "":
                st.markdown(f"<span style='color:red'>{item}: {qty} (min {minq})</span>",
                            unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:red'>{item} — {sub}: {qty} (min {minq})</span>",
                            unsafe_allow_html=True)

    st.header("⚠️ Items Between Minimum and Desired")
    for section, items in between_min_desired.items():
        st.subheader(section)
        for item, sub, qty in items:
            if sub == "":
                st.write(f"{item}: {qty}")
            else:
                st.write(f"{item} — {sub}: {qty}")
