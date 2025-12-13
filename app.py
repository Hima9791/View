import streamlit as st
import pandas as pd
import numpy as np

# Altair is commonly available via Streamlit installs; if not, we gracefully fall back.
try:
    import altair as alt
    HAS_ALTAIR = True
except Exception:
    alt = None
    HAS_ALTAIR = False


# ==========================================
# 1) CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Component Analytics Pro",
    layout="wide",
    page_icon="💠",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
<style>
/* -----------------------------
   Design tokens (subtle, corporate)
------------------------------ */
:root{
    --bg0: #f8fafc;
    --bg1: #eef2ff;
    --card: rgba(255,255,255,0.92);
    --cardSolid: #ffffff;
    --stroke: rgba(15, 23, 42, 0.10);
    --stroke2: rgba(15, 23, 42, 0.08);
    --text: #0f172a;
    --muted: #64748b;
    --primary: #1e3a8a;
    --primary2: #2746a6;
    --shadow: 0 10px 22px rgba(2, 6, 23, 0.06);
    --shadow2: 0 14px 30px rgba(2, 6, 23, 0.08);
    --radius: 14px;
}

/* App background: subtle gradient */
.stApp {
    background: radial-gradient(1200px 600px at 20% 0%, var(--bg1) 0%, var(--bg0) 45%, var(--bg0) 100%);
    color: var(--text);
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 15px;
}

/* Wider layout */
.block-container{
    max-width: 1400px;
    padding: 1.25rem 2.25rem 4rem 2.25rem;
}

/* Headings */
h1, h2, h3, h4 {
    letter-spacing: -0.02em;
}
h1 {
    color: var(--primary);
    font-weight: 800;
    margin-bottom: 0.15rem;
}
.small-subtitle{
    color: var(--muted);
    margin-top: -0.15rem;
}

/* Reusable card */
.card {
    background: var(--card);
    border: 1px solid var(--stroke);
    border-radius: var(--radius);
    padding: 18px;
    box-shadow: var(--shadow);
    backdrop-filter: blur(6px);
}
.card.hover-lift{
    transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
}
.card.hover-lift:hover{
    transform: translateY(-2px);
    box-shadow: var(--shadow2);
    border-color: rgba(30, 58, 138, 0.18);
}

/* Sidebar polish */
section[data-testid="stSidebar"]{
    background: linear-gradient(180deg, rgba(255,255,255,0.65) 0%, rgba(255,255,255,0.40) 100%);
    border-right: 1px solid var(--stroke2);
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p{
    color: var(--text);
}

/* Metric cards (hover + tighter) */
[data-testid="stMetric"]{
    background: var(--cardSolid);
    border: 1px solid var(--stroke);
    border-radius: 12px;
    padding: 14px 14px 12px 14px;
    box-shadow: 0 6px 16px rgba(2, 6, 23, 0.05);
    transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
}
[data-testid="stMetric"]:hover{
    transform: translateY(-2px);
    box-shadow: 0 14px 28px rgba(2, 6, 23, 0.08);
    border-color: rgba(30, 58, 138, 0.20);
}
[data-testid="stMetricLabel"] { color: var(--muted); font-size: 0.86rem; }
[data-testid="stMetricValue"] { color: var(--primary); font-weight: 800; }

/* Tabs: modern pill style */
.stTabs [data-baseweb="tab-list"]{
    gap: 10px;
    padding: 6px 6px 2px 6px;
    border-bottom: 1px solid var(--stroke2);
}
.stTabs [data-baseweb="tab"]{
    height: 42px;
    padding: 0 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.75);
    border: 1px solid var(--stroke);
    color: #334155;
    font-weight: 600;
    transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease, border-color 160ms ease;
}
.stTabs [data-baseweb="tab"]:hover{
    transform: translateY(-1px);
    box-shadow: 0 10px 18px rgba(2, 6, 23, 0.06);
    border-color: rgba(30, 58, 138, 0.18);
}
.stTabs [aria-selected="true"]{
    background: linear-gradient(180deg, var(--primary2) 0%, var(--primary) 100%);
    color: white !important;
    border: 1px solid rgba(255,255,255,0.20);
}

