# Technical Spike Results (Chunk P04)

**Author**: @Aragon  
**Date**: 2026-11-11  
**Chunk**: `P04` (`docs/plan/pre/P04-tech-spikes.md`)  
**Code Locations**:
- Spike A: `spikes/spike_a_deckgl_h3/` (`h3-hex-map.tsx`, `run_benchmark.py`, `package.json`, `tsconfig.json`)
- Spike B: `spikes/spike_b_duckdb_parquet/run_spike.py`
- Spike C: `spikes/spike_c_llm_tools/run_spike.py`

---

## 1. Spike A: deck.gl H3 Hex Map (`spikes/spike_a_deckgl_h3/`)

### Verified Package Names and Versions
Tested with React `19.3.0`, Next.js `16.4.5` (App Router), and TypeScript `5.9.3` (`strict: true`):

| Package | Verified Version | Purpose |
| :--- | :--- | :--- |
| `@deck.gl/core` | `9.4.1` | Core deck.gl types (`PickingInfo`) and lifecycle |
| `@deck.gl/layers` | `9.4.1` | Base layers peer dependency for `@deck.gl/geo-layers` |
| `@deck.gl/geo-layers` | `9.4.1` | `H3HexagonLayer` for H3 hexagon rendering |
| `@deck.gl/mapbox` | `9.4.1` | `MapboxOverlay` and `MapboxOverlayProps` (implements MapLibre `IControl`) |
| `react-map-gl` | `8.1.3` | React wrapper; import from subpath `react-map-gl/maplibre` |
| `maplibre-gl` | `5.24.0` (`^5.3.0`) | Open-source WebGL2 vector map engine |
| `h3-js` | `4.5.0` | Client-side H3 geometry required by `H3HexagonLayer` |
| `d3-scale-chromatic` | `3.1.1` | `interpolateInferno` perceptual color ramp |
| `d3-color` | `3.1.1` | `rgb()` parser converting CSS color strings to `[r, g, b, a]` tuples |

### Measured Performance (30,000 Bangladesh H3 Resolution-7 Cells)
Measured via `spikes/spike_a_deckgl_h3/run_benchmark.py` in headless Chrome `157.0.0.0` (`1280x800` WebGL viewport) over `30,000` contiguous resolution-7 cells centered on Bangladesh (`23.685°N, 90.3563°E`):

| Metric | Measured Value | Target (`ARCHITECTURE.md` / `F02`) | Status |
| :--- | :---: | :---: | :---: |
| **Cell count rendered** | `30,000` (r7) | Up to `30,000` cells | Pass |
| **First render time (cold mount -> WebGL frame)** | **`355 ms`** | Fast initial load | Pass |
| **Pan + zoom frame rate (3D extruded, `extruded: true`)** | **`34.1 FPS`** | `>= 30 FPS` | Pass |
| **Pan + zoom frame rate (2D flat, `extruded: false`)** | **`89.3 FPS`** (uncapped; `60 FPS` vsync) | `>= 30 FPS` | Pass |
| **JS Heap Memory (`usedJSHeapSize`)** | **`86.3 MB`** | Bounded laptop memory | Pass |

### Free Keyless Basemap Styles, Attribution, and Terms
Verified live via HTTP `GET` (no API key required):
1. **Primary Dark Style (recommended for `NEXT_PUBLIC_BASEMAP_STYLE_URL`)**:
   - **URL**: `https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json` (HTTP 200, 67 KB)
   - **Required Attribution**: `© OpenStreetMap contributors, © CARTO`
   - **Terms**: Free for non-commercial / hackathon demo use with visible CARTO + OpenStreetMap attribution.
2. **Fallback Keyless Dark Style (OpenFreeMap)**:
   - **URL**: `https://tiles.openfreemap.org/styles/dark` (HTTP 200, 21 KB)
   - **Required Attribution**: `OpenFreeMap © OpenMapTiles Data from OpenStreetMap`
   - **Terms**: Completely free public instance with no API key and no request caps; mandatory OpenMapTiles + OpenStreetMap credit.

### Working Next.js App Router Snippet
In Next.js App Router (`apps/web/src/features/map/`), import the map component with `next/dynamic(..., { ssr: false })` and bridge `react-map-gl/maplibre` to `@deck.gl/mapbox` via `useControl`:

```tsx
"use client";

import React, { useMemo, useState } from "react";
import { Map, NavigationControl, useControl } from "react-map-gl/maplibre";
import { MapboxOverlay, type MapboxOverlayProps } from "@deck.gl/mapbox";
import { H3HexagonLayer } from "@deck.gl/geo-layers";
import type { PickingInfo } from "@deck.gl/core";
import { interpolateInferno } from "d3-scale-chromatic";
import { rgb } from "d3-color";
import "maplibre-gl/dist/maplibre-gl.css";

export interface HexCellDatum {
  h3: string;
  value: number;
}

function DeckGLOverlay(props: MapboxOverlayProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

export function infernoRgba(value: number, p95: number): [number, number, number, number] {
  const t = Math.max(0, Math.min(1, value / Math.max(1e-6, p95)));
  const c = rgb(interpolateInferno(t));
  return [c.r, c.g, c.b, 215];
}
```

