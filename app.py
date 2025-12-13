import streamlit as st
import pandas as pd
import numpy as np
import html

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

    --good: rgba(16,185,129,0.14);
    --warn: rgba(245,158,11,0.16);
    --diff: rgba(30,58,138,0.10);
    --diff2: rgba(30,58,138,0.16);
    --empty: rgba(15,23,42,0.03);
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
h1, h2, h3, h4 { letter-spacing: -0.02em; }
h1 { color: var(--primary); font-weight: 800; margin-bottom: 0.15rem; }
.small-subtitle{ color: var(--muted); margin-top: -0.15rem; }

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
section[data-testid="stSidebar"] p{ color: var(--text); }

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

/* Expander polish */
div[data-testid="stExpander"]{
    border-radius: 12px;
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,0.70);
}

/* ---------------------------------------
   "Website-like" Compare Table (HTML)
---------------------------------------- */
.spec-wrap{
    border: 1px solid var(--stroke);
    border-radius: 14px;
    overflow: hidden;
    background: var(--cardSolid);
    box-shadow: 0 10px 22px rgba(2,6,23,0.05);
}
.spec-scroll{
    overflow: auto;
    max-height: 560px;
}
.spec-table{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 14px;
}
.spec-table thead th{
    position: sticky;
    top: 0;
    z-index: 3;
    background: linear-gradient(180deg, rgba(30,58,138,0.10) 0%, rgba(255,255,255,0.98) 100%);
    color: var(--text);
    text-align: left;
    padding: 12px 12px;
    border-bottom: 1px solid var(--stroke);
    white-space: nowrap;
}
.spec-table thead th:first-child{
    left: 0;
    z-index: 4;
    position: sticky;
    background: linear-gradient(180deg, rgba(30,58,138,0.14) 0%, rgba(255,255,255,0.98) 100%);
}
.spec-table tbody td{
    padding: 11px 12px;
    border-bottom: 1px solid rgba(15,23,42,0.06);
    vertical-align: top;
}
.spec-table tbody tr:nth-child(even) td{
    background: rgba(15,23,42,0.02);
}
.spec-table tbody td:first-child{
    position: sticky;
    left: 0;
    z-index: 2;
    background: rgba(255,255,255,0.98);
    border-right: 1px solid rgba(15,23,42,0.06);
    min-width: 260px;
    max-width: 360px;
}
.spec-chip{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid rgba(15,23,42,0.10);
    background: rgba(255,255,255,0.85);
    color: #334155;
    font-weight: 650;
    font-size: 12px;
    white-space: nowrap;
}
.cell{
    line-height: 1.35;
    color: #0f172a;
    word-break: break-word;
}
.cell.empty{
    color: #94a3b8;
    background: var(--empty);
    border-radius: 10px;
    padding: 7px 9px;
}
.cell.diff{
    background: var(--diff);
    border: 1px solid rgba(30,58,138,0.12);
    border-radius: 10px;
    padding: 7px 9px;
}
.cell.diff.strong{
    background: var(--diff2);
}
.note-muted{
    color: var(--muted);
    font-size: 13px;
}

/* ---------------------------------------
   Supplier cards (Catalog view)
---------------------------------------- */
.supplier-grid{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}
@media (max-width: 900px){
    .supplier-grid{ grid-template-columns: 1fr; }
}
.supplier-card{
    border: 1px solid var(--stroke);
    border-radius: 14px;
    background: rgba(255,255,255,0.88);
    box-shadow: 0 10px 22px rgba(2,6,23,0.05);
    padding: 14px 14px 10px 14px;
    transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
}
.supplier-card:hover{
    transform: translateY(-2px);
    box-shadow: 0 16px 32px rgba(2,6,23,0.08);
    border-color: rgba(30,58,138,0.18);
}
.supplier-title{
    font-weight: 850;
    color: var(--text);
    font-size: 16px;
    margin-bottom: 4px;
}
.badges{
    display:flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 10px;
}
.badge{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    border: 1px solid rgba(15,23,42,0.10);
    color: #334155;
    background: rgba(255,255,255,0.75);
}
.badge.good{ background: var(--good); border-color: rgba(16,185,129,0.22); }
.badge.warn{ background: var(--warn); border-color: rgba(245,158,11,0.22); }
.kv-table{
    width:100%;
    border-collapse: separate;
    border-spacing: 0;
}
.kv-table td{
    padding: 8px 8px;
    border-bottom: 1px solid rgba(15,23,42,0.06);
    vertical-align: top;
}
.kv-table td:first-child{
    width: 44%;
    color: #334155;
    font-weight: 650;
}
.kv-table tr:nth-child(even) td{
    background: rgba(15,23,42,0.02);
}
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

    clean_cols = []
    for c in df.columns:
        c_str = str(c).strip()
        c_str = c_str.replace("\\", "")
        c_str = c_str.replace('"', "").strip()

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
    grouped = df.groupby([group_col, pivot_col])[features].agg(
        lambda x: ", ".join(sorted(set([str(v) for v in x if v != ""])))
    ).reset_index()
    return grouped