/* Dataframe container */
[data-testid="stDataFrame"]{
    border: 1px solid var(--stroke);
    border-radius: 12px;
    background: var(--cardSolid);
    box-shadow: 0 10px 22px rgba(2, 6, 23, 0.05);
    overflow: hidden;
}

/* Expander polish */
div[data-testid="stExpander"]{
    border-radius: 12px;
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,0.70);
}

/* Smaller spacing tweaks */
hr{ border-color: rgba(15,23,42,0.08) !important; }
div[data-testid="stCaptionContainer"] p { color: var(--muted); }
</style>
""",
    unsafe_allow_html=True
)


# ==========================================
# 2) DATA LOGIC
# ==========================================
@st.cache_data(show_spinner=False)
def load_data(file) -> pd.DataFrame:
    """Loads and cleans the messy Excel/CSV data."""
    if file.name.endswith(".csv"):
        df = pd.read_csv(file, on_bad_lines="skip")
    else:
        df = pd.read_excel(file)

    # Clean Column Headers
    clean_cols = []
    for c in df.columns:
        c_str = str(c).strip()
        c_str = c_str.replace("\\", "")
        c_str = c_str.replace('"', "").strip()

        # Fix known typos
        if "Supplier tire" in c_str:
            c_str = "Tier 1"
        if "Teir" in c_str:
            c_str = "Tier 1"

        clean_cols.append(c_str)

    df.columns = clean_cols
    df = df.fillna("")
    return df


@st.cache_data(show_spinner=False)
def aggregate_data(df: pd.DataFrame, group_col: str, pivot_col: str, features: list[str]) -> pd.DataFrame:
    """
    Aggregates data. If multiple values exist for the same cell, joins them.
    """
    grouped = df.groupby([group_col, pivot_col])[features].agg(
        lambda x: ", ".join(sorted(set([str(v) for v in x if v != ""])))
    ).reset_index()
    return grouped


def compute_feature_coverage(agg_df: pd.DataFrame, supplier_col: str, features: list[str]) -> pd.DataFrame:
    """
    For each feature: count unique non-empty values across suppliers (post-aggregation),
    and also count how many suppliers actually have a value for that feature.
    """
    num_suppliers = int(agg_df[supplier_col].nunique()) if supplier_col in agg_df.columns else 0
    rows = []
    for f in features:
        s = agg_df[f].astype(str).str.strip()
        non_empty_mask = s.ne("")
        rows.append({
            "Feature": f,
            "UniqueValues": int(s[non_empty_mask].nunique()),
            "SuppliersWithValue": int(non_empty_mask.sum()),
            "SuppliersTotal": num_suppliers,
        })
    out = pd.DataFrame(rows).sort_values(["UniqueValues", "SuppliersWithValue"], ascending=False)
    return out


def zebra_styler(df: pd.DataFrame) -> "pd.io.formats.style.Styler":
    """
    Zebra stripes + hover, for a clean 'report-like' look.
    Note: Styled tables may render less interactively than the default grid for very large data.
    """
    styles = [
        {"selector": "thead th", "props": [("background-color", "rgba(30,58,138,0.06)"),
                                          ("color", "#0f172a"),
                                          ("font-weight", "700"),
                                          ("border-bottom", "1px solid rgba(15,23,42,0.10)")]},
        {"selector": "tbody tr:nth-child(even)", "props": [("background-color", "rgba(15,23,42,0.03)")]},
        {"selector": "tbody tr:hover", "props": [("background-color", "rgba(30,58,138,0.07)")]},
        {"selector": "td", "props": [("border-bottom", "1px solid rgba(15,23,42,0.06)"),
                                     ("vertical-align", "top")]},
        {"selector": "table", "props": [("border-collapse", "separate"), ("border-spacing", "0")]},
    ]
    return df.style.set_table_styles(styles)


def render_dataframe(df: pd.DataFrame, height: int = 420, *, hide_index: bool = False) -> None:
    """
    Uses zebra styling for reasonable table sizes; falls back to the default fast grid for huge tables.
    """
    if df is None:
        return

    # Heuristic: styling for medium-ish tables only (keeps app fast)
    cells = int(df.shape[0]) * int(max(1, df.shape[1]))
    use_style = (df.shape[0] <= 2000) and (df.shape[1] <= 60) and (cells <= 80_000)

    if use_style:
        styled = zebra_styler(df)
        if hide_index:
            try:
                styled = styled.hide(axis="index")
            except Exception:
                pass
        st.dataframe(styled, use_container_width=True, height=height)
    else:
        st.dataframe(df, use_container_width=True, height=height, hide_index=hide_index)


# ==========================================
# 3) SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<div class='card hover-lift'>", unsafe_allow_html=True)
    st.header("📂 Data Import")
    uploaded_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv", "xls"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    if uploaded_file:
        with st.spinner("Loading dataset…"):
            df = load_data(uploaded_file)

        cols = list(df.columns)

        st.markdown("<div class='card hover-lift'>", unsafe_allow_html=True)
        st.header("⚙️ Configuration")

        # Smart Auto-Selection of Columns
        idx_die = 0
        idx_sup = 0
        for i, col in enumerate(cols):
            if "Die Family" in col:
                idx_die = i
            if "Latest" in col or "Company" in col:
                idx_sup = i

        c_die = st.selectbox("Grouping Column (e.g. Die Family)", cols, index=idx_die)
        c_supplier = st.selectbox("Supplier Column", cols, index=idx_sup)

        remaining_cols = [c for c in cols if c not in [c_die, c_supplier]]

        st.caption("Select features to analyze:")
        c_features = st.multiselect(
            "Features",
            remaining_cols,
            default=remaining_cols[:6] if len(remaining_cols) > 0 else None
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Awaiting file upload…")


# ==========================================
# 4) MAIN UI
# ==========================================
st.title("💠 Component Analytics")
st.markdown("<div class='small-subtitle'>High-trust supplier coverage, feature comparisons, and catalog views.</div>", unsafe_allow_html=True)

if not uploaded_file:
    st.markdown(
        """
        <div class='card hover-lift' style='text-align:center; margin-top: 1rem;'>
            <h3 style='margin:0; color:#0f172a;'>👋 Welcome</h3>
            <p style='color:#64748b; margin: 0.35rem 0 0.25rem 0;'>
                Upload your component dataset to configure suppliers, families, and feature comparisons.
            </p>
            <p style='color:#94a3b8; font-size: 14px; margin: 0;'>
                Works with CSV or Excel files. Bad rows are skipped automatically.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()

