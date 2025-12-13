import base64
import json
import re
import pandas as pd
import streamlit as st
import numpy as np

# ==========================================
# 1. CONFIG & UTILS
# ==========================================
st.set_page_config(page_title="Component Explorer Pro", layout="wide", page_icon="🔬")

APP_TITLE = "Supplier × DieFamily Explorer"
MULTI_JOIN = ", "
EMPTY_TOKEN = "-"

# Styling for Streamlit Native
st.markdown("""
<style>
    .stDataFrame { border: 1px solid #f0f2f6; border-radius: 5px; }
    h1 { color: #2c3e50; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f8f9fa; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #e3f2fd; color: #1976d2; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# Candidates for auto-mapping
TIER1_CANDIDATES = ["Tier 1", "Tier1", "Supplier Tier 1", "Teir 1", "Teir1"]
LATEST_CANDIDATES = ["LatestCompanyName", "Latest Company Name", "LatestCompany", "CompanyName"]
DIEFAM_CANDIDATES = ["DieFamily", "Die Family", "Die Family key", "Die_Family_Key"]

# ==========================================
# 2. LOGIC FUNCTIONS
# ==========================================
def norm(s: str) -> str:
    return re.sub(r"[\s\-_]+", "", str(s).strip().lower())

def find_col(df, candidates):
    cmap = {norm(c): c for c in df.columns}
    for cand in candidates:
        if norm(cand) in cmap: return cmap[norm(cand)]
    return df.columns[0]

def split_cell_to_values(x):
    if pd.isna(x): return []
    s = str(x).strip()
    if not s: return []
    return [p.strip() for p in re.split(r"\s*\|\|\s*|\s*\|\s*", s) if p.strip()]

def concat_unique(series):
    vals = []
    for v in series: vals.extend(split_cell_to_values(v))
    return MULTI_JOIN.join(sorted(set(vals))) if vals else EMPTY_TOKEN

@st.cache_data(show_spinner=False)
def load_data(file):
    if file.name.endswith('csv'):
        return pd.read_csv(file)
    return pd.read_excel(file)

def get_pivoted_data(df, tier1, diefam, latest, features):
    """
    Creates two views of the data for a specific Die Family.
    """
    # Filter columns
    cols = [tier1, diefam, latest] + features
    sub_df = df[cols].copy()
    
    # Clean text to ensure grouping works
    sub_df[latest] = sub_df[latest].fillna("Unknown").astype(str).str.strip()
    
    # Aggregate duplicate rows (same supplier, same die family)
    # We group by Supplier and DieFamily, and aggregate features
    grouped = sub_df.groupby([tier1, diefam, latest], as_index=False)[features].agg(concat_unique)
    
    return grouped

# ==========================================
# 3. THE CUSTOM "CANVAS" UI (HTML/JS)
# ==========================================
# This HTML creates a sticky-header comparison table
CUSTOM_UI_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
    :root { --primary: #2980b9; --bg: #ffffff; --header-bg: #f8f9fa; --border: #ddd; }
    body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 10px; background: var(--bg); }
    
    /* SCROLL CONTAINER */
    .table-container { overflow-x: auto; max-height: 800px; border: 1px solid var(--border); border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    
    table { border-collapse: separate; border-spacing: 0; width: 100%; min-width: 800px; }
    
    /* HEADERS */
    th { background: var(--header-bg); color: #444; font-weight: 600; padding: 12px 15px; text-align: left; border-bottom: 2px solid var(--primary); position: sticky; top: 0; z-index: 10; }
    
    /* FIRST COLUMN STICKY (Features) */
    th:first-child, td:first-child { position: sticky; left: 0; background: var(--header-bg); z-index: 11; border-right: 2px solid #eee; font-weight: bold; min-width: 150px; }
    th:first-child { z-index: 20; } /* Top-left corner */

    td { padding: 10px 15px; border-bottom: 1px solid #eee; color: #555; vertical-align: top; font-size: 14px; min-width: 120px; }
    
    /* HOVER EFFECTS */
    tbody tr:hover td { background-color: #f1f8ff; }
    tbody tr:hover td:first-child { background-color: #e3f2fd; }
    
    .empty { color: #ccc; font-style: italic; }
    .val-pill { display: inline-block; background: #eef; padding: 2px 6px; border-radius: 4px; margin: 2px; border: 1px solid #dde; }
</style>
</head>
<body>
    <div id="root"></div>
    <script>
        const data = window.__APP_DATA__;
        
        function renderTable() {
            const root = document.getElementById('root');
            if (!data || !data.matrix) { root.innerHTML = "No data available"; return; }
            
            const suppliers = data.suppliers; // Array of strings
            const features = data.features;   // Object { featureName: { supplierName: value } }
            
            let html = '<div class="table-container"><table>';
            
            // HEADERS (Suppliers)
            html += '<thead><tr><th>Feature / Spec</th>';
            suppliers.forEach(s => {
                html += `<th>${s}</th>`;
            });
            html += '</tr></thead>';
            
            // BODY (Rows = Features)
            html += 'tbody';
            for (const [featName, supMap] of Object.entries(features)) {
                html += `<tr><td>${featName}</td>`;
                suppliers.forEach(s => {
                    let val = supMap[s] || "-";
                    let display = val === "-" ? '<span class="empty">-</span>' : val;
                    // Check if value contains commas (multiple values), wrap them
                    if (val.includes(',') && val !== "-") {
                        display = val.split(',').map(v => `<span class="val-pill">${v.trim()}</span>`).join('');
                    }
                    html += `<td>${display}</td>`;
                });
                html += '</tr>';
            }
            html += '</tbody></table></div>';
            root.innerHTML = html;
        }
        renderTable();
    </script>
</body>
</html>
"""

def render_custom_html(matrix_data, suppliers_list):
    """Injects data into the HTML string and renders it"""
    app_data = {"suppliers": suppliers_list, "features": matrix_data}
    json_str = json.dumps(app_data)
    b64 = base64.b64encode(json_str.encode("utf-8")).decode("ascii")
    
    html = CUSTOM_UI_TEMPLATE.replace(
        "window.__APP_DATA__;", 
        f"window.__APP_DATA__ = JSON.parse(atob('{b64}'));"
    )
    st.components.v1.html(html, height=600, scrolling=False)

# ==========================================
# 4. MAIN APP
# ==========================================

st.title(APP_TITLE)
st.caption("Compare electronic components: Switch between 'Matrix View' (Feature comparison) and 'List View' (Supplier catalogs).")

# --- 4.1 Input Section ---
with st.sidebar:
    st.header("1. Upload Data")
    uploaded = st.file_uploader("Upload CSV or Excel", type=["xlsx", "xls", "csv"])
    
    if uploaded:
        df = load_data(uploaded)
        
        st.divider()
        st.header("2. Map Columns")
        
        c_tier1 = st.selectbox("Tier 1 (Root)", df.columns, index=df.columns.get_loc(find_col(df, TIER1_CANDIDATES)))
        c_die   = st.selectbox("Die Family (Grouping)", df.columns, index=df.columns.get_loc(find_col(df, DIEFAM_CANDIDATES)))
        c_latest= st.selectbox("Supplier Name", df.columns, index=df.columns.get_loc(find_col(df, LATEST_CANDIDATES)))
        
        # ID columns to exclude from features
        id_cols = {c_tier1, c_die, c_latest}
        feature_candidates = [c for c in df.columns if c not in id_cols]
        
        c_features = st.multiselect("Select Features to Compare", feature_candidates, default=feature_candidates[:8])

if not uploaded:
    st.info("👋 Upload a file to begin.")
    st.stop()

if not c_features:
    st.warning("Please select at least one feature in the sidebar.")
    st.stop()

# --- 4.2 Data Processing ---

# 1. Get List of Unique Die Families to filter by
unique_families = df[c_die].dropna().unique().tolist()
unique_families.sort()

# Selector at the top
st.markdown("### 🔍 Select Component Group")
selected_family = st.selectbox("Select a Die Family to analyze:", unique_families)

# Filter Data
filtered_df = get_pivoted_data(df, c_tier1, c_die, c_latest, c_features)
filtered_df = filtered_df[filtered_df[c_die] == selected_family]

if filtered_df.empty:
    st.warning("No data found for this selection.")
    st.stop()

# --- 4.3 THE DUAL VIEWS ---

tab1, tab2, tab3 = st.tabs(["📊 Matrix View (Features x Supplier)", "📋 Catalog View (Supplier x Features)", "🎨 Canvas View (Custom UI)"])

# VIEW 1: MATRIX (Rows=Features, Cols=Suppliers)
with tab1:
    st.markdown("#### Feature Comparison Matrix")
    st.caption("Best for comparing specific specs across different suppliers.")
    
    # Pivot logic: Index=Feature, Columns=Supplier, Values=Value
    # We first melt
    melted = filtered_df.melt(id_vars=[c_latest], value_vars=c_features, var_name="Feature", value_name="Value")
    
    # Then pivot
    matrix_df = melted.pivot(index="Feature", columns=c_latest, values="Value")
    matrix_df = matrix_df.fillna("-")
    
    st.dataframe(matrix_df, use_container_width=True, height=500)

# VIEW 2: LIST (Rows=Suppliers, Cols=Features)
with tab2:
    st.markdown("#### Supplier Catalog List")
    st.caption("Best for viewing the full specification sheet for each supplier.")
    
    # This is essentially the filtered_df, just cleaned up
    display_df = filtered_df.set_index(c_latest)[c_features].fillna("-")
    
    st.dataframe(display_df, use_container_width=True)

# VIEW 3: CANVAS (The Custom HTML UI)
with tab3:
    st.markdown("#### Visual Comparison Board")
    
    # Prepare data for JS
    # 1. Get list of suppliers (columns)
    suppliers_list = sorted(filtered_df[c_latest].unique().tolist())
    
    # 2. Build feature map: { "Voltage": { "Nexperia": "45V", "OnSemi": "45V" } }
    feature_map = {}
    
    # Iterate through features
    for feat in c_features:
        feature_map[feat] = {}
        # Iterate through rows in the filtered DF
        for _, row in filtered_df.iterrows():
            sup = row[c_latest]
            val = row[feat]
            feature_map[feat][sup] = str(val) if pd.notna(val) else "-"

    render_custom_html(feature_map, suppliers_list)
