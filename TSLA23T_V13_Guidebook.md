# TSLA23T V13 Guide

## Triangles

- Green ▲: Buy / Long Entry or Cover Short.
- Red ▼: Sell / Close Long or Short Entry.
- Hover shows action, date, price, score and rules.

## Backtesting

Default thresholds: Long Entry +35, Long Exit -20, Short Entry -25, Short Exit +15. Watch tiers: Long Watch 25, Short Watch -15 (setup-forming, not a confirmed entry). Results show actual historical profit/loss calculated from Yahoo chart data.

## Counters

TSLA, RKLB, ASTS, SPCX, NVDA, EOSE, ORCL, MU, SKHY, GOOGL, SNDK, AMD, INTC, OKLO.

## Navigation

Use View Full Chart from Scanner, then use Back to Scanner above the full chart.

Note: This Streamlit package carries the V13 settings (counters, thresholds, scores). The web 23T Trading System V13 has additional web-only features (paired trade triangles, dated axes, log chart, portfolio dashboard, disable-short toggle in Settings) that are not identical in this Streamlit code; in Streamlit, shorts are controlled by Backtesting Mode (Long / Short / Both).
