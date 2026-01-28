import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="PTC Drilldown", layout="wide")

# ---------- Helpers ----------
@st.cache_data(show_spinner=False)
def load_data(file_bytes: bytes):
    org = pd.read_excel(BytesIO(file_bytes), sheet_name="Organized")
    pend = pd.read_excel(BytesIO(file_bytes), sheet_name="Pending")
    return org, pend

def normalize_status(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()

def get_selected_x(event):
    """Return the clicked bar's x value or None."""
    if not event:
        return None
    sel = event.get("selection")
    if not sel:
        return None
    pts = sel.get("points")
    if not pts:
        return None
    return pts[0].get("x")

def back_to_home():
    st.session_state.screen = "home"
    st.session_state.pending_branch = None
    st.session_state.selected_title = None
    st.session_state.selected_department = None
    st.rerun()

# ---------- State ----------
if "screen" not in st.session_state:
    st.session_state.screen = "home"
if "selected_title" not in st.session_state:
    st.session_state.selected_title = None
if "selected_department" not in st.session_state:
    st.session_state.selected_department = None
if "pending_branch" not in st.session_state:
    st.session_state.pending_branch = None  # "notdone" or "offered"

# ---------- UI ----------
st.title("PTC Drilldown")

uploaded = st.file_uploader("Upload monthly Excel (.xlsx)", type=["xlsx"])
if not uploaded:
    st.info("Upload an Excel file to begin.")
    st.stop()

file_bytes = uploaded.getvalue()
org, pend = load_data(file_bytes)

# Normalize Pending statuses for reliable filtering
pend = pend.copy()
pend["_status_norm"] = normalize_status(pend["Status"])

# ---------- HOME: Organized vs Pending ----------
if st.session_state.screen == "home":
    organized_count = int(len(org))
    pending_count = int((pend["_status_norm"] == "notdone").sum() + (pend["_status_norm"] == "offered").sum())

    df_top = pd.DataFrame(
        {"Category": ["Organized", "Pending"], "Count": [organized_count, pending_count]}
    )

    st.subheader("Chart 1: Organized vs Pending")

    fig = px.bar(df_top, x="Category", y="Count", text="Count")
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_title="Count", xaxis_title="", clickmode="event+select")

    event = st.plotly_chart(
        fig,
        key="top_chart",
        width="stretch",
        height=520,
        on_select="rerun",
        selection_mode=("points",),
    )

    clicked = get_selected_x(event)
    if clicked == "Organized":
        st.session_state.screen = "organized_titles"
        st.session_state.selected_title = None
        st.session_state.selected_department = None
        st.rerun()
    elif clicked == "Pending":
        st.session_state.screen = "pending_split"
        st.session_state.pending_branch = None
        st.session_state.selected_title = None
        st.session_state.selected_department = None
        st.rerun()

    st.caption("Click a bar to continue.")

# ---------- ORGANIZED: Training Title vs Done ----------
elif st.session_state.screen == "organized_titles":
    st.subheader("Organized: Training Title vs Done count")

    if st.button("← Back to Chart 1"):
        back_to_home()

    title_counts = (
        org.groupby("Training Title", dropna=False)
        .size()
        .reset_index(name="Done Count")
        .sort_values("Done Count", ascending=False)
    )

    fig2 = px.bar(title_counts, x="Training Title", y="Done Count", text="Done Count")
    fig2.update_traces(textposition="outside")
    fig2.update_layout(xaxis_title="", yaxis_title="Done Count", clickmode="event+select")

    event2 = st.plotly_chart(
        fig2,
        key="organized_titles_chart",
        width="stretch",
        height=520,
        on_select="rerun",
        selection_mode=("points",),
    )

    clicked = get_selected_x(event2)
    if clicked is not None:
        st.session_state.selected_title = clicked
        st.session_state.screen = "organized_departments"
        st.rerun()

    st.caption("Click a Training Title bar to see departments.")

# ---------- ORGANIZED: Department vs Done ----------
elif st.session_state.screen == "organized_departments":
    title = st.session_state.selected_title
    st.subheader(f"Organized: Department vs Done count — {title}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back to Training Titles"):
            st.session_state.screen = "organized_titles"
            st.session_state.selected_department = None
            st.rerun()
    with c2:
        if st.button("← Back to Chart 1"):
            back_to_home()

    df_filtered = org[org["Training Title"].astype(str) == str(title)]

    dept_counts = (
        df_filtered.groupby("Department", dropna=False)
        .size()
        .reset_index(name="Done Count")
        .sort_values("Done Count", ascending=False)
    )

    fig3 = px.bar(dept_counts, x="Department", y="Done Count", text="Done Count")
    fig3.update_traces(textposition="outside")
    fig3.update_layout(xaxis_title="", yaxis_title="Done Count", clickmode="event+select")

    event3 = st.plotly_chart(
        fig3,
        key="organized_dept_chart",
        width="stretch",
        height=520,
        on_select="rerun",
        selection_mode=("points",),
    )

    clicked = get_selected_x(event3)
    if clicked is not None:
        st.session_state.selected_department = clicked
        st.session_state.screen = "organized_employees"
        st.rerun()

    st.caption("Click a Department bar to see employees.")