### Pitfalls Discovered & Mitigations
1. **TypeScript `interleaved` prop typing**: `@deck.gl/core`'s `DeckProps` does **not** declare `interleaved?: boolean`. Always type the `useControl` wrapper parameter with `MapboxOverlayProps` from `@deck.gl/mapbox`.
2. **`maplibre-gl` v5 vs v6**: `maplibre-gl` `^5.24.0` works out-of-the-box with `react-map-gl@8.1.3` and Next.js bundler without custom Web Worker loader configuration, whereas `maplibre-gl@6.x` changes default export semantics and requires explicit bundler worker configuration. Pin `maplibre-gl` to `^5.24.0`.
3. **`updateTriggers` required for selection & extrusion**: `H3HexagonLayer` caches attribute buffers; changing `selectedH3` or `extruded` will not re-run `getLineColor` or `getElevation` unless listed in `updateTriggers: { getLineColor: [selectedH3], getElevation: [extruded] }`.
4. **3D Extrusion Stroke Overhead**: Rendering wireframe/strokes on all 30,000 3D prisms reduces FPS; disable strokes (`stroked: false`) in 3D mode or only stroke when `extruded === false` / for the selected cell.

---

## 2. Spike B: DuckDB over 2M-Row Parquet (`spikes/spike_b_duckdb_parquet/run_spike.py`)

### Verified Versions
- `duckdb`: `2.0.0`
- `pyarrow`: `26.0.1`
- `pandas`: `3.1.1`
- `h3`: `4.5.0` (Python `h3-py` v4 API: `latlng_to_cell`, `cell_to_latlng`, `cell_to_parent`, `grid_disk`, `is_valid_cell`)

### Measured Timings (2,000,000 Rows, 30,000 Bangladesh r7 Cells)
Executed via `uv run python spikes/spike_b_duckdb_parquet/run_spike.py`:

| Operation | Measured Value | Target (`ARCHITECTURE.md` / `A02`) |
| :--- | :---: | :---: |
| **Precompute 30,000 r7 cells + r6/r5 parents + centroids in Python** | **`67.2 ms`** | One-time startup / reference build |
| **Write 2,000,000-row ZSTD Parquet (`monthly_cell_2m.parquet`)** | **`536.9 ms`** (`27.67 MB`) | Compact on-disk storage |
| **Cold query (new DuckDB connection + bbox join + `GROUP BY h3_r7` + hex formatting, 13,445 cells)** | **`119.6 ms`** | `< 500 ms` |
| **Warm query + `min`/`max`/`p95` (`quantile_cont`) + hex formatting + `json.dumps` (13,445 cells)** | **Median `75.0 ms`, p95 `81.8 ms`** | **p95 `< 500 ms`** |

### `UINT64` Handling & Architecture Decisions
1. **End-to-End `UINT64` Pipeline**:
   - **Python / Pandas**: `np.uint64(int(h3_hex, 16))` (`dtype='uint64'`).
   - **Parquet (PyArrow)**: Stored natively as unsigned 64-bit integer (`pa.uint64()`).
   - **DuckDB**: Reads Parquet `uint64` columns natively as `UBIGINT`.
   - **API / Python -> JSON**: Fetch rows with `.fetchall()` (which returns exact Python `int` values) and convert via `format(int(h), "x")`. Every Bangladesh r7 cell produces a 15-character lowercase hex string (e.g. `873c1b000ffffff`).
2. **Why JSON Numbers / `float64` Must Never Be Used**:
   - A Bangladesh r7 H3 index is `~6.09 × 10^17` (`609043336300331007`), which exceeds `Number.MAX_SAFE_INTEGER` (`2^53 - 1 = 9,007,199,254,740,991`).
   - Empirically verified in `run_spike.py`: casting `609043336300331007` (`873c1b000ffffff`) through IEEE-754 `float64` rounds it to `609043336300331008` (`873c1b001000000`), which fails `h3.is_valid_cell(...) == False`.
3. **Decision on DuckDB `h3` Community Extension**:
   - **Do NOT use the DuckDB `h3` extension.** Computing centroids for all ~30,000 Bangladesh r7 cells in Python with `h3.cell_to_latlng` takes only `67 ms` and joining a 30,000-row `cell_lookup` table in DuckDB runs in `75 ms` warm. Avoiding the community extension eliminates runtime network/extension-signing failure modes in CI and Docker.
4. **Critical SQL Pitfall Discovered (`INT16` Overflow in Date Range Filter)**:
   - In `docs/DB_SCHEMA.md`, `year` has type `INT16` (max `32,767`).
   - Writing `(year * 100 + month) BETWEEN 202001 AND 202412` in DuckDB `2.0.0` raises `_duckdb.OutOfRangeException: Overflow in multiplication of INT16 (2002 * 100)!`.
   - **Rule for `A02` / `A03` repositories**: Always cast `year` to `INTEGER` first:
     ```sql
     WHERE (CAST(mc.year AS INTEGER) * 100 + mc.month) BETWEEN ? AND ?
     ```