def _esc(x) -> str:
    return html.escape("" if x is None else str(x))


def _shorten(s: str, limit: int = 120) -> str:
    s = "" if s is None else str(s)
    s = s.strip()
    if len(s) <= limit:
        return s
    return s[: max(0, limit - 1)] + "…"


def build_compare_html(
    data_by_supplier: dict,
    suppliers: list[str],
    features: list[str],
    *,
    show_only_differences: bool,
    hide_empty_rows: bool,
    strong_diff_threshold: int = 2
) -> tuple[str, pd.DataFrame]:
    """
    Returns HTML for a sticky "spec compare" table + the underlying compare dataframe.
    """
    # Create compare df for export as well
    compare_df = pd.DataFrame({"Feature": features})
    for sup in suppliers:
        compare_df[sup] = [data_by_supplier.get(sup, {}).get(f, "") for f in features]

    # Decide diff rows
    diff_flags = []
    for f in features:
        row_vals = []
        for sup in suppliers:
            v = str(data_by_supplier.get(sup, {}).get(f, "")).strip()
            if v != "":
                row_vals.append(v)
        distinct = len(set(row_vals))
        is_diff = distinct >= 2
        diff_flags.append((is_diff, distinct))

    # Build HTML
    thead = "<thead><tr>"
    thead += "<th><span class='spec-chip'>Feature</span></th>"
    for sup in suppliers:
        thead += f"<th><span class='spec-chip'>{_esc(sup)}</span></th>"
    thead += "</tr></thead>"

    rows_html = []
    for i, f in enumerate(features):
        is_diff, distinct = diff_flags[i]

        if show_only_differences and not is_diff:
            continue

        # Hide row if all empty
        if hide_empty_rows:
            all_empty = True
            for sup in suppliers:
                if str(data_by_supplier.get(sup, {}).get(f, "")).strip() != "":
                    all_empty = False
                    break
            if all_empty:
                continue

        tr = "<tr>"
        tr += f"<td><div class='cell'><strong>{_esc(f)}</strong></div></td>"

        for sup in suppliers:
            raw = str(data_by_supplier.get(sup, {}).get(f, "")).strip()
            if raw == "":
                tr += "<td><div class='cell empty'>—</div></td>"
            else:
                cls = "cell"
                if is_diff:
                    cls += " diff"
                    if distinct >= strong_diff_threshold:
                        cls += " strong"
                shown = _shorten(raw, 150)
                tr += f"<td><div class='{cls}' title='{_esc(raw)}'>{_esc(shown)}</div></td>"
        tr += "</tr>"
        rows_html.append(tr)

    tbody = "<tbody>" + "".join(rows_html) + "</tbody>"

    html_table = f"""
    <div class="spec-wrap">
      <div class="spec-scroll">
        <table class="spec-table">
          {thead}
          {tbody}
        </table>
      </div>
    </div>
    """
    return html_table, compare_df




