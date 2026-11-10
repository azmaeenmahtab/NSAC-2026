# D06 Run harmonization, downscale to cells, validation report

Depends: D04, D05. Priority: P0. Window: EVENT. Read first: DB_SCHEMA.md `harmonized_region`, `calibration_report`, `harmonized_cell`; PRODUCT_BRIEF.md section 5.

## Goal
Produce the harmonized MODIS-equivalent record per district, aggregated up, downscaled to cells, with an honest validation report.

## Files (`pipeline/src/pyroscope_pipeline/harmonize/`)
`units.py` (calibration unit selection), `build.py` (stage logic), `downscale.py` (pure), `aggregate_up.py` (pure), `jump_metrics.py` (pure), `run.py`; tests in `pipeline/tests/harmonize/`.

## Specification
- **Calibration units**: for each district compute the mean monthly MODIS event count over the overlap; if it is below `min_mean_monthly_modis` (3) the district uses its parent division's series (sum of its districts) as the calibration series; the district then receives the division's fitted function. Record `calibration_unit_id` and `fallback_to_parent`.
- **Fit and choose**: per unit run D05 fitting and CV for both methods; choose per unit; write `calibration_report` (metrics, method, knots JSON).
- **Apply**: for every district-month in the overlap or later, `harmonized = apply(method, raw_viirs)`; `source_used = viirs_calibrated`. Months before the overlap start use raw MODIS (`source_used = modis_raw`, `method = none`). `in_overlap` flags months with both sensors.
- **Aggregate up (bottom-up)**: division and country rows = sum of their districts for `raw_modis`, `raw_viirs`, `harmonized`.
- **Downscale to cells** (`downscale.py`): for months with `viirs_calibrated`, `cell_harmonized = cell_raw_viirs * (district_harmonized / district_raw_viirs)` when `district_raw_viirs > 0`; if it is 0, cells are 0 and the district value is added to `unallocated_harmonized` in the manifest. For `modis_raw` months, `cell_harmonized = cell_raw_modis`. Write `harmonized_cell` (sparse).
- **Jump metrics** (`jump_metrics.py`): for the country series compute `naive_ratio` = mean annual count of the naive splice (MODIS before 2012-02, VIIRS raw after) over 2012-2016 divided by mean annual raw MODIS over 2007-2011; `harmonized_ratio` = the same ratio on the harmonized series; guard against zero denominators. Also the overlap CV metrics for the country (sum of district predictions). State in code comments that these are descriptive, not trend tests.
- **Report figures data**: Q-Q points (sorted VIIRS vs MODIS, and VIIRS after mapping vs MODIS) for the country series, saved as JSON for the methodology page.
- Output: `data/interim/harmonized_region.parquet`, `calibration_report.parquet`, `harmonized_cell.parquet`, `diagnostics.json`.

## Tests
- [ ] On the S01 fixture (VIIRS = 3 x MODIS exactly): every district chooses a method with CV RMSE 0 within 1e-9, and `harmonized == raw_modis` equivalent everywhere in the overlap
- [ ] Aggregate-up: country equals the sum of the districts exactly (fixture)
- [ ] Downscale conservation: cell sums equal the district value within 1e-6 (fixture), and the `unallocated_harmonized` case (district raw VIIRS 0) is reported
- [ ] Fallback test: a sparse district (mean MODIS below 3) uses the parent calibration unit
- [ ] Jump metrics on a synthetic series where the splice jumps by a known factor 3: `naive_ratio` is about 3 and `harmonized_ratio` is about 1
- [ ] Determinism: identical hashes across two runs

## Tasks
- [ ] Units, build, downscale, aggregate-up, jump metrics implemented
- [ ] Stage runs on the real monthly tables; calibration report reviewed by a human: list units that fell back, units where QM beat ratio, any unit with poor CV (flag, do not hide)
- [ ] Update `docs/DATA_FINDINGS.md` with the real jump metrics and CV numbers; update the pitch owner
- [ ] Master plan row D06 set to `[x]`
