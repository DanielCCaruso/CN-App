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
                inputs[key] = st.number_input(
                    item_name,
                    min_value=0,
                    value=0,
                    key=key
                )
            else:
                # Grouped sub-items
                st.subheader(item_name)
                cols = st.columns(len(rows))
                for col, r in zip(cols, rows):
                    label = r["SubItem"]
                    key = f"{section}-{item_name}-{label}"
                    with col:
                        inputs[key] = st.number_input(
                            label,
                            min_value=0,
                            value=0,
                            key=key
                        )

    submitted = st.form_submit_button("Submit")


if submitted:
    below_min = defaultdict(list)
    between_min_desired = defaultdict(list)

    output_rows = []

    for _, row in df.iterrows():
        section = row["Section"]
        item = row["Item"]
        sub = row["SubItem"]
        minq = row["MinQty"]
        desired = row["DesiredQty"]

        if sub == "":
            key = f"{section}-{item}"
        else:
            key = f"{section}-{item}-{sub}"

        qty = int(inputs[key])
        output_rows.append([section, item, sub, qty])

        # Classify
        if qty < minq:
            below_min[section].append((item, sub, qty, minq))
        elif minq <= qty < desired:
            between_min_desired[section].append((item, sub, qty))

    # CSV output
    csv_buffer = io.StringIO()
    pd.DataFrame(output_rows, columns=["Section", "Item", "SubItem", "Quantity"]).to_csv(
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
