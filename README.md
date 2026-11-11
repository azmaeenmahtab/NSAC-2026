# PyroScope: Burning Activity Calendar

> **NASA Space Apps Challenge 2026** — *Harmonization of MODIS and VIIRS Hot Spots*  
> **Team:** Singularity

PyroScope harmonizes NASA MODIS (1 km, 2000–present) and VIIRS (375 m, 2012–present) active-fire records into a consistent 2000–present **Burning Activity Calendar** (FireCalendar) for early warning, land managers, and emergency response.

---

## Architecture Overview

```
apps/web/                         Next.js App Router (TypeScript, Tailwind, MapLibre, deck.gl H3)
services/api/                     FastAPI + DuckDB (queries ZSTD Parquet tables)
pipeline/                         pyroscope_pipeline (ST-DBSCAN clustering, quantile mapping harmonization)
contracts/openapi.yaml            API contract (OpenAPI 3.1)
data/                             Parquet storage (raw, interim, processed, reference, fixtures)
```

---

## Offline Judging & Local Fallback (Docker)

To run the entire system offline without installing Python or Node:

```bash
docker compose up --build
```

- **Web Application**: [http://localhost:3000](http://localhost:3000)
- **Interactive Pitch Guide**: [http://localhost:3000/?demo=1](http://localhost:3000/?demo=1) (opens CHT preset and 4-step story walk-through)
- **API Endpoints & Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Offline Assistant**: Replay mode is enabled by default (`LLM_PROVIDER=replay`), requiring no external API keys.

To run the automated deployment smoke test suite against the local instance:
```bash
# Linux / macOS
./scripts/smoke.sh http://localhost:8000

# Windows PowerShell
.\scripts\smoke.ps1 -ApiUrl http://localhost:8000
```

---

## Development & Manual Setup

### Prerequisites
- Node.js LTS & `pnpm`
- Python 3.12+ & `uv`
- `make`

### Installation
```bash
make setup
```

### Development
```bash
make dev-api     # FastAPI server on http://localhost:8000
make dev-web     # Next.js web application on http://localhost:3000
```

### Verification
```bash
make lint        # ruff, mypy, web lint & typecheck
make test        # pytest, vitest
```

---

## Production Deployment & Data Shipping

### 1. Web Deployment (Vercel)
- Root directory: `apps/web`
- Build command: `pnpm build`
- Output directory: `.next`
- Environment Variables:
  - `NEXT_PUBLIC_API_URL`: Public HTTPS URL of the deployed FastAPI service.
  - `NEXT_PUBLIC_BASEMAP_STYLE_URL`: `https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json`

### 2. API Deployment (Render / Fly.io / Railway / Cloud Run)
- Built directly from `services/api/Dockerfile` (or repository root using the multi-stage Dockerfile).
- Environment Variables:
  - `DATA_DIR`: Path to active processed Parquet version (e.g. `/workspace/data/processed/v1.0.0` or `/workspace/data/fixtures`).
  - `WEB_ORIGIN`: Allowed frontend origin (e.g. `https://pyroscope.vercel.app`).
  - `LLM_PROVIDER`: `replay` for zero-key judging fallback, or `gemini` with `GEMINI_API_KEY`.
  - `PORT`: Set automatically by container hosts (defaults to `8000`).

### 3. Data Rollback Procedure
If an updated data version requires rollback:
1. Retain the previous data directory (e.g. `data/processed/v1.0.0/`).
2. Update the `DATA_DIR` environment variable on the API host to point to the previous version directory.
3. Restart the container service (`services/api` verifies `manifest.json` on startup and reloads all DuckDB views).
4. Verify with `./scripts/smoke.sh <PROD_URL>`.

---

## License & Attribution
- Active fire data courtesy of NASA FIRMS (MODIS Collection 6.1 and VIIRS S-NPP 375 m).
- Basemap styles courtesy of MapLibre / OpenStreetMap contributors.
- Administrative boundaries courtesy of geoBoundaries (CC-BY 3.0 IGO / CC0).
