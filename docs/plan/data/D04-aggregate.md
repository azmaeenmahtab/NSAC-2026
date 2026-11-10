# D04 Monthly cell and region tables

Depends: D03. Priority: P0. Window: EVENT. Read first: DB_SCHEMA.md `monthly_cell`, `monthly_region`.

## Goal
Aggregate events to monthly counts per H3 cell and per district, dense and consistent.

## Files (`pipeline/src/pyroscope_pipeline/aggregate/`)
`monthly.py` (pure group-bys), `coverage.py` (family coverage months), `run.py`, tests in `pipeline/tests/aggregate/`.

## Specification
- `monthly_cell`: group events with a district by `(h3_r7, family, year, month)`; keep `h3_r6`, `h3_r5`, `district_id`; sum `frp_sum`; count events. Sparse (non-zero only).
- `monthly_region` (district level): dense over the coverage of each family: MODIS from 2000-11, VIIRS from the first complete month found in the data (record it; expected 2012-02, VERIFY); zero rows included for district-months with no events. The latest month included is the last complete month in the data (the current partial month is excluded and handled by D08).
- Invariants checked in code and tests: `sum(monthly_cell.event_count) == sum(monthly_region.event_count)` per family and month; no negative counts; one district per cell.
- Output to `data/interim/`.

## Tests
- [ ] 10-event fixture: expected cell counts and district counts computed by hand and asserted; zero-filled district-months present; sparse cells absent
- [ ] Coverage test: MODIS rows start at 2000-11, VIIRS rows do not appear before the configured start
- [ ] Invariant tests on the fixture and on the real data (run in CI only on the fixture)

## Tasks
- [ ] Aggregations and coverage implemented
- [ ] Stage runs on real events; invariants pass; row counts logged
- [ ] Master plan row D04 set to `[x]`
