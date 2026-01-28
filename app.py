import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="PTC Drilldown", layout="wide")
st.title("PTC Drilldown")

uploaded = st.file_uploader("Upload monthly Excel (.xlsx)", type=["xlsx"])

if not uploaded:
    st.info("Upload an Excel file to begin.")
    st.stop()

# Load sheets
org = pd.read_excel(uploaded, sheet_name="Organized")
pend = pd.read_excel(uploaded, sheet_name="Pending")

# Normalize Status text
pend_status = pend["Status"].astype(str).str.strip().str.lower()

organized_count = len(org)  # Organized sheet = done rows
pending_count = int((pend_status == "notdone").sum() + (pend_status == "offered").sum())

df_top = pd.DataFrame(
    {
        "Category": ["Organized", "Pending"],
        "Count": [int(organized_count), int(pending_count)],
    }
)

st.subheader("Chart 1: Organized vs Pending")

fig = px.bar(df_top, x="Category", y="Count", text="Count")
fig.update_traces(textposition="outside")
fig.update_layout(yaxis_title="Count", xaxis_title="", uniformtext_minsize=10, uniformtext_mode="hide")

st.plotly_chart(fig, use_container_width=True)

# Temporary click UI (real click navigation next step)
col1, col2 = st.columns(2)
with col1:
    if st.button("Go: Organized"):
        st.session_state["path"] = "organized"
with col2:
    if st.button("Go: Pending"):
        st.session_state["path"] = "pending"

st.caption("Next step: we’ll make these buttons become true page navigation and build the Organized/Pending pages.")
