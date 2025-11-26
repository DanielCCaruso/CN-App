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

# Ensure expected columns exist
required_cols = {"Section", "Item", "Sub-Item", "Minimum", "Desired"}
missing = required_cols - set(df.columns)
if missing:
    st.error(f"Missing columns in sheet: {', '.join(sorted(missing))}")
    st.stop()

# Normalize values
df["Sub-Item"] = df["Sub-Item"].fillna("")
# Optional: sort for nicer rendering
df = df.sort_values(["Section", "Item", "Sub-Item"])

# === Build nested structure: sections -> items -> entries ===
# Structure:
# sections = {
#   "Pantry": {
#       "Rice": [ {"sub": "", "minimum": 2, "desired": 5}, ... ],
#       "Beans": [ ... ]
#   },
#   "Fridge": { ... }
# }
sections = {}
for _, row in df.iterrows():
    section = str(row["Section"]).strip()
    item = str(row["Item"]).strip()
    sub = str(row["Sub-Item"]).strip()
    minimum = row["Minimum"]
    desired = row["Desired"]

    if section not in sections:
        sections[section] = {}
    if item not in sections[section]:
        sections[section][item] = []
    sections[section][item].append({
        "sub": sub if sub else None,
        "minimum": minimum,
        "desired": desired
    })

# === Section navigation ===
if "section_index" not in st.session_state:
    st.session_state.section_index = 0

section_list = list(sections.keys())
current_section = section_list[st.session_state.section_index]

st.header(f"Section {st.session_state.section_index+1} of {len(section_list)}: {current_section}")

# === Render current section: show all items/sub-items under this section ===
# We display each Item as a container with its Sub-Items inputs.
for item_name, subentries in sections[current_section].items():
    with st.container():
        st.subheader(item_name)

        # Create columns for sub-items (limit columns to avoid overflow)
        # If many sub-items, render in rows of up to 4 columns
        max_cols = 4
        rows = [subentries[i:i+max_cols] for i in range(0, len(subentries), max_cols)]
        for row_entries in rows:
            cols = st.columns(len(row_entries))
            for col, entry in zip(cols, row_entries):
                sub = entry["sub"]
                label = sub if sub else item_name
                widget_key = f"{current_section}|{item_name}|{sub if sub else 'main'}"
                with col:
                    st.number_input(
                        label,
                        key=widget_key,
                        min_value=0,
                        value=int(entry["minimum"]) if not pd.isna(entry["minimum"]) else 0,
                        step=1
                    )

# === Navigation buttons ===
prev_col, next_col = st.columns([1, 1])

# Previous button
if prev_col.button("⬅️ Previous section") and st.session_state.section_index > 0:
    st.session_state.section_index -= 1
    st.rerun()

# Next button
if next_col.button("➡️ Next section") and st.session_state.section_index < len(section_list) - 1:
    st.session_state.section_index += 1
    st.rerun()
elif next_col.button("Finish") and st.session_state.section_index == len(section_list) - 1:
    st.success("✅ You’ve completed all sections!")

        # === Export after final section ===
        output_rows = []
        for section_name, items_dict in sections.items():
            for item_name, subentries in items_dict.items():
                for entry in subentries:
                    sub = entry["sub"] if entry["sub"] else ""
                    widget_key = f"{section_name}|{item_name}|{sub if sub else 'main'}"
                    qty = st.session_state.get(widget_key, 0)
                    output_rows.append({
                        "Section": section_name,
                        "Item": item_name,
                        "Sub-Item": sub,
                        "Quantity": qty
                    })

        csv_buffer = io.StringIO()
        pd.DataFrame(output_rows, columns=["Section", "Item", "Sub-Item", "Quantity"]).to_csv(
            csv_buffer, index=False
        )
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="📥 Download CSV report",
            data=csv_data,
            file_name="kitchen_stock_output.csv",
            mime="text/csv"
        )

        # === Results summary ===
        below_min = {}
        between_min_desired = {}

        for section_name, items_dict in sections.items():
            for item_name, subentries in items_dict.items():
                for entry in subentries:
                    sub = entry["sub"] if entry["sub"] else ""
                    minq = entry["minimum"]
                    desq = entry["desired"]

                    widget_key = f"{section_name}|{item_name}|{sub if sub else 'main'}"
                    qty = st.session_state.get(widget_key, 0)

                    if qty < minq:
                        below_min.setdefault(section_name, []).append((item_name, sub, qty, minq))
                    elif qty < desq:
                        between_min_desired.setdefault(section_name, []).append((item_name, sub, qty))

        st.header("📉 Items below minimum (red)")
        for section_name, items_list in below_min.items():
            st.subheader(section_name)
            for item_name, sub, qty, minq in items_list:
                if sub == "":
                    st.markdown(
                        f"<span style='color:red'>{item_name}: {qty} (min {minq})</span>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<span style='color:red'>{item_name} — {sub}: {qty} (min {minq})</span>",
                        unsafe_allow_html=True
                    )

        st.header("⚠️ Items between minimum and desired")
        for section_name, items_list in between_min_desired.items():
            st.subheader(section_name)
            for item_name, sub, qty in items_list:
                if sub == "":
                    st.write(f"{item_name}: {qty}")
                else:
                    st.write(f"{item_name} — {sub}: {qty}")
