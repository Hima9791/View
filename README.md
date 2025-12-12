# Option A (Single-root): Streamlit + Embedded Web UI (no folders)

Files in repo root:
- `app.py` (Streamlit backend)
- `ui.html` (single-file front-end)
- `requirements.txt`

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Cloud)
- Main file: `app.py`

### Common error fixed in v2
If you accidentally map the **same column** for Tier1 / DieFamily / LatestCompany, pandas `melt()` will crash.
This version validates mapping and shows a friendly error instead.