# ---- Dataset overview (now in expander) ----
base_rows, base_cols = df.shape
preview_rows = min(5, base_rows)

with st.expander("Dataset overview", expanded=False):
    info_col, preview_col = st.columns([1, 2], gap="large")

    with info_col:
        st.markdown("<div class='card hover-lift'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style='font-weight:800; color:#0f172a; margin-bottom: 6px;'>Source Summary</div>
            <div style='color:#475569; line-height: 1.65;'>
                • <strong>{base_rows}</strong> rows loaded<br>
                • <strong>{base_cols}</strong> columns detected<br>
                • Grouping: <em>{c_die}</em><br>
                • Supplier: <em>{c_supplier}</em>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with preview_col:
        st.markdown("<div class='card hover-lift'>", unsafe_allow_html=True)
        st.caption("First few rows (sanity check)")
        render_dataframe(df.head(preview_rows), height=240, hide_index=False)
        st.markdown("</div>", unsafe_allow_html=True)

if not c_features:
    st.error("Please select at least one feature from the sidebar.")
    st.stop()

# ---- Filter context ----
unique_groups = sorted(list(set(df[c_die].astype(str))))
if not unique_groups:
    st.error("No data found in the selected grouping column.")
    st.stop()

st.divider()

top_row = st.columns([1.6, 1], gap="large")
with top_row[0]:
    selected_group = st.selectbox("Select Component Family to Analyze:", unique_groups)
with top_row[1]:
    st.markdown(
        "<div class='card' style='padding: 12px 14px;'>"
        "<div style='font-weight:800; color:#0f172a; margin-bottom: 2px;'>Analysis scope</div>"
        "<div style='color:#64748b;'>Changes update KPIs, chart, and views.</div>"
        "</div>",
        unsafe_allow_html=True
    )

subset = df[df[c_die].astype(str) == selected_group]

# ---- KPIs ----
st.markdown("<div class='card hover-lift' style='margin-top: 0.25rem;'>", unsafe_allow_html=True)

kpi_header = st.columns([1, 1])
with kpi_header[0]:
    st.markdown("#### Key highlights")
with kpi_header[1]:
    st.caption("Metrics update as you switch component families.")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

num_suppliers = int(subset[c_supplier].nunique())
num_features = int(len(c_features))
total_records = int(len(subset))

if not subset.empty and subset[c_supplier].astype(str).ne("").any():
    try:
        top_supplier = subset[c_supplier].mode()[0]
    except Exception:
        top_supplier = "N/A"
else:
    top_supplier = "N/A"

kpi1.metric("Active Suppliers", num_suppliers)
kpi2.metric("Features Tracked", num_features)
kpi3.metric("Total Records", total_records)
kpi4.metric("Top Supplier", top_supplier)

st.markdown("</div>", unsafe_allow_html=True)

# ---- Data processing ----
with st.spinner("Building comparison views…"):
    agg_df = aggregate_data(subset, c_die, c_supplier, c_features)

if agg_df.empty:
    st.warning("No data available for this selection.")
    st.stop()

# Views
view_catalog = agg_df.set_index(c_supplier)[c_features]
view_matrix = view_catalog.transpose()

# ---- Altair coverage chart (after KPIs) ----
coverage_df = compute_feature_coverage(agg_df, c_supplier, c_features)

st.markdown("<div class='card hover-lift' style='margin-top: 1rem;'>", unsafe_allow_html=True)
st.markdown("#### Supplier feature coverage")
st.caption("Bars show how many **unique non-empty values** exist per feature across suppliers (post-aggregation).")

if HAS_ALTAIR:
    hover = alt.selection_point(on="mouseover", fields=["Feature"], nearest=True, empty=False)

    chart = (
        alt.Chart(coverage_df)
        .mark_bar()
        .encode(
            x=alt.X("Feature:N", sort="-y", axis=alt.Axis(title=None, labelAngle=-25, labelLimit=220)),
            y=alt.Y("UniqueValues:Q", title="Unique non-empty values"),
            tooltip=[
                alt.Tooltip("Feature:N"),
                alt.Tooltip("UniqueValues:Q", title="Unique values"),
                alt.Tooltip("SuppliersWithValue:Q", title="Suppliers with value"),
                alt.Tooltip("SuppliersTotal:Q", title="Total suppliers"),
            ],
            opacity=alt.condition(hover, alt.value(1.0), alt.value(0.75)),
        )
        .add_params(hover)
        .properties(height=280)
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("Altair is not available in this environment. Showing a simple bar chart instead.")
    st.bar_chart(coverage_df.set_index("Feature")["UniqueValues"])

st.markdown("</div>", unsafe_allow_html=True)

# ---- Tabs ----
tab_matrix, tab_catalog = st.tabs(["📊 Compare View (Matrix)", "📋 Catalog View (List)"])

with tab_matrix:
    st.markdown("<div class='card hover-lift'>", unsafe_allow_html=True)
    st.markdown("#### ⚔️ Head-to-Head Comparison")
    st.caption(f"Comparing **{len(c_features)} features** across **{num_suppliers} suppliers**. (Suppliers are columns)")
    render_dataframe(view_matrix, height=460, hide_index=False)
    st.markdown("</div>", unsafe_allow_html=True)

with tab_catalog:
    st.markdown("<div class='card hover-lift'>", unsafe_allow_html=True)
    st.markdown("#### 📚 Supplier Catalog")
    st.caption("Detailed breakdown per supplier. (Suppliers are rows)")
    render_dataframe(view_catalog, height=460, hide_index=False)
    st.markdown("</div>", unsafe_allow_html=True)
