import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="PTC Drilldown", layout="wide")

# ---------- App styling ----------
st.markdown(
    """
    <style>
      @keyframes softFade {
        0% { opacity: 0; }
        100% { opacity: 1; }
      }

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
        animation: softFade 0.4s ease-out;
      }

      .card {
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 18px;
        background: white;
        padding: 14px 16px;
        box-shadow: 0 6px 24px rgba(0,0,0,0.04);
        margin-bottom: 14px;
        animation: softFade 0.4s ease-out;
      }

      .crumb {
        font-size: 0.95rem;
        color: rgba(0,0,0,0.65);
        margin-top: -6px;
        margin-bottom: 8px;
        animation: softFade 0.3s ease-out;
      }
      .crumb b { color: rgba(0,0,0,0.86); }

      footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Theme Colors ----------
COLOR_MAP = {
    "Done": "#10b981",       # Emerald Green
    "Offered": "#3b82f6",    # Blue
    "Not Done": "#ef4444",   # Rose Red
    "Default": "#6b7280"     # Gray
}

# ---------- State Initialization ----------
if "screen" not in st.session_state:
    st.session_state.screen = "home"
if "selected_status" not in st.session_state:
    st.session_state.selected_status = None 
if "selected_title" not in st.session_state:
    st.session_state.selected_title = None
if "selected_department" not in st.session_state:
    st.session_state.selected_department = None
if "file_bytes" not in st.session_state:
    st.session_state.file_bytes = None

# ---------- Helpers ----------
@st.cache_data(show_spinner=False)
def load_data(file_bytes: bytes):
    org = pd.read_excel(BytesIO(file_bytes), sheet_name="Organized")
    pend = pd.read_excel(BytesIO(file_bytes), sheet_name="Pending")
    
    # 🚨 FIX: Automatically strip invisible spaces from all column names 
    org.columns = org.columns.astype(str).str.strip()
    pend.columns = pend.columns.astype(str).str.strip()
    
    return org, pend

def normalize_status(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()

def get_selected_x(event):
    if not event or not event.get("selection") or not event.get("selection").get("points"):
        return None
    return event["selection"]["points"][0].get("x")

def go(screen: str, status=None, title=None, dept=None):
    st.session_state.screen = screen
    if status is not None:
        st.session_state.selected_status = status
    if title is not None:
        st.session_state.selected_title = title
    if dept is not None:
        st.session_state.selected_department = dept
    st.rerun()

def reset_to_home():
    st.session_state.screen = "home"
    st.session_state.selected_status = None
    st.session_state.selected_title = None
    st.session_state.selected_department = None

def full_reset():
    st.session_state.clear()
    st.rerun()

def crumb(text: str):
    st.markdown(f'<div class="crumb">{text}</div>', unsafe_allow_html=True)

def card_open():
    st.markdown('<div class="card">', unsafe_allow_html=True)

def card_close():
    st.markdown("</div>", unsafe_allow_html=True)

def bar_with_labels(df, xcol, ycol, ytitle, color_col=None, hover_x_name=None, hover_y_name=None, pct_col=None):
    if hover_x_name is None: hover_x_name = xcol
    if hover_y_name is None: hover_y_name = ytitle

    # Setup custom data for hover template
    if pct_col and pct_col in df.columns:
        fig = px.bar(df, x=xcol, y=ycol, text=ycol, color=color_col, color_discrete_map=COLOR_MAP, custom_data=[pct_col])
        htemplate = f"{hover_x_name}: %{{x}}<br>{hover_y_name}: %{{y}}<br>Percentage: %{{customdata[0]}}<extra></extra>"
    else:
        fig = px.bar(df, x=xcol, y=ycol, text=ycol, color=color_col, color_discrete_map=COLOR_MAP)
        htemplate = f"{hover_x_name}: %{{x}}<br>{hover_y_name}: %{{y}}<extra></extra>"

    # Force 100% opacity on click so bars don't fade
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=htemplate,
        selected=dict(marker=dict(opacity=1)),
        unselected=dict(marker=dict(opacity=1))
    )

    fig.update_layout(
        xaxis_title="",
        yaxis_title=ytitle,
        clickmode="event+select",
        margin=dict(l=10, r=10, t=10, b=10),
        uniformtext_minsize=10,
        uniformtext_mode="hide",
        showlegend=False,
        hoverlabel=dict(font_size=16, bgcolor="white", bordercolor="rgba(0,0,0,0.25)", namelength=-1)
    )
    return fig

# ---------- Main Logic ----------

# 1. Show Upload Screen if no file is uploaded
if st.session_state.file_bytes is None:
    st.markdown("## PTC Training Status")
    card_open()
    st.markdown("### Get started")
    st.write("Upload your monthly Excel file containing **Organized** and **Pending** sheets.")
    uploaded = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])
    if uploaded:
        st.session_state.file_bytes = uploaded.getvalue()
        st.rerun()
    card_close()
    st.stop()

# 2. File is uploaded - Load Data
org, pend = load_data(st.session_state.file_bytes)
pend = pend.copy()
pend["_status_norm"] = normalize_status(pend["Status"])

def get_current_df():
    status = st.session_state.selected_status
    if status == "done": return org
    elif status in ["offered", "notdone"]: return pend[pend["_status_norm"] == status]
    return pd.DataFrame()

def get_status_label():
    return {"done": "Done", "offered": "Offered", "notdone": "Not Done"}.get(st.session_state.selected_status, "Default")

# ---------- Header (Data Loaded) ----------
left, right = st.columns([0.80, 0.20])
with left:
    st.markdown("## PTC Training Status")
with right:
    # Changed to completely reset the app so they can upload a new file if needed
    if st.button("Start Over", use_container_width=True):
        full_reset()

# ---------- HOME ----------
if st.session_state.screen == "home":
    crumb("<b>Home</b>")

    done_count = int(len(org))
    offered_count = int((pend["_status_norm"] == "offered").sum())
    notdone_count = int((pend["_status_norm"] == "notdone").sum())
    total_count = done_count + offered_count + notdone_count
    
    df_top = pd.DataFrame({
        "Category": ["Done", "Offered", "Not Done"], 
        "Count": [done_count, offered_count, notdone_count]
    })
    
    df_top["Percentage"] = df_top["Count"].apply(lambda x: f"{(x / total_count * 100):.1f}%" if total_count > 0 else "0.0%")

    card_open()
    st.markdown("### Overall Status")
    
    fig = bar_with_labels(
        df_top, "Category", "Count", "Count", 
        color_col="Category", hover_x_name="Status", hover_y_name="Count", pct_col="Percentage"
    )

    event = st.plotly_chart(fig, key="top_chart", width="stretch", height=520, on_select="rerun", selection_mode=("points",))
    card_close()

    clicked = get_selected_x(event)
    if clicked == "Done": go("titles", status="done")
    elif clicked == "Offered": go("titles", status="offered")
    elif clicked == "Not Done": go("titles", status="notdone")

# ---------- TITLES ----------
elif st.session_state.screen == "titles":
    label = get_status_label()
    crumb(f'Home → <b>{label}</b> → Training Titles')

    c1, c2 = st.columns([0.15, 0.85])
    with c1:
        if st.button("← Back"): reset_to_home()
    with c2:
        st.markdown(f"### Training Title vs {label} Count")

    df_current = get_current_df()
    
    # 🚨 FIX: Safety check to prevent app crashes if columns are missing
    if "Training Title" not in df_current.columns:
        st.error("⚠️ Column 'Training Title' is missing from this sheet. Please check your Excel file headers.")
        st.stop()
        
    title_counts = df_current.groupby("Training Title", dropna=False).size().reset_index(name="Count").sort_values("Count", ascending=False)
    title_counts["ColorGroup"] = label # Assign color based on current status

    card_open()
    fig2 = bar_with_labels(title_counts, "Training Title", "Count", "Count", color_col="ColorGroup", hover_x_name="Training Title", hover_y_name=f"{label} Count")
    fig2.update_layout(xaxis_tickangle=-45)

    event2 = st.plotly_chart(fig2, key=f"titles_{st.session_state.selected_status}", width="stretch", height=520, on_select="rerun", selection_mode=("points",))
    card_close()

    clicked = get_selected_x(event2)
    if clicked is not None: go("departments", title=clicked)

# ---------- DEPARTMENTS ----------
elif st.session_state.screen == "departments":
    label = get_status_label()
    title = st.session_state.selected_title
    crumb(f'Home → {label} → <b>{title}</b> → Departments')

    c1, c2 = st.columns([0.15, 0.85])
    with c1:
        if st.button("← Back"): go("titles")
    with c2:
        st.markdown(f"### Department vs {label} Count")

    df_current = get_current_df()
    
    # 🚨 FIX: Safety check
    if "Department" not in df_current.columns:
        st.error("⚠️ Column 'Department' is missing from this sheet. Please check your Excel file headers.")
        st.stop()
        
    df_filtered = df_current[df_current["Training Title"].astype(str) == str(title)]
    dept_counts = df_filtered.groupby("Department", dropna=False).size().reset_index(name="Count").sort_values("Count", ascending=False)
    dept_counts["ColorGroup"] = label

    card_open()
    fig3 = bar_with_labels(dept_counts, "Department", "Count", "Count", color_col="ColorGroup", hover_x_name="Department", hover_y_name=f"{label} Count")
    event3 = st.plotly_chart(fig3, key=f"dept_{st.session_state.selected_status}", width="stretch", height=520, on_select="rerun", selection_mode=("points",))
    card_close()

    clicked = get_selected_x(event3)
    if clicked is not None: go("employees", dept=clicked)

# ---------- EMPLOYEES ----------
elif st.session_state.screen == "employees":
    label = get_status_label()
    title = st.session_state.selected_title
    dept = st.session_state.selected_department
    crumb(f'Home → {label} → {title} → <b>{dept}</b> → Employees')

    c1, c2 = st.columns([0.15, 0.85])
    with c1:
        if st.button("← Back"): go("departments")
    with c2:
        st.markdown(f"### Employee Information ({label})")

    df_current = get_current_df()
    df_emp = df_current[
        (df_current["Training Title"].astype(str) == str(title)) &
        (df_current["Department"].astype(str) == str(dept))
    ].copy()

    show_cols = ["Staff ID", "Employee Name", "Desg Name", "Department", "Training Type", "Training Title", "Status"]
    existing_cols = [c for c in show_cols if c in df_emp.columns]

    card_open()
    st.dataframe(df_emp[existing_cols], use_container_width=True, hide_index=True)
    card_close()
