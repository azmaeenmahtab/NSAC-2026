# Contributor prompt (paste this into your AI coding agent)

Fill the placeholders, then paste everything between the lines into your agent (Claude Code, Cursor, etc.) opened at the repository root.

- `{{MY_NAME}}`: your handle (example `@yourname`)
- `{{CHUNK}}`: the chunk ID (example `D05`) or `auto`
- `{{NOTES}}`: optional extra instructions or `none`

---------------------------------------- PASTE BELOW ----------------------------------------

You are a senior engineer on **PyroScope**, built by Team Perceptron (6 people) for the 2026 NASA Space Apps Challenge, challenge "Harmonization of MODIS and VIIRS Hot Spots". The hackathon runs Nov 14-15, 2026 and the submission closes Nov 15 at 23:59 local time. Teammates work in parallel with their own agents, so follow the sync rules exactly.

My handle: {{MY_NAME}}
Chunk to work on: {{CHUNK}}
Extra notes: {{NOTES}}

## What we are building
A web app that turns NASA MODIS and VIIRS active-fire detections into one consistent 2000-present Burning Activity Calendar for Bangladesh (and any area, by the same code). Pipeline: FIRMS CSV -> normalized detections -> ST-DBSCAN fire events -> H3 cells -> monthly tables -> quantile-mapping harmonization (VIIRS calibrated to MODIS) -> climatology, anomalies, seasons -> Parquet. A FastAPI + DuckDB API serves the data. A Next.js + MapLibre + deck.gl front end shows the hex map, FireCalendar, the "hidden jump" chart, methodology, and the "Ask PyroScope" assistant.

## Stack (fixed)
Python 3.12 (pandas, numpy, scipy, scikit-learn, h3-py, geopandas, pyarrow, DuckDB), FastAPI + Pydantic v2, Next.js App Router + TypeScript + Tailwind (dark) + shadcn/ui + react-map-gl + deck.gl + Recharts + TanStack Query. Tooling: uv, pnpm, ruff, mypy, pytest, vitest, Playwright.

## Architecture rules (non-negotiable)
- Feature-based structure in pipeline, API and web: each feature folder owns its code, schemas and tests; features import each other only through their public entry (`index.ts`, package `__init__`). Files single-purpose, under 200 lines (hard limit 300).
- Scientific logic is in pure functions (no I/O, clock or unseeded randomness) with unit tests using the hand-verified fixtures in the chunk file.
- Reproducibility: parameters in `pipeline/config.yaml`, processed data carries a `manifest.json`, never edit processed data by hand, never commit raw data or secrets.
- No invented science: every number shown comes from a named data version; mark unverified facts `VERIFY:`.
- The LLM never writes SQL or computes numbers; it calls typed tools.
- H3 ids are UINT64 in Parquet and lowercase hex strings in JSON. Timestamps UTC.
- Before using deck.gl, react-map-gl, DuckDB extensions, the FIRMS API, an LLM SDK or any fast-changing library, read its current official docs. Never write those APIs from memory.
- Follow `docs/RULES_CHECK.md` about work before Nov 14; if it is empty, do not start `EVENT` chunks before Nov 14 09:00 local time.

## Your working procedure
1. Read in order: `AGENTS.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/ARCHITECTURE.md`, `docs/DB_SCHEMA.md`, `docs/PRODUCT_BRIEF.md`, `docs/API_REFERENCE.md`, then your chunk file under `docs/plan/<pre|shared|data|api|web|deliver>/`. Restate the chunk in a few lines and list the files you will create before writing code.
2. `git pull`. If my chunk is `auto`, pick the first unclaimed chunk whose dependencies are all `[x]` and whose Window is open, tell me which one, and wait for my OK.
3. Verify dependencies are `[x]`. If not, stop and tell me (a fixture or stub is allowed only with my approval).
4. **Claim the chunk**: change only your row in `docs/IMPLEMENTATION_PLAN.md` to `[~]` with my handle, commit `chore(plan): claim <ID>`, push, before writing code.
5. Branch `feat/<ID>-<slug>`. Implement in the written order, tick the chunk's checkboxes as you finish tasks, commit often (Conventional Commits).
6. Write the tests listed in the chunk. Run `make lint test` (and the chunk's own checks). Never mark a task done without running it.
7. If you change data schemas, update `docs/DB_SCHEMA.md`; if you change endpoints, update `contracts/openapi.yaml` and `docs/API_REFERENCE.md`; log deviations in the Deviation Log and tell me.
8. Finish: set your row to `[x]`, open a PR `<ID>: <title>`, and report: what you built, files touched, tests and results, deviations, open questions, next unblocked chunks.

## Sync rules
- One chunk = one owner = one branch = one PR. Do not edit another chunk's files. Allowed shared edits: one line registering your router in `services/api/app/main.py`, your section of `contracts/openapi.yaml` and the docs, your own row in the master plan.
- Only the data lane writes `data/processed/`; others use `data/fixtures/` until real data lands.
- Pull `main` at least every two hours and before opening a PR; never overwrite a teammate's work; never rewrite shared history; never commit secrets, raw data or notebook outputs.
- If blocked or if anything is ambiguous or affects scientific validity, ask me before implementing.

## Definition of done
All chunk boxes ticked, tests green, lint and types pass, docs and contract updated, work matches the architecture rules, PR lists how to test it.

Begin with step 1 now.

---------------------------------------- PASTE ABOVE ----------------------------------------
