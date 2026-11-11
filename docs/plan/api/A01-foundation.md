# A01 API foundation, data loading, meta and areas

Depends: S01. Priority: P0. Window: EVENT. Read first: ARCHITECTURE.md section 4; API_REFERENCE.md; the current FastAPI and DuckDB docs.

## Goal
A running FastAPI service that loads the processed (or fixture) Parquet data into DuckDB views, serves `/api/health`, `/api/meta`, `/api/areas`, and provides the shared plumbing for every other API feature.

## Files (`services/api/app/`)
`main.py`, `core/{config.py,errors.py,logging.py,ratelimit.py,db.py,dataset.py,responses.py}`, `features/meta/{router.py,service.py,schemas.py}`, `features/areas/{router.py,service.py,repository.py,schemas.py}`, `tests/` (use `data/fixtures/`).

## Specification
- `core/config.py`: pydantic-settings from env (`DATA_DIR`, `WEB_ORIGIN`, `LLM_PROVIDER`, ...). Default `DATA_DIR` points to `data/fixtures` in tests.
- `core/dataset.py`: on startup read `manifest.json`, verify the listed files exist, register each Parquet as a DuckDB view (read-only connection, one connection per worker, `read_parquet`). Expose `DataVersion` and `as_of`. `POST /api/admin/reload` is NOT exposed; reload by restart.
- `core/responses.py`: success envelope with `meta.dataVersion` and `meta.asOf`; `core/errors.py`: error envelope and handlers for validation errors (400), not found (404), rate limit (429), upstream (502), internal (500) with request ids.
- Middleware: request id, CORS for `WEB_ORIGIN` only, slowapi rate limits (120 per minute default).
- `meta`: data version, as-of, provisional-from, a safe subset of parameters, source list, counts, attribution text.
- `areas`: from `regions.parquet`; filter by `level`; resolve region ids and `bbox:<w>,<s>,<e>,<n>` strings (validate numbers and ranges) via a shared `resolve_area(area_id)` used by all features (returns type, region ids or bbox).
- All SQL uses bound parameters; identifiers only from whitelists.
- OpenAPI served at `/api/openapi.json` and must match `contracts/openapi.yaml` (test).

## Tests
- [x] Health, meta and areas endpoints against fixtures (shape equals the OpenAPI examples)
- [x] Bad `level`, bad bbox (west >= east, out of range) return 400 with the error envelope
- [x] Unknown area returns 404; CORS header absent for a different origin; 121st request returns 429
- [x] Startup fails with a clear message when `manifest.json` is missing or a file is absent
- [x] Contract test: generated OpenAPI equals the committed contract for implemented paths

## Tasks
- [x] Core plumbing, meta and areas implemented
- [x] Router registration pattern documented in `main.py` (one line per feature)
- [x] Dockerfile stub builds
- [x] Master plan row A01 set to `[x]`
