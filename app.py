import base64
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


APP_TITLE = "Supplier × DieFamily Explorer (Single-root Option A)"
UI_HTML_PATH = Path(__file__).parent / "ui.html"

MULTI_JOIN = ", "
EMPTY_TOKEN = "-"

# --- Column candidates (case-insensitive, spaces/_/- ignored) ---
TIER1_COL_CANDIDATES = [
    "Tier 1", "Tier1", "Tier 1 Supplier", "Tier1 Supplier",
    "Tire 1", "Tire1",
    "Supplier Tier 1", "Supplier_Tier1",
    "Top Supplier", "Primary Supplier",
    # common in your files:
    "Supplier Family", "SupplierFamily", "Supplier", "Supplier Name", "Tier1_Supplier"
]
LATEST_COMPANY_CANDIDATES = [
    "LatestCompanyName", "Latest Company Name", "LatestCompany",
    "CompanyName_Latest"
]
DIEFAM_CANDIDATES = [
    "DieFamily", "Die Family", "TechDieFamily", "Die_Family",
    # common in your files:
    "Die Family key", "DieFamilyKey", "Die_Family_Key"
]
NON_FEATURE_CANDIDATES = [
    "PartID", "Part Id", "Part_ID",
    "PartNumber", "Part Number", "PN", "MfrPartNumber",
    "ItemID", "Item Id",
    "CompanyName", "Company Name",
    "LatestCompanyName", "Latest Company Name",
    "Supplier", "Supplier Family",
    "Tier 1", "Tier1", "Tier 1 Supplier", "Tier1 Supplier",
    "Family", "Generic", "Series",
    "MaskedTextNon", "Status", "FinalStatus"
]


def norm(s: str) -> str:
    return re.sub(r"[\s\-_]+", "", str(s).strip().lower())

def find_col(df: pd.DataFrame, candidates):
    cmap = {norm(c): c for c in df.columns}
    for cand in candidates:
        key = norm(cand)
        if key in cmap:
            return cmap[key]
    return None

def build_non_feature_set(df: pd.DataFrame):
    nset = set(norm(c) for c in NON_FEATURE_CANDIDATES)
    cols = []
    for c in df.columns:
        if norm(c) in nset:
            cols.append(c)
    return set(cols)

def split_cell_to_values(x):
    if pd.isna(x):
        return []
    s = str(x).strip()
    if not s:
        return []
    # tolerate existing separators, but output uses comma
    parts = re.split(r"\s*\|\|\s*|\s*\|\s*", s)
    return [p.strip() for p in parts if p and p.strip()]

def concat_unique(series: pd.Series) -> str:
    all_vals = []
    for v in series:
        all_vals.extend(split_cell_to_values(v))
    if not all_vals:
        return EMPTY_TOKEN
    uniq = sorted(set(all_vals))
    return MULTI_JOIN.join(uniq)

def count_unique(series: pd.Series) -> int:
    all_vals = []
    for v in series:
        all_vals.extend(split_cell_to_values(v))
    return len(set(all_vals))


@st.cache_data(show_spinner=False)
def load_excel(uploaded_file, sheet_name):
    return pd.read_excel(uploaded_file, sheet_name=sheet_name)

@st.cache_data(show_spinner=False)
def build_records(df: pd.DataFrame, tier1_col: str, diefam_col: str, latest_col: str, feature_cols: list[str]):
    # defensive: ensure unique id_vars (pandas melt pops them)
    id_vars = [tier1_col, diefam_col, latest_col]
    if len(set(id_vars)) != 3:
        raise ValueError("Mapping error: Tier1 / DieFamily / LatestCompany must be 3 DIFFERENT columns.")

    # also ensure selected feature cols don't overlap with id_vars
    feature_cols = [c for c in feature_cols if c not in id_vars]

    long_df = df.melt(
        id_vars=id_vars,
        value_vars=feature_cols,
        var_name="FeatureName",
        value_name="FeatureValue",
    )
    long_df["FeatureValue"] = long_df["FeatureValue"].replace("", np.nan)

    agg_val = (
        long_df.groupby([tier1_col, diefam_col, latest_col, "FeatureName"])["FeatureValue"]
        .agg(concat_unique)
        .reset_index()
    )
    agg_cnt = (
        long_df.groupby([tier1_col, diefam_col, latest_col, "FeatureName"])["FeatureValue"]
        .agg(count_unique)
        .reset_index()
        .rename(columns={"FeatureValue": "Count"})
    )
    merged = agg_val.merge(agg_cnt, on=[tier1_col, diefam_col, latest_col, "FeatureName"], how="left")

    companies = sorted([c for c in merged[latest_col].dropna().astype(str).unique().tolist() if c.strip()])

    records = []
    for (t, d, f), g in merged.groupby([tier1_col, diefam_col, "FeatureName"], dropna=False):
        t = "" if pd.isna(t) else str(t)
        d = "" if pd.isna(d) else str(d)
        f = "" if pd.isna(f) else str(f)

        values = {c: EMPTY_TOKEN for c in companies}
        counts = {c: 0 for c in companies}

        for _, r in g.iterrows():
            comp = "" if pd.isna(r[latest_col]) else str(r[latest_col]).strip()
            if not comp:
                continue
            v = r["FeatureValue"]
            values[comp] = str(v).strip() if pd.notna(v) and str(v).strip() else EMPTY_TOKEN
            counts[comp] = int(r["Count"]) if pd.notna(r["Count"]) else 0

        records.append({"tier1": t, "dieFamily": d, "feature": f, "values": values, "counts": counts})

    records.sort(key=lambda x: (x["tier1"], x["dieFamily"], x["feature"]))
    return companies, records


