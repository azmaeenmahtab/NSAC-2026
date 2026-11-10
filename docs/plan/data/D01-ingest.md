# D01 Ingest and normalize FIRMS CSVs

Depends: S00, P01. Priority: P0. Window: EVENT. Read first: DB_SCHEMA.md `detections`; `docs/DATA_FINDINGS.md` (P02) for the real column names.

## Goal
Turn the raw MODIS and VIIRS CSVs into one clean `detections.parquet` with a unified schema, deterministic ids and a dropped-rows report.

## Files (`pipeline/src/pyroscope_pipeline/ingest/`)
`readers.py` (per-sensor CSV readers), `normalize.py` (pure transforms), `confidence.py` (pure filter), `firms_api.py` (HTTP client, reused by D08), `run.py` (stage), `__init__.py`; tests in `pipeline/tests/ingest/` with tiny CSV fixtures.

## Specification
- Read in chunks (pandas `chunksize`) to bound memory. Column maps from P02 findings: MODIS `brightness`, `bright_t31`, `confidence` numeric, `satellite` Terra/Aqua, optional `type`; VIIRS `bright_ti4`, `bright_ti5`, `confidence` in l/n/h, `satellite` N (S-NPP), N20, N21.
- `acq_ts` = `acq_date` + zero-padded `acq_time` (HHMM: pad to 4 digits, so `"52"` becomes `0052`) in UTC.
- Sensor tags: MODIS Terra -> `MODIS_TERRA`, Aqua -> `MODIS_AQUA`; VIIRS satellite code N -> `VIIRS_SNPP`, N20 -> `VIIRS_NOAA20`, N21 -> `VIIRS_NOAA21` (VERIFY codes in the files).
- Filters (config-driven): MODIS confidence >= 30 and `type == 0` when the column exists; VIIRS keep `n` and `h`. Count every dropped row by reason (`low_confidence`, `non_vegetation_type`, `invalid_coordinates`, `invalid_time`, `duplicate`) and write the counts to the manifest.
- Dedup on `(sensor, lat, lon, acq_ts)`.
- Output sorted by `acq_ts, lat, lon`, `detection_id` assigned after sorting; ZSTD Parquet in `data/interim/detections.parquet`.
- Only S-NPP for VIIRS in the main record unless config `include_viirs_noaa` is true (D08 and sensitivity runs).
- `firms_api.py`: `fetch_area(source, bbox, start_date, days, map_key)` with exponential backoff, a token bucket that keeps below 3,000 transactions per 10 minutes, redacts the MAP_KEY in logs, returns a DataFrame. VERIFY the allowed day range and transaction cost (see P01).

## Tests
- [ ] `normalize` unit tests: `acq_time` `"52"` -> `00:52`, `"1330"` -> `13:30`, `"0"` -> `00:00`
- [ ] `confidence` tests: MODIS 29 dropped, 30 kept, 80 kept; VIIRS `l` dropped, `n` and `h` kept; MODIS `type` 2 dropped
- [ ] Duplicate rows removed; counts by reason correct on a 20-row fixture
- [ ] Stage run on the fixture raw files produces the DB_SCHEMA columns and types
- [ ] Idempotent: running twice yields identical Parquet bytes content (compare a content hash)

## Tasks
- [ ] Readers, normalize, confidence filter implemented per spec
- [ ] `firms_api.py` implemented with a mocked-HTTP test for backoff and the rate limiter
- [ ] Stage `ingest` runs on the real raw files; manifest counts written; row counts logged in the PR
- [ ] Master plan row D01 set to `[x]`
