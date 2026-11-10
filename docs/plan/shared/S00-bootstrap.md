# S00 Repo bootstrap

Depends: P00. Priority: P0. Window: EVENT. Read first: ARCHITECTURE.md sections 1, 2, 11.

## Goal
A working monorepo with Python and web tooling, a Makefile, CI, and empty feature skeletons so every lane starts on a green base.

## Files
- Root: `Makefile`, `.gitignore` (raw data, interim, node_modules, .venv, .next, .env*, app.db, notebooks outputs), `.editorconfig`, `README.md` (stub), `.github/workflows/ci.yml`
- `pipeline/`: `pyproject.toml` (package `pyroscope_pipeline`), `config.yaml` (parameters from PRODUCT_BRIEF section 5), `.env.example`, `src/pyroscope_pipeline/common/{config.py,paths.py,logging.py,manifest.py}`, `cli.py`, empty feature packages with `__init__.py`, `tests/`
- `services/api/`: `pyproject.toml` (depends on the pipeline package, editable), `app/main.py` (app factory stub), `app/core/`, `.env.example`, `Dockerfile` (stub)
- `apps/web/`: Next.js app via the current `create-next-app` (TypeScript, App Router, Tailwind, ESLint, `src/`), pnpm
- `data/{raw,interim,processed,reference,fixtures}/` with `.gitkeep`

## Specification
- `make setup` installs everything (`uv sync` for both Python packages, `pnpm install`). `make dev-api`, `make dev-web`, `make lint` (ruff, mypy, web lint and typecheck), `make test` (pytest, vitest), `make pipeline` (runs all stages once they exist).
- `config.yaml` holds every parameter in PRODUCT_BRIEF section 5 with the defaults (confidence filter, eps_s 2700, eps_t_hours 24, min_pts 2, h3 resolutions [5,6,7], min_mean_monthly_modis 3, month-pool width 1, percentiles [50,90,95], season share 0.7, cv method).
- `common/manifest.py`: write and read `manifest.json` per DB_SCHEMA.md.
- CI runs on pull requests: ruff, mypy, pytest, web typecheck, lint, vitest.
- Add the lint rule that blocks deep cross-feature imports in the web app (only `@/features/<name>` allowed).

## Tasks
- [x] Skeleton committed; `make setup` works on a clean clone
- [x] `make lint` and `make test` pass on the empty skeleton (include one trivial test per package)
- [x] CI green on a pull request
- [x] `config.yaml` loaded by a typed config object with a test (missing key fails)
- [x] Master plan row S00 set to `[x]`
