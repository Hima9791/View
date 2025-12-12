# Option A (Single-root): Streamlit + Embedded Web UI (no folders)

This version keeps **everything in the repo root**:
- `app.py` (Streamlit backend)
- `ui.html` (single-file front-end, no build step)
- `requirements.txt`

✅ Works on Streamlit Cloud without Node / npm.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud (GitHub)
1. Push these files to GitHub.
2. In Streamlit Cloud:
   - Main file: `app.py`

## Notes
- UI is a single HTML/CSS/JS file embedded via Streamlit `components.html`.
- Multi-values are joined with comma: `", "` (no `||`).
