# Architecture and conventions

## 1. Stack and approved libraries

| Layer | Choice |
| --- | --- |
| Python | 3.12 (VERIFY the exact version supported by your host), `uv` with lockfile |
| Pipeline libs | pandas, numpy, scipy, scikit-learn (BallTree haversine), h3 (h3-py v4), geopandas, shapely, pyarrow, duckdb, httpx, pyyaml, pydantic |
| API | FastAPI, Pydantic v2, uvicorn, DuckDB, slowapi (rate limit), rapidfuzz (area name matching), httpx, google-genai or another SDK behind the provider adapter (VERIFY) |
| Web | Next.js App Router, React, TypeScript strict, Tailwind (dark), shadcn/ui, react-map-gl (MapLibre), deck.gl (`@deck.gl/geo-layers` H3HexagonLayer), Recharts, TanStack Query, d3-scale-chromatic, openapi-typescript, MSW (mocks) |
| Tests | pytest, hypothesis (optional), vitest, React Testing Library, Playwright |
| Tooling | ruff, mypy, pre-commit (optional), GitHub Actions, Docker (API image) |

## 2. Repository layout

```
apps/web/                         Next.js app
services/api/                     FastAPI app (package `app`)
pipeline/                         Python package `pyroscope_pipeline` + config.yaml
contracts/openapi.yaml            the API contract (source of truth for web types and mocks)
data/raw/                         raw FIRMS downloads (gitignored, shared out of band)
data/interim/                     intermediate Parquet (gitignored)
data/processed/<version>/         final Parquet + manifest.json (shipped to the API); `current` points to the active version
data/reference/                   regions.geojson, guidance.json, region_cells.parquet (committed)
data/fixtures/                    tiny deterministic synthetic dataset (committed, used by tests and mocks)
spikes/                           throwaway experiments (excluded from the submission build)
docs/                             plan and design docs
Makefile                          setup, dev, lint, test, pipeline, api, web
```

## 3. Pipeline architecture (feature-based, pure engines)

```
pipeline/src/pyroscope_pipeline/
  common/        config loading, paths, logging, manifest, h3 helpers, time helpers
  ingest/        FIRMS readers and API client, normalization        (D01, D08)
  clustering/    st_dbscan.py (pure), events.py                     (D02, D03)
  aggregate/     monthly cell and region tables                     (D04)
  harmonize/     quantile_map.py, ratio.py, evaluate.py (pure), run (D05, D06)
  stats/         climatology, anomalies, seasons, yearly (pure)     (D07)
  nrt/           incremental update                                 (D08)
  cli.py         `python -m pyroscope_pipeline <stage>`
  tests/ per feature folder
```

Rules: `engine`-style modules are pure (inputs in, outputs out, no I/O, no clock, no randomness without a seed). IO wrappers live next to them in `run.py`. Stages read and write Parquet with ZSTD compression, in the schemas of `docs/DB_SCHEMA.md`.

Data flow: raw CSV -> `detections.parquet` -> `events.parquet` -> `monthly_cell.parquet`, `monthly_region.parquet` -> `harmonized_region.parquet`, `harmonized_cell.parquet` -> `climatology.parquet`, `anomalies.parquet`, `seasons.parquet`, `yearly.parquet` -> `data/processed/<version>/` with `manifest.json`.

## 4. API architecture (FastAPI)

```
services/api/app/
  main.py            app factory, middleware, router registration (one line per feature)
  core/              config (pydantic-settings), errors, logging, rate limit, duckdb connection, data version
  features/<feature>/
    router.py        HTTP only
    service.py       business logic
    repository.py    DuckDB queries (parameterized, read-only)
    schemas.py       Pydantic models (match contracts/openapi.yaml)
    tests/
  features: meta, areas, heatmap, series, calendar, stats, methodology, ask, guidance, alerts
```

Layer rules: router -> service -> repository. Repositories use parameterized SQL only; user input never goes into SQL strings (use bound parameters; validate identifiers against whitelists). The API reads `data/processed/current/` at startup, registers Parquet files as DuckDB views, and exposes the data version in every response (`meta.dataVersion`). The API imports pure functions from `pyroscope_pipeline` (installed editable) instead of re-implementing them.

