# D03 Build fire events and H3 index

Depends: D01, D02, P03. Priority: P0. Window: EVENT. Read first: DB_SCHEMA.md `events`, regions reference.

## Goal
Cluster detections into fire events per sensor family, attach H3 ids and district, and write `events.parquet`.

## Files (`pipeline/src/pyroscope_pipeline/clustering/`)
`events.py` (pure: labels + detections -> events), `h3_index.py` (h3-py helpers), `regions.py` (point-in-district assignment using the reference polygons), `run.py` (stage); tests under `pipeline/tests/clustering/`.

## Specification
- Cluster each sensor family separately (`MODIS` = Terra+Aqua together, `VIIRS` = S-NPP, plus others only if configured). Time axis = hours since the first detection.
- Event record per cluster: `n_pixels`, `start_ts` (min), `end_ts` (max), `lat` and `lon` (mean of pixels), `frp_sum` (sum, ignoring nulls), `frp_max`, `year` and `month` from `start_ts` in UTC. Noise points (`-1`) are not events; count them in the manifest by family.
- H3: `h3_r7` from lat/lon; `h3_r6`, `h3_r5` are the parents (h3-py v4: VERIFY function names such as `latlng_to_cell` and `cell_to_parent`). Store as UINT64 (convert from the hex string with `int(x, 16)`).
- District assignment: point-in-polygon against the full-resolution ADM2 polygons (geopandas spatial join, or use `region_cells` for r7 cell lookup, whichever is faster; they must agree). Events outside Bangladesh get `district_id = null`, are kept in `events.parquet` but excluded downstream; count them.
- Order events by `start_ts, lat, lon` and assign `event_id` sequentially so reruns are identical.
- Report in the manifest: pixels in, events out, noise points, events outside, per family; and the VIIRS/MODIS ratio of pixels and of events per year (this shows how much clustering reduces the sensor disparity, a useful pitch number if real).

## Tests
- [ ] `events.py` on a hand-built 6-detection input: two clusters with known centroid (mean), `n_pixels`, start and end, FRP sum, and month; a MODIS and a VIIRS pixel at the same place and time must NOT merge (different families)
- [ ] H3 round trip: for 3 known lat/lon pairs compare `h3_r7` against values computed with the h3 CLI or docs examples; parent relation holds (`parent(h3_r7, 6) == h3_r6`)
- [ ] District assignment: a point inside Rangamati returns `BGD-ADM2-rangamati`; a point in the Bay of Bengal returns null
- [ ] Determinism: two runs give identical content hashes

## Tasks
- [ ] events, h3 helpers, region assignment, stage implemented
- [ ] Stage runs on the real detections; manifest report written; runtime logged
- [ ] Sanity table in the PR: events per year per family; ratio of VIIRS to MODIS events per year
- [ ] Master plan row D03 set to `[x]`