def build_catalog_html(
    data_by_supplier: dict,
    suppliers: list[str],
    features: list[str],
    *,
    hide_empty_columns: bool,
    show_only_diff_columns: bool,
    strong_diff_threshold: int = 2
) -> tuple[str, pd.DataFrame]:
    """Supplier Catalog as a wide, website-like table.
    Rows = suppliers, Columns = features (same structure as input headers).
    """
    # Base df for downloads
    catalog_df = pd.DataFrame({"Supplier": suppliers})
    for f in features:
        catalog_df[f] = [data_by_supplier.get(s, {}).get(f, "") for s in suppliers]

    # Column stats for filtering + styling
    col_flags = {}
    for f in features:
        vals = []
        any_non_empty = False
        for s in suppliers:
            v = str(data_by_supplier.get(s, {}).get(f, "")).strip()
            if v != "":
                any_non_empty = True
                vals.append(v)
        distinct = len(set(vals))
        is_diff = distinct >= 2
        col_flags[f] = {"any": any_non_empty, "diff": is_diff, "distinct": distinct}

    visible_features = list(features)
    if hide_empty_columns:
        visible_features = [f for f in visible_features if col_flags.get(f, {}).get("any", False)]
    if show_only_diff_columns:
        visible_features = [f for f in visible_features if col_flags.get(f, {}).get("diff", False)]

    # HTML header
    thead = "<thead><tr>"
    thead += "<th><span class='spec-chip'>Supplier</span></th>"
    for f in visible_features:
        thead += f"<th><span class='spec-chip'>{_esc(f)}</span></th>"
    thead += "</tr></thead>"

    # HTML body
    rows_html = []
    for s in suppliers:
        tr = "<tr>"
        tr += f"<td><div class='cell'><strong>{_esc(s)}</strong></div></td>"
        for f in visible_features:
            raw = str(data_by_supplier.get(s, {}).get(f, "")).strip()
            if raw == "":
                tr += "<td><div class='cell empty'>—</div></td>"
            else:
                cls = "cell"
                if col_flags.get(f, {}).get("diff", False):
                    cls += " diff"
                    if col_flags.get(f, {}).get("distinct", 0) >= strong_diff_threshold:
                        cls += " strong"
                shown = _shorten(raw, 120)
                tr += f"<td><div class='{cls}' title='{_esc(raw)}'>{_esc(shown)}</div></td>"
        tr += "</tr>"
        rows_html.append(tr)

    tbody = "<tbody>" + "".join(rows_html) + "</tbody>"

    html_table = f"""
    <div class=\"spec-wrap\">
      <div class=\"spec-scroll\">
        <table class=\"spec-table\">
          {thead}
          {tbody}
        </table>
      </div>
    </div>
    """

    # Return df with only visible features for the view (downloads can use this or full)
    view_df = catalog_df[["Supplier"] + visible_features] if visible_features else catalog_df[["Supplier"]]
    return html_table, view_df
def build_supplier_cards_html(
    suppliers_ordered: list[str],
    supplier_summary: dict,
    supplier_feature_map: dict,
    features: list[str],
    *,
    compact: bool = False
) -> str:
    """
    Returns HTML grid of supplier cards. Details are rendered inside Streamlit expanders (below each card).
    Here we only render the visible top area (title + badges).
    """
    cards = []
    for sup in suppliers_ordered:
        meta = supplier_summary.get(sup, {})
        coverage_pct = meta.get("coverage_pct", 0)
        filled = meta.get("filled", 0)
        total = meta.get("total", len(features))
        recs = meta.get("records", 0)

        # Badge severity
        if coverage_pct >= 75:
            cov_class = "good"
        elif coverage_pct >= 40:
            cov_class = ""
        else:
            cov_class = "warn"

        cards.append(f"""
        <div class="supplier-card">
            <div class="supplier-title">{_esc(sup)}</div>
            <div class="badges">
                <div class="badge {cov_class}">Coverage: <strong>{coverage_pct:.0f}%</strong></div>
                <div class="badge">Filled: <strong>{filled}</strong> / {total}</div>
                <div class="badge">Records: <strong>{recs}</strong></div>
            </div>
            <div class="note-muted">{_esc("Click the expander below to view feature details.")}</div>
        </div>
        """)

    grid = '<div class="supplier-grid">' + "".join(cards) + "</div>"
    return grid


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

        # Use ALL remaining columns as features (Compare + Catalog).
        c_features = list(remaining_cols)

        with st.expander("Feature columns (using ALL by default)", expanded=False):
            st.caption("These columns become your feature headers. You can optionally exclude a few.")
            exclude_cols = st.multiselect("Exclude columns", remaining_cols, default=[])
            if exclude_cols:
                c_features = [c for c in remaining_cols if c not in exclude_cols]
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
                • Grouping: <em>{_esc(c_die)}</em><br>
                • Supplier: <em>{_esc(c_supplier)}</em>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with preview_col:
        st.markdown("<div class='card hover-lift'>", unsafe_allow_html=True)
        st.caption("First few rows (sanity check)")
        st.dataframe(df.head(preview_rows), use_container_width=True, height=240)
        st.markdown("</div>", unsafe_allow_html=True)