API conventions: base `/api`; success `{ "data": ..., "meta": { "dataVersion": "...", "asOf": "..." } }`; error `{ "error": { "code": "...", "message": "...", "requestId": "..." } }` with codes `VALIDATION_ERROR` 422->400, `NOT_FOUND` 404, `RATE_LIMITED` 429, `UPSTREAM_ERROR` 502, `INTERNAL` 500. CORS only for `WEB_ORIGIN`. IDs and h3 as strings. Dates `YYYY-MM` or `YYYY-MM-DD`.

## 5. Frontend architecture (feature-based)

```
apps/web/src/
  app/                 routing only; each page under 40 lines
  features/<feature>/{api,components,hooks,lib,types.ts,index.ts}
    features: map, areas, calendar, series, stats, guidance, alerts, ask, methodology, shell
  components/ui/       shadcn primitives
  components/layout/   app shell, header, panels
  lib/api/             typed client generated from contracts/openapi.yaml, error handling, env
  lib/color/           inferno/viridis scales, legend helpers
  providers/
  mocks/               MSW handlers using contracts/examples and data/fixtures
```

Rules: Server Components by default; client components for map and charts. A feature imports another feature only through its `index.ts`. State in the URL for shareable views (`?area=&from=&to=&metric=&cell=`). Every screen has loading, empty, error and data states. Text from the API or LLM is rendered as plain text. Map layers must stay at 30 fps or better on a mid-range laptop with up to 30,000 cells (target, measure it).

## 6. Time, units, identifiers

- UTC everywhere in data; the UI labels local months in the Asia/Dhaka calendar only where stated. An event belongs to the calendar month of its start timestamp in UTC (decision D-05 in PRODUCT_BRIEF).
- Region ids: `BGD` (country), `BGD-ADM1-<slug>`, `BGD-ADM2-<slug>`, `PRESET-CHT`. Custom areas use `bbox:<w>,<s>,<e>,<n>`.
- Sensor families: `MODIS` (Terra+Aqua) and `VIIRS` (S-NPP primary; NOAA-20/21 used for NRT only, see PRODUCT_BRIEF).

## 7. Security and privacy (kept simple, no user accounts)

Validate all inputs (Pydantic, whitelists); rate limit `/api/ask` (10 per minute per IP) and alert subscriptions; LLM key server-side only; limit prompt length (500 characters); never echo raw model output as HTML; store only an optional email address for alert subscriptions with explicit consent and an unsubscribe link; no analytics without need; CORS locked to the web origin; dependency audit in CI.

## 8. Testing standards

- Pure engines: unit tests with the exact fixtures in the chunk files; property tests where marked.
- API: pytest with the fixture dataset (`data/fixtures/`), every route covers success, validation error, not found.
- Web: vitest for hooks and logic, RTL for components with logic, Playwright smoke for the demo path (map loads, area select, calendar shows, ask returns in replay mode).
- Performance targets (measure and report, never claim unmeasured): `/api/heatmap` p95 under 500 ms on the processed Bangladesh dataset; `/api/calendar` under 300 ms; full pipeline run under 20 minutes on a laptop.

## 9. Code standards

Python: ruff + mypy (strict on pipeline engines), type hints everywhere, dataclasses or Pydantic models for structured data, no notebooks in `src/`, functions under 40 lines, docstrings on public engine functions stating inputs, outputs, units. TypeScript: strict, no `any`, named exports, small components, no dead code, comments explain why. Names: Python `snake_case`, TS `camelCase` and `PascalCase` components, files `kebab-case.tsx`.

## 10. Environment variables

`services/api/.env.example`: `DATA_DIR=../../data/processed/current`, `WEB_ORIGIN=http://localhost:3000`, `LLM_PROVIDER=replay` (gemini|replay), `LLM_MODEL=` (VERIFY a current model id), `GEMINI_API_KEY=`, `SMTP_HOST=`, `SMTP_USER=`, `SMTP_PASSWORD=`, `ALERTS_FROM=`, `APP_DB_PATH=./app.db`.
`pipeline/.env.example`: `FIRMS_MAP_KEY=`, `DATA_ROOT=../data`.
`apps/web/.env.example`: `NEXT_PUBLIC_API_URL=http://localhost:8000`, `NEXT_PUBLIC_USE_MOCKS=false`, `NEXT_PUBLIC_BASEMAP_STYLE_URL=` (VERIFY a free style URL and its terms).

## 11. Git workflow

`main` stays green. Branches `feat/<ID>-<slug>`, one chunk per PR, squash merge, Conventional Commits. CI: ruff, mypy, pytest, web typecheck, lint, vitest.
