# S01 Contract first: OpenAPI, examples, deterministic fixtures, mocks

Depends: S00. Priority: P0. Window: EVENT. Read first: API_REFERENCE.md, DB_SCHEMA.md.

## Goal
Freeze the API shape and provide a tiny synthetic dataset so the API lane and both web lanes can build and test without waiting for real data.

## Files
- `contracts/openapi.yaml` (all endpoints in API_REFERENCE.md, request and response schemas, error schema, examples), `contracts/examples/*.json`
- `pipeline/src/pyroscope_pipeline/fixtures/make_fixtures.py` (deterministic, seeded) writing `data/fixtures/` Parquet files in the exact schemas of DB_SCHEMA.md (monthly_region, harmonized_region, harmonized_cell, climatology, anomalies, seasons, yearly, regions) plus `manifest.json`
- `apps/web/src/lib/api/` generated types script (`pnpm gen:api` using openapi-typescript) and `apps/web/src/mocks/` MSW handlers serving the examples

## Fixture design (so tests have exact expectations)
- 3 regions: `BGD` (country, sum of the other two), `BGD-ADM2-alpha`, `BGD-ADM2-beta`, years 2000-11 to 2025-12.
- MODIS monthly counts for alpha: `base[m] * 10 * trend`, with `base` = [1,1,2,8,10,6,1,1,1,1,1,1] for months 1 to 12 (same shape as the season test below), flat trend. VIIRS (from 2012-02) = 3 x MODIS exactly. Harmonized = MODIS-equivalent (so equals MODIS everywhere). Beta = alpha x 0.5.
- Season for alpha: start 4, peak 5, end 6, share 24/34 = 0.7059.
- 200 r7 hex cells (valid H3 ids near Bangladesh) with weights summing so that cell values add up to the district totals.
- One deliberate anomaly: alpha, year 2020, month 5 value = 2 x the baseline p95 (class extreme).
- `make_fixtures.py` is byte-for-byte deterministic (seeded; sorted output; fixed Parquet settings).

## Tasks
- [x] OpenAPI complete and validates (use an OpenAPI linter in CI)
- [x] Examples consistent with the fixture numbers
- [x] Fixture generator and fixtures committed; test that running it twice gives identical files (hash)
- [x] Types generation and MSW mocks work in the web app (a page can fetch `/api/meta` from the mock)
- [x] All lanes notified that the contract is frozen; later changes go through a PR that updates the OpenAPI file and the docs
- [x] Master plan row S01 set to `[x]`
