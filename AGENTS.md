# AGENTS.md: rules for every AI coding agent on PyroScope

PyroScope harmonizes NASA MODIS and VIIRS active-fire records into one consistent "Burning Activity Calendar" web app (NASA Space Apps Challenge 2026, challenge "Harmonization of MODIS and VIIRS Hot Spots"). Six humans work in parallel, each with an AI agent. The hackathon runs Nov 14-15, 2026; submission closes Nov 15, 23:59 local time. Scientific honesty, reproducibility and consistency matter more than typing speed.

## 1. Read order (every session, before writing code)

1. `docs/IMPLEMENTATION_PLAN.md`: what is done, claimed, next.
2. `docs/ARCHITECTURE.md`: conventions you must follow.
3. `docs/DB_SCHEMA.md`: every data table, how they relate, invariants.
4. `docs/PRODUCT_BRIEF.md`: product, method, parameters, scoring map, decisions.
5. `docs/API_REFERENCE.md`: every endpoint and response shape.
6. Your chunk file in `docs/plan/<pre|shared|data|api|web|deliver>/`.

Do not start coding until you have read all six. If something is not written down, ask the human; do not guess.

## 2. Stack (fixed)

- Data pipeline: Python 3.12, pandas, numpy, scipy, scikit-learn (BallTree), h3-py, geopandas/shapely, pyarrow, DuckDB. Package `pipeline/`.
- API: FastAPI + Pydantic v2 + DuckDB reading Parquet. Package `services/api/`.
- Web: Next.js (App Router, TypeScript), Tailwind (dark theme), shadcn/ui, MapLibre via react-map-gl, deck.gl (`H3HexagonLayer`), Recharts, TanStack Query.
- Tooling: `uv` for Python, `pnpm` for web, ruff, mypy, pytest, vitest, Playwright, GitHub Actions.
- No database server. Data is Parquet files plus one SQLite file for app state.

## 3. Non-negotiable rules

1. **Feature-based structure** in pipeline, API and web. A feature folder owns its code, schemas and tests. No global dumping folders. See ARCHITECTURE.md.
2. **One responsibility per file**, target under 200 lines, hard limit 300.
3. **Pure engines.** Scientific logic (clustering, harmonization, statistics) lives in pure functions with no file, network or clock access, unit-tested with the hand-verified fixtures in the chunk files.
4. **Reproducible data.** Every parameter lives in `pipeline/config.yaml`. Every processed dataset has a `manifest.json` (data version, parameters, row counts, source files, git commit). Never edit processed data by hand. Raw data is never committed.
5. **No invented science.** Never claim an accuracy, trend or number the data does not show. Every number shown in the UI or by the assistant comes from the processed data of a named data version. Mark unverified facts `VERIFY:` and say how to verify.
6. **The LLM never writes SQL and never computes numbers.** It calls typed tools; the tools return numbers.
7. **Units and time.** Timestamps UTC. Coordinates WGS84 lat/lon. H3 ids are 64-bit unsigned integers in Parquet and **lowercase hex strings in any JSON** (JSON numbers lose precision above 2^53).
8. **Volatile libraries and APIs** (deck.gl, react-map-gl, DuckDB extensions, FIRMS API, LLM SDK, Next.js): read the current official docs before writing code that uses them. Never write those APIs from memory. Record what you verified in the chunk's PR description.
9. **Tests are part of the task.** A chunk is not done until its tests pass and `make lint test` is green.
10. **Secrets** (FIRMS MAP_KEY, LLM key, SMTP) never enter the repo; only names in `.env.example`.
11. **Attribution and licensing.** Keep the NASA FIRMS acknowledgement, basemap attribution and boundary-data license notices in the UI and README.
12. **Before-event rule.** Follow the decision recorded in `docs/RULES_CHECK.md` about work done before Nov 14. If it is not filled in, treat chunks with Window `EVENT` as not startable before Nov 14 09:00 local time.

## 4. Working on a chunk (the loop)

1. `git pull` the latest `main`; re-read the master plan.
2. Pick your chunk (assigned by the human, or the first unclaimed chunk whose dependencies are all `[x]` and whose Window is open). Tell the human which one you picked.
3. **Claim it**: change only that chunk's row in `docs/IMPLEMENTATION_PLAN.md` to `[~] @handle`, commit `chore(plan): claim <ID>`, push, before coding.
4. Branch `feat/<ID>-<slug>`.
5. Implement in the order written. After each task tick its checkbox in the chunk file and commit (Conventional Commits).
6. Deviations: append one line to the Deviation Log (what, why, impact).
7. Schema or data-contract change: update `docs/DB_SCHEMA.md` and/or `contracts/openapi.yaml` and `docs/API_REFERENCE.md` in the same commit.
8. Finish: `make lint test`, tick all boxes, set the row to `[x] @handle`, open a PR `<ID>: <title>`, report: what was built, files, tests, deviations, open questions.

## 5. Sync rules for parallel work

- One chunk = one owner = one branch = one PR. Do not edit another chunk's files. Allowed shared edits: one line to register your router in `services/api/app/main.py`, your feature's section in `contracts/openapi.yaml`, your sections of the docs, your own row in the master plan.
- Only the data lane writes into `data/processed/`. Everyone else reads it. Use the fixtures in `data/fixtures/` while real data is not ready.
- Pull `main` at least every two hours and before a PR. Never rewrite shared history. Never commit `.env`, raw data or notebooks with outputs.
- Blocked by another chunk? Stop, tell the human, use the fixture or a clearly marked stub inside your own feature folder.

## 6. Never do this

- Do not add libraries not listed in ARCHITECTURE.md section 1 without asking.
- Do not build out-of-scope items (global coverage, burned-area product, mobile app, user accounts, Text-to-SQL).
- Do not mark a task done without running it. Do not claim a write or download succeeded without checking the output.
- Do not weaken a test to make it pass; fix the cause.
