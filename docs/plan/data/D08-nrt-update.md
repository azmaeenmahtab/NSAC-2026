# D08 NRT incremental update and provisional flags

Depends: D03, D07. Priority: P1. Window: EVENT. Read first: the current FIRMS NRT notes (VERIFY which NRT products exist, retention, and whether S-NPP products are ending: a third-party source mentions FIRMS data products ceasing on 2026-11-01; check the FIRMS news page).

## Goal
Keep the dataset alive: fetch recent detections, run the same pipeline on the new days, mark them provisional, and refresh the current-month status.

## Files (`pipeline/src/pyroscope_pipeline/nrt/`)
`plan.py` (pure: which days are missing), `fetch.py` (uses `ingest/firms_api.py`), `merge.py` (pure: append and recompute affected months), `run.py`; tests in `pipeline/tests/nrt/`. A GitHub Actions workflow `nrt.yml` (scheduled daily, manual trigger) that runs the stage and publishes a new processed version.

## Specification
- Read `manifest.json` `as_of_date`. Plan the missing days up to yesterday (UTC). Fetch NRT sources: `MODIS_NRT` and `VIIRS_SNPP_NRT`; if S-NPP is not available, use `VIIRS_NOAA20_NRT` or `VIIRS_NOAA21_NRT` and apply the cross-sensor factor below.
- Cross-sensor factor (only when S-NPP is unavailable): compute on a shared window of at least 2 years the ratio of S-NPP events to NOAA-20 events per calibration unit and month-group, with CV; if not available in time, label the data "provisional, unadjusted NOAA-20".
- Run normalize, cluster (with a time buffer: re-cluster the last 3 days of existing detections plus the new ones so events that span the boundary stay correct), aggregate, apply the stored transfer functions from `calibration_report` (do not refit), and mark rows `provisional = true` from `provisional_from`.
- Provisional rows are never used in climatology baselines. The current month's anomaly is evaluated on month-to-date versus the climatological month-to-date (scale the baseline by days elapsed / days in month, state this in the manifest as an approximation).
- Rate limit: stay below 3,000 transactions per 10 minutes; retry on 5xx/504.
- Publish: new `data/processed/<version>/`, `current` pointer updated, API reload endpoint or restart (see A01).

## Tests
- [x] `plan.py`: given `as_of_date = 2026-11-01` and today `2026-11-04`, plans days Nov 2 to Nov 3
- [x] `merge.py`: appending a day to a fixture changes only the affected month rows; boundary-spanning event re-clustered correctly (fixture with a 2-day event across the boundary)
- [x] Provisional rows excluded from climatology (fixture)
- [x] Mocked FIRMS responses for the fetch (success, 504 then success, empty day)

## Tasks
- [x] Plan, fetch, merge, run implemented
- [x] Manual run against the live FIRMS service with a real MAP_KEY for 3 days; results logged
- [x] Scheduled workflow committed (disabled until the key is added as a secret)
- [x] Master plan row D08 set to `[x]`

## Live Run Log (2026-11-11 UTC)
- **3-day live check (`2026-11-08..2026-11-10`, bbox `[88.0, 20.5, 92.8, 26.7]`)**:
  - `MODIS_NRT`: `2` rows (`2026-11-09`)
  - `VIIRS_SNPP_NRT`: `0` rows (confirmed retired after `2026-11-01`); automatic fallback triggered to `VIIRS_NOAA20_NRT`
  - `VIIRS_NOAA20_NRT`: `55` rows across `2026-11-08`, `2026-11-09`, `2026-11-10`
  - Normalized: `57` raw rows -> `4` low-confidence dropped -> `53` kept (`errors = []`)
- **Full live NRT update (`python -m pyroscope_pipeline nrt`, `2026-11-01..2026-11-10`)**:
  - Mid-range S-NPP cutoff handled automatically: `VIIRS_SNPP_NRT` delivered `2026-11-01`, then switched to `VIIRS_NOAA20_NRT` for `2026-11-02..2026-11-10` (`viirs_source_used = "VIIRS_SNPP_NRT+VIIRS_NOAA20_NRT"`)
  - `nrt_raw_rows = 127`, `nrt_kept_rows = 119`, `affected_months = ["2026-11"]` (`elapsed = 14.05s`)
  - Published `v2026-11-10-3206108c` (`as_of_date = "2026-11-10"`, `provisional_from = "2026-11-01"`), idempotency verified (`status = "up_to_date"` on immediate second run), and FastAPI `/api/meta`, `/api/calendar`, `/api/series` verified `200` with `provisional = true` on `2026-11`.
