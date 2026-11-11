# A03 Calendar, yearly stats, anomalies, methodology

Depends: A01. Priority: P0. Window: EVENT. Read first: API_REFERENCE.md rows `/api/calendar`, `/api/stats/yearly`, `/api/anomalies`, `/api/methodology`; DB_SCHEMA.md stats tables.

## Goal
Serve the calendar grid, season, anomalies, yearly stats and the methodology evidence for any preset region, and compute the same statistics on the fly for custom bbox areas using the pipeline's pure functions.

## Files (`services/api/app/features/{calendar,stats,methodology}/`)
Each with `router.py`, `service.py`, `repository.py`, `schemas.py`, `tests/`.

## Specification
- `/api/calendar?area_id=`: for preset or district ids read `harmonized_region`, `climatology`, `anomalies`, `seasons`. Return `{ years: [...], grid: [{ year, month, value, class, percentileRank, provisional }], climatology: [{ month, mean, p50, p90, p95 }], season: { startMonth, peakMonth, endMonth, shareOfAnnual } }`.
- For `bbox:` areas: build the monthly series from cells in the bbox and call `pyroscope_pipeline.stats` functions (climatology, anomalies, seasons) so results use the exact same code. Limit bbox size and cache.
- `/api/stats/yearly`, `/api/anomalies` (filter `year`, `class`): straight reads with the same on-the-fly path for bbox areas.
- `/api/methodology`: from `manifest.json`, `calibration_report`, `diagnostics.json`: parameters, per-unit chosen method and CV metrics (summarized: counts by method, median RMSE, worst units), country-level overlap CV, Q-Q points, jump metrics (`naive_ratio`, `harmonized_ratio`), counts of dropped detections by reason, and the fixed list of limitations (copy from PRODUCT_BRIEF section 7). Include attribution text.
- Provisional months are flagged and excluded from the baselines (already true in the data; just pass flags through).

## Tests
- [x] Fixture calendar for alpha: season start 4, peak 5, end 6, share 0.7059; the 2020-05 cell is `extreme`
- [x] Yearly ranks and `vs_mean_pct` match the fixture values
- [x] On-the-fly bbox covering all fixture cells reproduces the country calendar exactly
- [x] Methodology payload contains every required key; limitations list is non-empty and unchanged from the brief
- [x] Validation, 404 and size-limit tests

## Tasks
- [x] Three features implemented with tests (calendar, stats/anomalies, methodology)
- [x] OpenAPI and examples updated
- [x] Master plan row A03 set to `[x]`