if not c_features:
    st.error("Please select at least one feature from the sidebar.")
    st.stop()

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

# =========================================================
# Build website-like maps for Compare + Catalog
# =========================================================
suppliers_all = sorted([s for s in agg_df[c_supplier].astype(str).unique().tolist() if str(s).strip() != ""])
if not suppliers_all:
    st.warning("No suppliers found (empty supplier column for this selection).")
    st.stop()

# Per-supplier feature values (already aggregated)
supplier_feature_map = {}
for _, row in agg_df.iterrows():
    sup = str(row[c_supplier]).strip()
    if sup == "":
        continue
    supplier_feature_map.setdefault(sup, {})
    for f in c_features:
        supplier_feature_map[sup][f] = str(row.get(f, "")).strip()

# Supplier record counts (raw subset)
supplier_records = subset.groupby(c_supplier).size().to_dict()

# Coverage summary per supplier
supplier_summary = {}
for sup in suppliers_all:
    filled = 0
    for f in c_features:
        if str(supplier_feature_map.get(sup, {}).get(f, "")).strip() != "":
            filled += 1
    total = len(c_features)
    coverage_pct = (filled / total * 100.0) if total else 0.0
    supplier_summary[sup] = {
        "filled": filled,
        "total": total,
        "coverage_pct": coverage_pct,
        "records": int(supplier_records.get(sup, 0)),
    }

# ==========================================
# 5) TABS: Website-like Compare + Catalog
# ==========================================
tab_matrix, tab_catalog = st.tabs(["📊 Compare View", "📋 Catalog View"])

with tab_matrix:
    st.markdown("<div class='card hover-lift'>", unsafe_allow_html=True)
    st.markdown("#### ⚔️ Supplier Comparison Builder")
    st.caption("Pick suppliers. The table uses **all features** (you can search features if needed).")

    # Controls
    ctl1, ctl2, ctl3 = st.columns([1.6, 1.4, 1], gap="large")

    # Default suppliers: top by records (or a selection pushed from Catalog view)
    top_by_records = sorted(suppliers_all, key=lambda s: supplier_summary.get(s, {}).get("records", 0), reverse=True)
    default_compare = top_by_records[:4] if len(top_by_records) >= 2 else top_by_records
    if "compare_suppliers" in st.session_state and isinstance(st.session_state["compare_suppliers"], list):
        pushed = [s for s in st.session_state["compare_suppliers"] if s in suppliers_all]
        if len(pushed) >= 2:
            default_compare = pushed

    with ctl1:
        compare_suppliers = st.multiselect(
            "Suppliers to compare",
            suppliers_all,
            default=default_compare,
        )
    with ctl2:
        feature_q = st.text_input(
            "Search features (optional)",
            value="",
            placeholder="Type part of a feature name…"
        )
    with ctl3:
        show_only_diff = st.toggle("Only differences", value=False)
        hide_empty_rows = st.toggle("Hide empty rows", value=True)

    compare_features = list(c_features)
    if feature_q.strip():
        ql = feature_q.strip().lower()
        compare_features = [f for f in c_features if ql in str(f).lower()]
    if len(compare_suppliers) < 2:
        st.info("Select at least **2 suppliers** to compare.")
        st.markdown("</div>", unsafe_allow_html=True)
    elif len(compare_features) == 0:
        st.info("No features match your search filter.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Build compare HTML
        html_table, compare_df = build_compare_html(
            supplier_feature_map,
            compare_suppliers,
            compare_features,
            show_only_differences=show_only_diff,
            hide_empty_rows=hide_empty_rows,
            strong_diff_threshold=2
        )

        st.markdown(
            "<div class='note-muted'>Tip: hover cells to see full value (tooltip). Sticky header + first column stay visible.</div>",
            unsafe_allow_html=True
        )
        st.markdown(html_table, unsafe_allow_html=True)

        # Download compare data
        csv_bytes = compare_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download comparison (CSV)",
            data=csv_bytes,
            file_name=f"compare_{selected_group}.csv".replace(" ", "_"),
            mime="text/csv",
            use_container_width=False
        )

        st.markdown("</div>", unsafe_allow_html=True)

