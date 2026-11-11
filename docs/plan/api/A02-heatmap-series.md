# A02 Heatmap and series endpoints

Depends: A01. Priority: P0. Window: EVENT. Read first: API_REFERENCE.md rows `/api/heatmap`, `/api/series`; DB_SCHEMA.md `harmonized_cell`, `monthly_cell`, `harmonized_region`.

## Goal
Fast hex-density data for the map and monthly series (raw vs harmonized) for the charts.

## Files (`services/api/app/features/heatmap/` and `features/series/`)
`router.py`, `service.py`, `repository.py`, `schemas.py`, `tests/` in each.

## Specification
- `/api/heatmap`: params `bbox` (w,s,e,n), `from` and `to` (YYYY-MM, inclusive; defaults: the last 12 complete months), `metric` (`harmonized` from `harmonized_cell`; `raw_modis` and `raw_viirs` from `monthly_cell` filtered by family), `res` (5, 6 or 7; default by area size). Aggregate with `GROUP BY h3_r{res}` and `SUM`. Return `{ res, metric, from, to, cells: [{ h3, value }], stats: { min, max, p95 } }`. Convert UINT64 to lowercase hex strings in Python (`format(int(x), "x")`). Cap at 40,000 cells; if exceeded return 400 with a message to use a coarser `res` or smaller bbox.
- Cell inclusion by bbox uses the cell centroid columns if present or a precomputed `h3 -> lat/lon` lookup; do not call h3 functions per row in SQL unless the extension was chosen in P04. VERIFY approach from `docs/SPIKE_RESULTS.md`.
- `/api/series`: params `area_id`, `from`, `to`. For preset or district ids read `harmonized_region`; for `bbox:` areas aggregate `monthly_cell`/`harmonized_cell` over cells whose centroid is inside the bbox (limit area size and return 400 beyond it). Fields per month: `raw_modis`, `raw_viirs` (null before 2012-02), `naive_splice` (MODIS before the VIIRS start month, raw VIIRS from then on), `harmonized`, `in_overlap`, `source_used`, `provisional`.
- Response caching: in-process LRU keyed by `(data_version, params)` (max 256 entries).
- Performance target: p95 under 500 ms for a Bangladesh-wide heatmap at res 6 on the real data (measure and note in the PR).

## Tests
- [x] Fixture heatmap for the 200 cells: sum of values equals the fixture district totals for the chosen months (exact numbers from S01)
- [x] Hex ids are lowercase hex strings, 15 characters long for r7 (VERIFY length), and valid H3 cells (check with h3-py)
- [x] `res` 5 and 6 aggregate to parents; totals equal the r7 total
- [x] Series `naive_splice` equals MODIS before 2012-02 and raw VIIRS after (fixture: VIIRS = 3 x MODIS, so the splice shows a 3x jump while harmonized does not)
- [x] Validation errors: bad dates, `from` after `to`, bad metric, too many cells
- [x] Cache returns identical payloads and does not leak across data versions

## Tasks
- [x] Heatmap and series implemented with tests
- [x] OpenAPI updated if shapes changed; examples updated
- [x] Timing measured on real data and logged in the PR
- [x] Master plan row A02 set to `[x]`
