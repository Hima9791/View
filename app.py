import streamlit as st
import pandas as pd

# ==========================================
# 1. CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Component Analytics Pro",
    layout="wide",
    page_icon="💠",
    initial_sidebar_state="expanded"
)

# Custom CSS for a clean, professional look
st.markdown("""
<style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-size: 15px;
    }

    /* Constrain the main container so the UI doesn't feel zoomed-in */
    .block-container {
        max-width: 1200px;
        padding: 1.5rem 2rem 4rem 2rem;
    }
    
    /* Header Styling */
    h1 {
        color: #1e3a8a;
        font-weight: 700;
        letter-spacing: -1px;
        padding-bottom: 10px;
        border-bottom: 2px solid #e5e7eb;
        margin-bottom: 0.5rem;
    }
    
    h3 {
        color: #374151;
        font-weight: 600;
    }

    /* Metric Cards Styling */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 14px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    [data-testid="stMetricLabel"] { color: #6b7280; font-size: 0.9rem; }
    [data-testid="stMetricValue"] { color: #1e3a8a; font-weight: 700; }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 6px;
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        color: #4b5563;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e3a8a;
        color: white;
        border: none;
    }

    /* DataFrame Styling */
    [data-testid="stDataFrame"] {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        background-color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    /* Section container */
    .card-container {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOGIC
# ==========================================

@st.cache_data
def load_data(file):
    """Loads and cleans the messy Excel/CSV data."""
    if file.name.endswith('.csv'):
        # On Bad Lines: skip them to prevent errors
        df = pd.read_csv(file, on_bad_lines='skip')
    else:
        df = pd.read_excel(file)
    
    # Clean Column Headers
    clean_cols = []
    for c in df.columns:
        c_str = str(c).strip()
        
        # 1. Remove backslashes explicitly (avoid problematic regex patterns)
        c_str = c_str.replace('\\', '')

        # 2. Remove double quotes
        c_str = c_str.replace('"', '').strip()
        
        # 3. Fix known typos
        if "Supplier tire" in c_str: c_str = "Tier 1"
        if "Teir" in c_str: c_str = "Tier 1"
        
        clean_cols.append(c_str)
    
    df.columns = clean_cols
    
    # Fill NANs with empty string for cleaner display
    df = df.fillna("")
    return df

def aggregate_data(df, group_col, pivot_col, features):
    """
    Aggregates data. If multiple values exist for the same cell, joins them.
    """
    # Group by the main ID and the Supplier, then aggregate features
    grouped = df.groupby([group_col, pivot_col])[features].agg(
        lambda x: ", ".join(sorted(set([str(v) for v in x if v != ""])))
    ).reset_index()
    return grouped

# ==========================================
# 3. MAIN APPLICATION UI
# ==========================================

# --- Sidebar ---
with st.sidebar:
    st.header("📂 Data Import")
    uploaded_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv", "xls"])
    
    st.divider()
    
    if uploaded_file:
        df = load_data(uploaded_file)
        cols = list(df.columns)
        
        st.header("⚙️ Configuration")
        
        # Smart Auto-Selection of Columns
        idx_die = 0
        idx_sup = 0
        
        # Safe Loop to find indices
        for i, col in enumerate(cols):
            if "Die Family" in col: idx_die = i
            if "Latest" in col or "Company" in col: idx_sup = i

        c_die = st.selectbox("Grouping Column (e.g. Die Family)", cols, index=idx_die)
        c_supplier = st.selectbox("Supplier Column", cols, index=idx_sup)
        
        # Exclude ID columns from feature list
        remaining_cols = [c for c in cols if c not in [c_die, c_supplier]]
        
        st.caption("Select features to analyze:")
        c_features = st.multiselect(
            "Features", 
            remaining_cols, 
            default=remaining_cols[:6] if len(remaining_cols) > 0 else None
        )
    else:
        st.info("Awaiting file upload...")

# --- Main Area ---
st.title("💠 Component Analytics")

if not uploaded_file:
    st.markdown("""
    <div class='card-container' style='text-align: center'>
        <h3 style='margin:0'>👋 Welcome!</h3>
        <p style='color: #6b7280'>Upload your component dataset to configure suppliers, families, and feature comparisons.</p>
        <p style='color: #9ca3af; font-size: 14px;'>Works with CSV or Excel files. Bad rows are skipped automatically.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Quick glance at the raw file to help users verify columns
st.markdown("#### Dataset overview")
base_rows, base_cols = df.shape
preview_rows = min(5, base_rows)

info_col, preview_col = st.columns([1, 2])
with info_col:
    st.markdown(
        f"""
        <div class='card-container'>
            <div style='font-weight:600; color:#111827; margin-bottom: 4px;'>Source Summary</div>
            <div style='color:#4b5563;'>
                • <strong>{base_rows}</strong> rows loaded<br>
                • <strong>{base_cols}</strong> columns detected<br>
                • Grouping: <em>{c_die}</em><br>
                • Supplier: <em>{c_supplier}</em>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with preview_col:
    st.markdown("<div class='card-container' style='margin-bottom: 8px;'>", unsafe_allow_html=True)
    st.caption("First few rows (sanity check)")
    st.dataframe(df.head(preview_rows), use_container_width=True, height=220)
    st.markdown("</div>", unsafe_allow_html=True)

if not c_features:
    st.error("Please select at least one feature from the sidebar.")
    st.stop()

# --- Dashboard Logic ---

# 1. Filter Context
unique_groups = sorted(list(set(df[c_die].astype(str))))
if not unique_groups:
    st.error("No data found in the selected grouping column.")
    st.stop()

selected_group = st.selectbox("Select Component Family to Analyze:", unique_groups)

# Filter Dataset
subset = df[df[c_die].astype(str) == selected_group]

# 2. Quick Stats (KPIs)
st.markdown("---")
kpi_header = st.columns([1, 1])
with kpi_header[0]:
    st.markdown("#### Key highlights")
with kpi_header[1]:
    st.caption("Metrics update as you switch component families.")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

num_suppliers = subset[c_supplier].nunique()
num_features = len(c_features)
total_records = len(subset)

# Calculate top supplier safely
if not subset.empty:
    top_supplier = subset[c_supplier].mode()[0]
else:
    top_supplier = "N/A"

kpi1.metric("Active Suppliers", num_suppliers)
kpi2.metric("Features Tracked", num_features)
kpi3.metric("Total Records", total_records)
kpi4.metric("Top Supplier", top_supplier)
st.markdown("---")

# 3. Data Processing for Views
agg_df = aggregate_data(subset, c_die, c_supplier, c_features)

if agg_df.empty:
    st.warning("No data available for this selection.")
    st.stop()

# VIEW A: Catalog (Suppliers = Rows, Features = Columns)
view_catalog = agg_df.set_index(c_supplier)[c_features]

# VIEW B: Matrix (Features = Rows, Suppliers = Columns) -> Transpose
view_matrix = view_catalog.transpose()

# --- Tabs Implementation ---
tab_matrix, tab_catalog = st.tabs(["📊 Compare View (Matrix)", "📋 Catalog View (List)"])

with tab_matrix:
    st.markdown("#### ⚔️ Head-to-Head Comparison")
    st.caption(f"Comparing **{len(c_features)} features** across **{num_suppliers} suppliers**. (Suppliers are Columns)")

    st.dataframe(
        view_matrix,
        use_container_width=True,
        height=420,
        column_config={
            col: st.column_config.TextColumn(col)
            for col in view_matrix.columns
        }
    )

with tab_catalog:
    st.markdown("#### 📚 Supplier Catalog")
    st.caption("Detailed breakdown per supplier. (Suppliers are Rows)")

    st.dataframe(
        view_catalog,
        use_container_width=True,
        height=420
    )