with tab_catalog:
    st.markdown("<div class='card hover-lift'>", unsafe_allow_html=True)
    st.markdown("#### 🧾 Supplier Catalog (Table)")
    st.caption("Website-like catalog table: **rows = suppliers**, **columns = features** (same structure as your input headers).")

    # Catalog controls
    c1, c2, c3 = st.columns([1.6, 1.2, 1.2], gap="large")
    with c1:
        q = st.text_input("Search supplier", value="", placeholder="Type a supplier name…")
    with c2:
        sort_by = st.selectbox(
            "Sort suppliers",
            ["Coverage (desc)", "Records (desc)", "Name (A→Z)", "Name (Z→A)"],
            index=0
        )
    with c3:
        filter_feature = st.selectbox(
            "Supplier must have value for",
            ["(no filter)"] + list(c_features),
            index=0
        )

    c4, c5, c6 = st.columns([1.6, 1, 1], gap="large")
    with c4:
        feature_q = st.text_input("Search columns (optional)", value="", placeholder="Type part of a feature/column name…")
    with c5:
        show_only_diff_cols = st.toggle("Only different columns", value=False)
    with c6:
        hide_empty_cols = st.toggle("Hide all-empty columns", value=False)

    # Filter suppliers (search + optional feature filter)
    filtered = suppliers_all
    if q.strip():
        ql = q.strip().lower()
        filtered = [s for s in filtered if ql in s.lower()]

    if filter_feature != "(no filter)":
        f = filter_feature
        filtered = [
            s for s in filtered
            if str(supplier_feature_map.get(s, {}).get(f, "")).strip() != ""
        ]

    # Sort suppliers
    if sort_by == "Coverage (desc)":
        filtered = sorted(filtered, key=lambda s: supplier_summary.get(s, {}).get("coverage_pct", 0), reverse=True)
    elif sort_by == "Records (desc)":
        filtered = sorted(filtered, key=lambda s: supplier_summary.get(s, {}).get("records", 0), reverse=True)
    elif sort_by == "Name (A→Z)":
        filtered = sorted(filtered, key=lambda s: s.lower())
    else:
        filtered = sorted(filtered, key=lambda s: s.lower(), reverse=True)

    # Filter visible columns (optional search)
    visible_features = list(c_features)
    if feature_q.strip():
        qf = feature_q.strip().lower()
        visible_features = [f for f in visible_features if qf in str(f).lower()]

    # Quick compare selector (pushes selection into Compare tab defaults)
    with st.expander("Quick compare (send suppliers to Compare View)", expanded=False):
        default_pick = filtered[:4] if len(filtered) >= 4 else filtered
        pick = st.multiselect("Pick 2+ suppliers", filtered, default=default_pick)
        if st.button("Use these suppliers in Compare View"):
            if len(pick) >= 2:
                st.session_state["compare_suppliers"] = pick
                st.success("Applied. Open the **Compare View** tab to see them.")
            else:
                st.info("Pick at least 2 suppliers.")

    if not filtered:
        st.info("No suppliers match your filters.")
        st.markdown("</div>", unsafe_allow_html=True)
    elif len(visible_features) == 0:
        st.info("No columns match your column search filter.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Build website-like catalog table
        html_table, catalog_view_df = build_catalog_html(
            supplier_feature_map,
            filtered,
            visible_features,
            hide_empty_columns=hide_empty_cols,
            show_only_diff_columns=show_only_diff_cols,
            strong_diff_threshold=2
        )

        st.markdown(
            "<div class='note-muted'>Tip: use horizontal scroll for many columns. Hover any cell to see the full value.</div>",
            unsafe_allow_html=True
        )
        st.markdown(html_table, unsafe_allow_html=True)

        # Download (current view)
        csv_bytes = catalog_view_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download catalog (CSV — current view)",
            data=csv_bytes,
            file_name=f"catalog_{selected_group}.csv".replace(" ", "_"),
            mime="text/csv",
        )

        st.markdown("</div>", unsafe_allow_html=True)
