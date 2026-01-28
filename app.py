import streamlit as st
import pandas as pd

st.set_page_config(page_title="PTC Drilldown", layout="wide")

st.title("PTC Drilldown (Organized vs Pending)")

uploaded = st.file_uploader("Upload monthly Excel (.xlsx)", type=["xlsx"])

if not uploaded:
    st.info("Upload an Excel file to begin.")
    st.stop()

# Load sheets
org = pd.read_excel(uploaded, sheet_name="Organized")
pend = pd.read_excel(uploaded, sheet_name="Pending")

# Counts per your rules
organized_count = len(org)  # done count from Organized sheet
pending_count = (pend["Status"].astype(str).str.lower().eq("notdone").sum()
                 + pend["Status"].astype(str).str.lower().eq("offered").sum())

st.subheader("Chart 1: Organized vs Pending")
st.write({"Organized": int(organized_count), "Pending": int(pending_count)})