def load_ui_html() -> str:
    if not UI_HTML_PATH.exists():
        raise FileNotFoundError(f"Missing ui.html at {UI_HTML_PATH}")
    return UI_HTML_PATH.read_text(encoding="utf-8")

def inject_data_into_html(html: str, app_data: dict) -> str:
    raw = json.dumps(app_data, ensure_ascii=False).encode("utf-8")
    b64 = base64.b64encode(raw).decode("ascii")
    inject = f"""<script>
window.__APP_DATA__ = JSON.parse(atob("{b64}"));
</script>"""
    if "</head>" in html:
        return html.replace("</head>", inject + "\n</head>", 1)
    return inject + "\n" + html


st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.caption("Single-root Option A: Streamlit backend + embedded website-style UI (no folders, no npm build).")

uploaded = st.file_uploader("Upload Excel", type=["xlsx", "xls"])
if not uploaded:
    st.info("Upload your Excel to start.")
    st.stop()

xls = pd.ExcelFile(uploaded)
sheet = st.selectbox("Sheet", options=xls.sheet_names, index=0)
df = load_excel(uploaded, sheet)

auto_tier1 = find_col(df, TIER1_COL_CANDIDATES) or df.columns[0]
auto_die   = find_col(df, DIEFAM_CANDIDATES) or df.columns[0]
auto_latest= find_col(df, LATEST_COMPANY_CANDIDATES) or df.columns[0]

with st.sidebar:
    st.header("Mapping")
    tier1_col = st.selectbox("Tier-1 Supplier column", options=df.columns.tolist(), index=df.columns.get_loc(auto_tier1))
    diefam_col = st.selectbox("DieFamily column", options=df.columns.tolist(), index=df.columns.get_loc(auto_die))
    latest_col = st.selectbox("LatestCompanyName column", options=df.columns.tolist(), index=df.columns.get_loc(auto_latest))

    # mapping validation (prevents pandas melt KeyError)
    chosen = [tier1_col, diefam_col, latest_col]
    if len(set(chosen)) != 3:
        st.error("Mapping error: Tier1 / DieFamily / LatestCompany must be 3 different columns.")
        st.stop()

    st.divider()
    st.subheader("Features")
    non_feature = build_non_feature_set(df)
    non_feature.update([tier1_col, diefam_col, latest_col])
    auto_features = [c for c in df.columns if c not in non_feature]

    manual = st.checkbox("Select features manually", value=False)
    if manual:
        feature_cols = st.multiselect("Feature columns", options=auto_features, default=auto_features)
    else:
        feature_cols = auto_features

    # Safety: remove overlap if user manually picked id vars
    feature_cols = [c for c in feature_cols if c not in chosen]

    st.divider()
    st.subheader("Performance")
    max_records = st.number_input("Max records (safety cap)", min_value=1000, max_value=200000, value=60000, step=1000)

if not feature_cols:
    st.error("No feature columns selected.")
    st.stop()

# Optional: show columns (helps debugging on Cloud)
with st.expander("Debug: show detected columns"):
    st.write("Columns:", list(df.columns))
    st.write("Tier1:", tier1_col)
    st.write("DieFamily:", diefam_col)
    st.write("LatestCompany:", latest_col)
    st.write("Feature columns:", len(feature_cols))

try:
    with st.spinner("Aggregating features for the UI..."):
        companies, records = build_records(df, tier1_col, diefam_col, latest_col, feature_cols)
except Exception as e:
    st.error("Failed while building the view. Check your mapping and sheet.")
    st.exception(e)
    st.stop()

if len(records) > int(max_records):
    records = records[: int(max_records)]
    st.warning(f"Records truncated to {max_records} for responsiveness. Increase the cap in the sidebar if needed.")

app_data = {
    "meta": {
        "fileName": getattr(uploaded, "name", ""),
        "tier1Col": str(tier1_col),
        "diefamCol": str(diefam_col),
        "latestCol": str(latest_col),
        "featureCount": int(len(feature_cols)),
        "recordCount": int(len(records)),
    },
    "companies": companies,
    "records": records,
}

ui_html = load_ui_html()
html_with_data = inject_data_into_html(ui_html, app_data)
st.components.v1.html(html_with_data, height=980, scrolling=True)
