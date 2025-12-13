import streamlit as st
import pandas as pd
import re

# ==========================================
# 1. CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Component Analytics Pro",
    layout="wide",
    page_icon="💠",
    initial_sidebar_state="expanded"
)

# Custom CSS for a "Fantastic" Design
st.markdown("""
<style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Header Styling */
    h1 {
        color: #1e3a8a;
        font-weight: 700;
        letter-spacing: -1px;
        padding-bottom: 10px;
        border-bottom: 2px solid #e5e7eb;
    }
    
    h3 {
        color: #374151;
        font-weight: 600;
    }

    /* Metric Cards Styling */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 15px;
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
        height: 45px;
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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOGIC
# ==========================================

@st.cache_data
def load_data(file):
    """Loads and cleans the messy Excel/CSV data."""
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    
    # Clean Column Headers: Remove "", extra spaces, and fix typos
    clean_cols = []
    for c in df.columns:
        c_str = str(c).strip()
        # FIX: Used double quotes for the regex pattern to prevent syntax errors
        c_str = re.sub(r"\", "", c_str)
        
        # Fix known typos
        if "Supplier tire" in c_str: c_str = "Tier 1"
        if "Teir" in c_str: c_str = "Tier 1"
        clean_cols.append(c_str.strip())
    
    df.columns = clean_cols
    
    # Fill NANs with empty string for cleaner display
    df = df.fillna("")
    return df

def aggregate_data(df, group_col, pivot_col, features):
    """
    Aggregates data. If multiple values exist for the same cell, joins them.
    """
    # Group by the main ID and the Supplier, then aggregate features
    # We use a lambda to join unique values with a comma
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
        # Tries to find 'Die Family' or defaults to the 2nd column
        idx_die = next((i for i, c in enumerate(cols) if "Die Family" in c), 1)
        # Tries to find 'Latest' or 'Company' or defaults to 3rd column
        idx_sup = next((i for i, c in enumerate(cols) if "Latest" in c or "Company" in c), 2)
        
        # Safety check to keep indices in bounds
        if idx_die >= len(cols): idx_die = 0
        if idx_sup >= len(cols): idx_sup = 0
        
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
    <div style='background-color: white; padding: 40px; border-radius: 10px; text-align: center; border: 2px dashed #e5e7eb;'>
        <h3 style='margin:0'>👋 Welcome!</h3>
        <p style='color: #6b7280'>Upload your component dataset to begin the analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if not c_features:
    st.error("Please select at least one feature from the sidebar.")
    st.stop()

# --- Dashboard Logic ---

# 1. Filter Context
unique_groups = sorted(list(set(df[c_die].astype(str))))
selected_group = st.selectbox("Select Component Family to Analyze:", unique_groups)

# Filter Dataset
subset = df[df[c_die].astype(str) == selected_group]

# 2. Quick Stats (KPIs)
st.markdown("---")
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

# VIEW A: Catalog (Suppliers = Rows, Features = Columns)
view_catalog = agg_df.set_index(c_supplier)[c_features]

# VIEW B: Matrix (Features = Rows, Suppliers = Columns) -> Transpose
view_matrix = view_catalog.transpose()

# --- Tabs Implementation ---
tab_matrix, tab_catalog = st.tabs(["📊 Compare View (Matrix)", "📋 Catalog View (List)"])

with tab_matrix:
    st.markdown("#### ⚔️ Head-to-Head Comparison")
    st.caption(f"Comparing **{len(c_features)} features** across **{num_suppliers} suppliers**. (Suppliers are Columns)")
    
    # Use st.dataframe with full width for a nice grid
    st.dataframe(
        view_matrix, 
        use_container_width=True, 
        height=600,
        column_config={
            # Apply generic styling to all columns
            col: st.column_config.TextColumn(wrap_text=True) 
            for col in view_matrix.columns
        }
    )

with tab_catalog:
    st.markdown("#### 📚 Supplier Catalog")
    st.caption("Detailed breakdown per supplier. (Suppliers are Rows)")
    
    st.dataframe(
        view_catalog, 
        use_container_width=True, 
        height=600
    )