---

## 3. Spike C: LLM Function Calling & Replay Mode (`spikes/spike_c_llm_tools/run_spike.py`)

### Verified SDK, Model ID, and Free-Tier Limits
- **SDK**: `google-genai` (`>=2.30.1`, latest verified on PyPI: `3.1.0`). Do **not** use the deprecated `google-generativeai` package.
- **API Surface**: Gemini **Interactions API** (`client.interactions.create`), which is Generally Available and replaces legacy `generate_content` in `google-genai >= 2.30.1`.
- **Verified Model ID (`LLM_MODEL`)**:
  - Primary for `/api/ask`: **`gemini-3.8-flash`** (1M context window, fast agentic tool calling).
  - High-throughput fallback: **`gemini-3.5-flash-lite`**.
  - Frontier reasoning: **`gemini-4-argon`** or **`gemini-4-carbon`**.
  - *Note*: Legacy models `gemini-1.5-pro`, `gemini-1.5-flash`, `gemini-2.0-flash`, and `gemini-2.5-flash` are deprecated and must not be used.
- **Free-Tier Quotas**:
  - Flash models (`gemini-3.8-flash` / `gemini-3.5-flash-lite`): ~10–15 RPM, ~500–1,500 RPD, 250,000 TPM per Google Cloud project (resets midnight PT).
  - Exceeding any quota returns HTTP `429 Resource Exhausted`. Our `/api/ask` rate limit (10 RPM/IP) and automatic fallback to `replay` mode (`LLM_PROVIDER=replay`) protect the live demo from quota exhaustion.
- **Timeout & Thread-Safety**:
  - Configure client timeout via `types.HttpOptions(timeout=20_000)` (milliseconds = 20 seconds, matching `A05`'s 20-second turn limit).
  - `genai.Client` uses `httpx` internally and is thread-safe across requests; create one shared client at startup or use `client.aio` in async routes.
  - Note that `temperature`, `top_p`, and `top_k` are deprecated on Gemini 3.8 / 4 models; omit them or use `thinking_level`.

### Working SDK Snippet (`spikes/spike_c_llm_tools/run_spike.py`)
```python
from google import genai
from google.genai import types

GET_VALUE_DECLARATION = {
    "type": "function",
    "name": "get_value",
    "description": "Return harmonized MODIS-equivalent fire event count and peak season for an area.",
    "parameters": {
        "type": "object",
        "properties": {
            "area": {
                "type": "string",
                "description": "Region ID such as PRESET-CHT or BGD",
            }
        },
        "required": ["area"],
    },
}

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(timeout=20_000),  # 20s timeout in ms
)

interaction = client.interactions.create(
    model=os.environ.get("LLM_MODEL", "gemini-3.8-flash"),
    system_instruction=SYSTEM_INSTRUCTION,
    input=question,
    tools=[GET_VALUE_DECLARATION],
)

function_results = []
for step in interaction.steps:
    if getattr(step, "type", None) == "function_call" and step.name == "get_value":
        res = get_value(str(step.arguments.get("area", "PRESET-CHT")))
        function_results.append(
            {
                "type": "function_result",
                "name": step.name,
                "call_id": step.id,
                "result": [{"type": "text", "text": json.dumps(res)}],
            }
        )

final_turn = client.interactions.create(
    model=os.environ.get("LLM_MODEL", "gemini-3.8-flash"),
    system_instruction=SYSTEM_INSTRUCTION,
    input=function_results,
    tools=[GET_VALUE_DECLARATION],
    previous_interaction_id=interaction.id,
)
answer = final_turn.output_text
```

---

## 4. Official Documentation Pages Read & Verified
- **deck.gl `H3HexagonLayer`**: https://deck.gl/docs/api-reference/geo-layers/h3-hexagon-layer (`https://raw.githubusercontent.com/visgl/deck.gl/master/docs/api-reference/geo-layers/h3-hexagon-layer.md`)
- **deck.gl `MapboxOverlay`**: https://deck.gl/docs/api-reference/mapbox/mapbox-overlay (`https://raw.githubusercontent.com/visgl/deck.gl/master/docs/api-reference/mapbox/mapbox-overlay.md`)
- **react-map-gl Get Started (MapLibre)**: https://visgl.github.io/react-map-gl/docs/get-started (`https://raw.githubusercontent.com/visgl/react-map-gl/master/docs/get-started/get-started.md`)
- **OpenFreeMap QuickStart & Attribution**: https://openfreemap.org/quick_start/
- **CARTO Basemaps Terms & Attribution**: https://carto.com/attribution/
- **DuckDB Parquet & SQL Functions (`UBIGINT`, `quantile_cont`, `printf`)**: https://duckdb.org/docs/data/parquet/overview and https://duckdb.org/docs/sql/aggregates
- **Google Gemini Interactions API & Function Calling**: https://aistudio.google.com/docs/interactions-overview.md and https://aistudio.google.com/docs/function-calling.md

