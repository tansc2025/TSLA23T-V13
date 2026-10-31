# TSLA23T V13 — Streamlit package

Streamlit version of the 23T Trading System, updated to V13 settings from the web app.

- Main file: `app.py`
- Config: `rules_config.json` (14 counters, thresholds 35 / -20 / -25 / 15, watch tiers 25 / -15)
- Guide: `TSLA23T_V13_Guidebook.md`

## Run locally

```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io and sign in with GitHub.
2. New app → Repository: `tansc2025/TSlA23T-V13` → Branch: `main` → Main file: `app.py`
3. Deploy.

Note: This Streamlit package carries the V13 settings. The web 23T Trading System V13 has additional web-only features (paired trade triangles, dated axes, log chart, portfolio dashboard) that are not identical in this Streamlit code.
