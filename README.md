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

## Quick Start

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

## License & Attribution
- Active fire data courtesy of NASA FIRMS (MODIS Collection 6.1 and VIIRS S-NPP 375 m).
- Basemap styles courtesy of MapLibre / OpenStreetMap contributors.