# ---------- ORGANIZED: Employees (Done) ----------
elif st.session_state.screen == "organized_employees":
    title = st.session_state.selected_title
    dept = st.session_state.selected_department
    st.subheader(f"Employees (Done) — {title} / {dept}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back to Departments"):
            st.session_state.screen = "organized_departments"
            st.rerun()
    with c2:
        if st.button("← Back to Chart 1"):
            back_to_home()

    df_emp = org[
        (org["Training Title"].astype(str) == str(title)) &
        (org["Department"].astype(str) == str(dept))
    ].copy()

    show_cols = ["Staff ID", "Employee Name", "Desg Name", "Department", "Training Type", "Training Title", "Status"]
    existing_cols = [c for c in show_cols if c in df_emp.columns]
    st.dataframe(df_emp[existing_cols], use_container_width=True, hide_index=True)

# ---------- PENDING: NotDone vs Offered ----------
elif st.session_state.screen == "pending_split":
    st.subheader("Pending: NotDone vs Offered count")

    if st.button("← Back to Chart 1"):
        back_to_home()

    notdone_count = int((pend["_status_norm"] == "notdone").sum())
    offered_count = int((pend["_status_norm"] == "offered").sum())

    df_p = pd.DataFrame(
        {"Category": ["NotDone", "Offered"], "Count": [notdone_count, offered_count]}
    )

    figp = px.bar(df_p, x="Category", y="Count", text="Count")
    figp.update_traces(textposition="outside")
    figp.update_layout(xaxis_title="", yaxis_title="Count", clickmode="event+select")

    eventp = st.plotly_chart(
        figp,
        key="pending_split_chart",
        width="stretch",
        height=520,
        on_select="rerun",
        selection_mode=("points",),
    )

    clicked = get_selected_x(eventp)
    if clicked is not None:
        branch = str(clicked).strip().lower()
        if branch in ("notdone", "offered"):
            st.session_state.pending_branch = branch
            st.session_state.screen = "pending_titles"
            st.session_state.selected_title = None
            st.session_state.selected_department = None
            st.rerun()

    st.caption("Click NotDone or Offered to continue.")

# ---------- PENDING: Training Title vs Count ----------
elif st.session_state.screen == "pending_titles":
    branch = st.session_state.pending_branch  # "notdone" or "offered"
    label = "NotDone" if branch == "notdone" else "Offered"
    st.subheader(f"Pending ({label}): Training Title vs Count")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back to NotDone/Offered"):
            st.session_state.screen = "pending_split"
            st.session_state.selected_title = None
            st.session_state.selected_department = None
            st.rerun()
    with c2:
        if st.button("← Back to Chart 1"):
            back_to_home()

    df_branch = pend[pend["_status_norm"] == branch]

    title_counts = (
        df_branch.groupby("Training Title", dropna=False)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )

    figt = px.bar(title_counts, x="Training Title", y="Count", text="Count")
    figt.update_traces(textposition="outside")
    figt.update_layout(xaxis_title="", yaxis_title="Count", clickmode="event+select")

    eventt = st.plotly_chart(
        figt,
        key=f"pending_titles_{branch}",
        width="stretch",
        height=520,
        on_select="rerun",
        selection_mode=("points",),
    )

    clicked = get_selected_x(eventt)
    if clicked is not None:
        st.session_state.selected_title = clicked
        st.session_state.screen = "pending_departments"
        st.rerun()

    st.caption("Click a Training Title bar to see departments.")

# ---------- PENDING: Department vs Count ----------
elif st.session_state.screen == "pending_departments":
    branch = st.session_state.pending_branch
    label = "NotDone" if branch == "notdone" else "Offered"
    title = st.session_state.selected_title

    st.subheader(f"Pending ({label}): Department vs Count — {title}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back to Training Titles"):
            st.session_state.screen = "pending_titles"
            st.session_state.selected_department = None
            st.rerun()
    with c2:
        if st.button("← Back to Chart 1"):
            back_to_home()

    df_filtered = pend[
        (pend["_status_norm"] == branch) &
        (pend["Training Title"].astype(str) == str(title))
    ]

    dept_counts = (
        df_filtered.groupby("Department", dropna=False)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )

    figd = px.bar(dept_counts, x="Department", y="Count", text="Count")
    figd.update_traces(textposition="outside")
    figd.update_layout(xaxis_title="", yaxis_title="Count", clickmode="event+select")

    eventd = st.plotly_chart(
        figd,
        key=f"pending_dept_{branch}",
        width="stretch",
        height=520,
        on_select="rerun",
        selection_mode=("points",),
    )

    clicked = get_selected_x(eventd)
    if clicked is not None:
        st.session_state.selected_department = clicked
        st.session_state.screen = "pending_employees"
        st.rerun()

    st.caption("Click a Department bar to see employees.")

# ---------- PENDING: Employees (NotDone / Offered) ----------
elif st.session_state.screen == "pending_employees":
    branch = st.session_state.pending_branch
    label = "NotDone" if branch == "notdone" else "Offered"
    title = st.session_state.selected_title
    dept = st.session_state.selected_department

    st.subheader(f"Employees ({label}) — {title} / {dept}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back to Departments"):
            st.session_state.screen = "pending_departments"
            st.rerun()
    with c2:
        if st.button("← Back to Chart 1"):
            back_to_home()

    df_emp = pend[
        (pend["_status_norm"] == branch) &
        (pend["Training Title"].astype(str) == str(title)) &
        (pend["Department"].astype(str) == str(dept))
    ].copy()

    show_cols = ["Staff ID", "Employee Name", "Desg Name", "Department", "Training Type", "Training Title", "Status"]
    existing_cols = [c for c in show_cols if c in df_emp.columns]
    st.dataframe(df_emp[existing_cols], use_container_width=True, hide_index=True)
