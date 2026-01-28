import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import time

st.set_page_config(page_title="PTC Drilldown", layout="wide")

# ---------- App styling ----------
st.markdown(
    """
    <style>
      .stApp { background: #fbfbfd; }
      h1, h2, h3 { letter-spacing: -0.02em; }

      section[data-testid="stFileUploaderDropzone"] {
        border: 1px dashed rgba(0,0,0,0.15);
        border-radius: 14px;
        background: rgba(255,255,255,0.85);
        padding: 16px;
      }

      div.stButton > button {
        border-radius: 999px;
        padding: 0.55rem 0.95rem;
        border: 1px solid rgba(0,0,0,0.08);
        background: white;
      }
      div.stButton > button:hover {
        border: 1px solid rgba(0,0,0,0.18);
        background: rgba(255,255,255,0.95);
      }

      div[data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid rgba(0,0,0,0.08);
        background: white;
      }

      .card {
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 18px;
        background: white;
        padding: 14px 16px;
        box-shadow: 0 6px 24px rgba(0,0,0,0.04);
        margin-bottom: 14px;
      }

      .crumb {
        font-size: 0.95rem;
        color: rgba(0,0,0,0.65);
        margin-top: -6px;
        margin-bottom: 8px;
      }
      .crumb b { color: rgba(0,0,0,0.86); }

      footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Helpers ----------
@st.cache_data(show_spinner=False)
def load_data(file_bytes: bytes):
    org = pd.read_excel(BytesIO(file_bytes), sheet_name="Organized")
    pend = pd.read_excel(BytesIO(file_bytes), sheet_name="Pending")
    return org, pend

def normalize_status(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()

def get_selected_x(event):
    if not event:
        return None
    sel = event.get("selection")
    if not sel:
        return None
    pts = sel.get("points")
    if not pts:
        return None
    return pts[0].get("x")

def go(screen: str, title=None, dept=None, branch=None):
    with st.spinner("Loading…"):
        time.sleep(0.18)
    st.session_state.screen = screen
    if title is not None:
        st.session_state.selected_title = title
    if dept is not None:
        st.session_state.selected_department = dept
    if branch is not None:
        st.session_state.pending_branch = branch
    st.rerun()

def reset_to_home():
    st.session_state.screen = "home"
    st.session_state.pending_branch = None
    st.session_state.selected_title = None
    st.session_state.selected_department = None

def crumb(text: str):
    st.markdown(f'<div class="crumb">{text}</div>', unsafe_allow_html=True)

def card_open():
    st.markdown('<div class="card">', unsafe_allow_html=True)

def card_close():
    st.markdown("</div>", unsafe_allow_html=True)

def apply_hover_style(fig, font_size=18, box_border=1):
    """Make hover tooltip bigger and cleaner."""
    fig.update_layout(
        hoverlabel=dict(
            font_size=font_size,
            bordercolor="rgba(0,0,0,0.25)",
            bgcolor="white",
            namelength=-1,
        )
    )
    # remove the small "trace name" grey box
    fig.update_traces(hovertemplate=fig.data[0].hovertemplate if fig.data else None)
    return fig

def make_indexed_bar(df, label_col, value_col, hover_label_name, hover_value_name):
    """
    X axis uses Rank (1..N), no long labels.
    Hover shows the real label + value.
    No text labels drawn on top of bars.
    """
    d = df.copy().reset_index(drop=True)
    d["Rank"] = range(1, len(d) + 1)

    fig = px.bar(
        d,
        x="Rank",
        y=value_col,
        hover_data={
            "Rank": False,
            label_col: True,
            value_col: True,
        },
    )

    # custom hover text (big)
    fig.update_traces(
        customdata=d[[label_col]].to_numpy(),
        hovertemplate=(
            f"{hover_label_name}: %{{customdata[0]}}<br>"
            f"{hover_value_name}: %{{y}}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        xaxis_title="",
        yaxis_title=hover_value_name,
        clickmode="event+select",
        xaxis=dict(showticklabels=False, ticks=""),
        margin=dict(l=10, r=10, t=10, b=10),
    )

    apply_hover_style(fig, font_size=18)
    return fig, d

def simple_bar(df, xcol, ycol, ytitle, hover_x_name=None, hover_y_name=None):
    """Simple bar with NO top labels; hover-only info."""
    fig = px.bar(df, x=xcol, y=ycol)
    if hover_x_name is None:
        hover_x_name = xcol
    if hover_y_name is None:
        hover_y_name = ytitle

    fig.update_traces(
        hovertemplate=f"{hover_x_name}: %{{x}}<br>{hover_y_name}: %{{y}}<extra></extra>"
    )
    fig.update_layout(
        xaxis_title="",
        yaxis_title=ytitle,
        clickmode="event+select",
        margin=dict(l=10, r=10, t=10, b=10),
    )
    apply_hover_style(fig, font_size=18)
    return fig

# ---------- State ----------
if "screen" not in st.session_state:
    st.session_state.screen = "home"
if "selected_title" not in st.session_state:
    st.session_state.selected_title = None
if "selected_department" not in st.session_state:
    st.session_state.selected_department = None
if "pending_branch" not in st.session_state:
    st.session_state.pending_branch = None  # "notdone" or "offered"

# ---------- Header ----------
left, right = st.columns([0.78, 0.22])
with left:
    st.markdown("## PTC Training Status")
    st.caption("Click charts to drill down • Hover bars to see details")
with right:
    if st.button("Reset", use_container_width=True):
        reset_to_home()
        st.rerun()

uploaded = st.file_uploader("Upload monthly Excel (.xlsx)", type=["xlsx"])

if not uploaded:
    card_open()
    st.markdown("### Get started")
    st.write("Upload your monthly Excel file containing **Organized** and **Pending** sheets.")
    st.write("Then click the bars to drill down.")
    card_close()
    st.stop()

file_bytes = uploaded.getvalue()
org, pend = load_data(file_bytes)

pend = pend.copy()
pend["_status_norm"] = normalize_status(pend["Status"])

# ---------- HOME ----------
if st.session_state.screen == "home":
    crumb("<b>Home</b>")

    organized_count = int(len(org))
    pending_count = int((pend["_status_norm"] == "notdone").sum() + (pend["_status_norm"] == "offered").sum())
    df_top = pd.DataFrame({"Category": ["Organized", "Pending"], "Count": [organized_count, pending_count]})

    card_open()
    st.markdown("### Organized vs Pending")
    fig = simple_bar(df_top, "Category", "Count", "Count", hover_x_name="Category", hover_y_name="Count")

    event = st.plotly_chart(fig, key="top_chart", width="stretch", height=520, on_select="rerun", selection_mode=("points",))
    card_close()

    clicked = get_selected_x(event)
    if clicked == "Organized":
        go("organized_titles")
    elif clicked == "Pending":
        go("pending_split")

# ---------- ORGANIZED: Training Titles ----------
elif st.session_state.screen == "organized_titles":
    crumb('Home → <b>Organized</b> → Training Titles')

    c1, c2 = st.columns([0.15, 0.85])
    with c1:
        if st.button("← Back"):
            go("home")
    with c2:
        st.markdown("### Training Title vs Done count")

    title_counts = (
        org.groupby("Training Title", dropna=False)
        .size()
        .reset_index(name="Done Count")
        .sort_values("Done Count", ascending=False)
    )

    fig2, d2 = make_indexed_bar(
        title_counts,
        label_col="Training Title",
        value_col="Done Count",
        hover_label_name="Training Title",
        hover_value_name="Done Count",
    )

    card_open()
    event2 = st.plotly_chart(fig2, key="organized_titles_chart", width="stretch", height=520, on_select="rerun", selection_mode=("points",))
    card_close()

    clicked_rank = get_selected_x(event2)
    if clicked_rank is not None:
        try:
            idx = int(clicked_rank) - 1
            if 0 <= idx < len(d2):
                go("organized_departments", title=d2.loc[idx, "Training Title"])
        except Exception:
            pass

# ---------- ORGANIZED: Department ----------
elif st.session_state.screen == "organized_departments":
    title = st.session_state.selected_title
    crumb(f'Home → Organized → <b>{title}</b> → Departments')

    c1, c2 = st.columns([0.15, 0.85])
    with c1:
        if st.button("← Back"):
            go("organized_titles")
    with c2:
        st.markdown("### Department vs Done count")

    df_filtered = org[org["Training Title"].astype(str) == str(title)]
    dept_counts = (
        df_filtered.groupby("Department", dropna=False)
        .size()
        .reset_index(name="Done Count")
        .sort_values("Done Count", ascending=False)
    )

    card_open()
    fig3 = simple_bar(dept_counts, "Department", "Done Count", "Done Count", hover_x_name="Department", hover_y_name="Done Count")
    event3 = st.plotly_chart(fig3, key="organized_dept_chart", width="stretch", height=520, on_select="rerun", selection_mode=("points",))
    card_close()

    clicked = get_selected_x(event3)
    if clicked is not None:
        go("organized_employees", dept=clicked)

# ---------- ORGANIZED: Employees ----------
elif st.session_state.screen == "organized_employees":
    title = st.session_state.selected_title
    dept = st.session_state.selected_department
    crumb(f'Home → Organized → {title} → <b>{dept}</b> → Employees (Done)')

    c1, c2 = st.columns([0.15, 0.85])
    with c1:
        if st.button("← Back"):
            go("organized_departments")
    with c2:
        st.markdown("### Employee information (Done)")

    df_emp = org[
        (org["Training Title"].astype(str) == str(title)) &
        (org["Department"].astype(str) == str(dept))
    ].copy()

    show_cols = ["Staff ID", "Employee Name", "Desg Name", "Department", "Training Type", "Training Title", "Status"]
    existing_cols = [c for c in show_cols if c in df_emp.columns]

    card_open()
    st.dataframe(df_emp[existing_cols], use_container_width=True, hide_index=True)
    card_close()

# ---------- PENDING: Split ----------
elif st.session_state.screen == "pending_split":
    crumb('Home → <b>Pending</b> → NotDone / Offered')

    c1, c2 = st.columns([0.15, 0.85])
    with c1:
        if st.button("← Back"):
            go("home")
    with c2:
        st.markdown("### NotDone vs Offered count")

    notdone_count = int((pend["_status_norm"] == "notdone").sum())
    offered_count = int((pend["_status_norm"] == "offered").sum())
    df_p = pd.DataFrame({"Category": ["NotDone", "Offered"], "Count": [notdone_count, offered_count]})

    card_open()
    figp = simple_bar(df_p, "Category", "Count", "Count", hover_x_name="Category", hover_y_name="Count")
    eventp = st.plotly_chart(figp, key="pending_split_chart", width="stretch", height=520, on_select="rerun", selection_mode=("points",))
    card_close()

    clicked = get_selected_x(eventp)
    if clicked is not None:
        branch = str(clicked).strip().lower()
        if branch in ("notdone", "offered"):
            go("pending_titles", branch=branch)

# ---------- PENDING: Training Titles ----------
elif st.session_state.screen == "pending_titles":
    branch = st.session_state.pending_branch
    label = "NotDone" if branch == "notdone" else "Offered"
    crumb(f'Home → Pending → <b>{label}</b> → Training Titles')

    c1, c2 = st.columns([0.15, 0.85])
    with c1:
        if st.button("← Back"):
            go("pending_split")
    with c2:
        st.markdown(f"### Training Title vs {label} count")

    df_branch = pend[pend["_status_norm"] == branch]
    title_counts = (
        df_branch.groupby("Training Title", dropna=False)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )

    figt, dt = make_indexed_bar(
        title_counts,
        label_col="Training Title",
        value_col="Count",
        hover_label_name="Training Title",
        hover_value_name=f"{label} Count",
    )

    card_open()
    eventt = st.plotly_chart(figt, key=f"pending_titles_{branch}", width="stretch", height=520, on_select="rerun", selection_mode=("points",))
    card_close()

    clicked_rank = get_selected_x(eventt)
    if clicked_rank is not None:
        try:
            idx = int(clicked_rank) - 1
            if 0 <= idx < len(dt):
                go("pending_departments", title=dt.loc[idx, "Training Title"])
        except Exception:
            pass

# ---------- PENDING: Departments ----------
elif st.session_state.screen == "pending_departments":
    branch = st.session_state.pending_branch
    label = "NotDone" if branch == "notdone" else "Offered"
    title = st.session_state.selected_title
    crumb(f'Home → Pending → {label} → <b>{title}</b> → Departments')

    c1, c2 = st.columns([0.15, 0.85])
    with c1:
        if st.button("← Back"):
            go("pending_titles")
    with c2:
        st.markdown(f"### Department vs {label} count")

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

    card_open()
    figd = simple_bar(dept_counts, "Department", "Count", "Count", hover_x_name="Department", hover_y_name=f"{label} Count")
    eventd = st.plotly_chart(figd, key=f"pending_dept_{branch}", width="stretch", height=520, on_select="rerun", selection_mode=("points",))
    card_close()

    clicked = get_selected_x(eventd)
    if clicked is not None:
        go("pending_employees", dept=clicked)

# ---------- PENDING: Employees ----------
elif st.session_state.screen == "pending_employees":
    branch = st.session_state.pending_branch
    label = "NotDone" if branch == "notdone" else "Offered"
    title = st.session_state.selected_title
    dept = st.session_state.selected_department
    crumb(f'Home → Pending → {label} → {title} → <b>{dept}</b> → Employees')

    c1, c2 = st.columns([0.15, 0.85])
    with c1:
        if st.button("← Back"):
            go("pending_departments")
    with c2:
        st.markdown(f"### Employee information ({label})")

    df_emp = pend[
        (pend["_status_norm"] == branch) &
        (pend["Training Title"].astype(str) == str(title)) &
        (pend["Department"].astype(str) == str(dept))
    ].copy()

    show_cols = ["Staff ID", "Employee Name", "Desg Name", "Department", "Training Type", "Training Title", "Status"]
    existing_cols = [c for c in show_cols if c in df_emp.columns]

    card_open()
    st.dataframe(df_emp[existing_cols], use_container_width=True, hide_index=True)
    card_close()
