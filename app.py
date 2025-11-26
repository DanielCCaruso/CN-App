import streamlit as st
import pandas as pd
from collections import defaultdict
import io

st.set_page_config(page_title="Kitchen Stock Checklist", layout="centered")

# Load Google Sheet CSV directly
@st.cache_data
def load_items():
    url = "https://docs.google.com/spreadsheets/d/1HGgv-EE6n3RSgSZxtCblIF51xqu80Y8j0_LORfK4ChU/export?format=csv"
    df = pd.read_csv(url)
    df.columns = ["Section", "Item", "MinQty", "DesiredQty"]
    return df

df = load_items()

st.title("🏡 Kitchen Stock Checklist")
st.write("Enter the quantities for each item below:")

sections = df.groupby("Section")
inputs = {}

with st.form("stock_form"):
    for section, items in sections:
        st.subheader(section)
        for _, row in items.iterrows():
            key = f"{section}-{row['Item']}"
            qty = st.number_input(
                row["Item"],
                min_value=0,
                value=0,
                key=key
            )
            inputs[key] = qty

    submitted = st.form_submit_button("Submit")


if submitted:
    below_min = defaultdict(list)
    between_min_desired = defaultdict(list)

    output_rows = []

    # Process inputs
    for _, row in df.iterrows():
        key = f"{row['Section']}-{row['Item']}"
        qty = int(inputs[key])
        output_rows.append([row["Section"], row["Item"], qty])

        if qty < row["MinQty"]:
            below_min[row["Section"]].append((row["Item"], qty, row["MinQty"]))
        elif row["MinQty"] <= qty < row["DesiredQty"]:
            between_min_desired[row["Section"]].append((row["Item"], qty))

    # CSV output
    csv_buffer = io.StringIO()
    pd.DataFrame(output_rows, columns=["Section", "Item", "Quantity"]).to_csv(
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
    st.header("📉 Items Below Minimum")
    for section, items in below_min.items():
        st.subheader(section)
        for item, qty, minq in items:
            st.markdown(
                f"<span style='color:red'>{item}: {qty} (min {minq})</span>",
                unsafe_allow_html=True
            )

    st.header("⚠️ Items Between Minimum and Desired")
    for section, items in between_min_desired.items():
        st.subheader(section)
        for item, qty in items:
            st.write(f"{item}: {qty}")
