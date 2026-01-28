import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="PTC Drilldown", layout="wide")

# ---------- Helpers ----------
def load_data(uploaded_file):
    org = pd.read_excel(uploaded_file, sheet_name="Organized")
    pend = pd.read_excel(uploaded_file, sheet_name="Pending")
    return org, pend

def normalize_status(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()

# ---------- App State ----------
if "screen" not in st.session_state:
    st.session_state.screen = "home"   # home | organized_titles | pending_split

st.title("PTC Drilldown")

uploaded = st.file_uploader("Upload monthly Excel (.xlsx)", type=["xlsx"])

if not uploaded:
    st.info("Upload an Excel file to begin.")
    st.stop()

org, pend = load_data(uploaded)

# ---------- HOME SCREEN ----------
if st.session_state.screen == "home":
    pend_status = normalize_status(pend["Status"])
    organized_count = int(len(org))
    pending_count = int((pend_status == "notdone").sum() + (pend_status == "offered").sum())

    df_top = pd.DataFrame(
        {"Category": ["Organized", "Pending"], "Count": [organized_count, pending_count]}
    )

    st.subheader("Chart 1: Organized vs Pending")
    fig = px.bar(df_top, x="Category", y="Count", text="Count")
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_title="Count", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Go: Organized", use_container_width=True):
            st.session_state.screen = "organized_titles"
            st.rerun()
    with col2:
        if st.button("Go: Pending", use_container_width=True):
            st.session_state.screen = "pending_split"
            st.rerun()

# ---------- ORGANIZED: Training Title vs Done ----------
elif st.session_state.screen == "organized_titles":
    st.subheader("Organized: Training Title vs Done count")

    # Back button
    if st.button("← Back to Chart 1"):
        st.session_state.screen = "home"
        st.rerun()

    # Group by Training Title
    title_counts = (
        org.groupby("Training Title", dropna=False)
        .size()
        .reset_index(name="Done Count")
        .sort_values("Done Count", ascending=False)
    )

    fig2 = px.bar(title_counts, x="Training Title", y="Done Count", text="Done Count")
    fig2.update_traces(textposition="outside")
    fig2.update_layout(xaxis_title="", yaxis_title="Done Count")
    st.plotly_chart(fig2, use_container_width=True)

    st.caption("Next step: make Training Title bars clickable → Department vs Done count → Employee list.")

# ---------- PENDING: NotDone vs Offered ----------
elif st.session_state.screen == "pending_split":
    st.subheader("Pending: NotDone vs Offered count")

    # Back button
    if st.button("← Back to Chart 1"):
        st.session_state.screen = "home"
        st.rerun()

    pend_status = normalize_status(pend["Status"])
    notdone_count = int((pend_status == "notdone").sum())
    offered_count = int((pend_status == "offered").sum())

    df_p = pd.DataFrame(
        {"Category": ["NotDone", "Offered"], "Count": [notdone_count, offered_count]}
    )

    figp = px.bar(df_p, x="Category", y="Count", text="Count")
    figp.update_traces(textposition="outside")
    figp.update_layout(xaxis_title="", yaxis_title="Count")
    st.plotly_chart(figp, use_container_width=True)

    st.caption("Next step: make NotDone/Offered clickable → Training Title charts for each branch.")
