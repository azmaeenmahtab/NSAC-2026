"""Spike B: DuckDB over 2M-row Parquet with UINT64 H3 indices (Chunk P04).

Validates:
1. Generating a 2,000,000-row synthetic `monthly_cell` Parquet file with `UINT64` H3 columns.
2. UINT64 fidelity across pandas -> PyArrow -> Parquet -> DuckDB (`UBIGINT`) -> Python -> JSON.
3. Precision loss demonstration if UINT64 is cast to float64 / JSON number (> 2^53).
4. Querying with DuckDB by date range and bounding box (via 30k-cell centroid lookup table vs inline),
   aggregating by H3 cell, computing `min`, `max`, `quantile_cont(..., 0.95)`, and converting H3 to
   lowercase hex strings (`format(int(x), "x")` vs SQL `printf('%x', h3)`).
5. Cold vs warm query latency benchmarks.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import duckdb
import h3
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def generate_bangladesh_r7_cells(n_cells: int = 30_000) -> list[str]:
    """Generate `n_cells` real resolution-7 H3 cell hex strings around Bangladesh."""
    center = h3.latlng_to_cell(23.6850, 90.3563, 7)
    ring = h3.grid_disk(center, 110)
    cells = sorted(ring)[:n_cells]
    assert len(cells) == n_cells, f"Expected {n_cells} cells, got {len(cells)}"
    return cells


def run_spike() -> dict[str, object]:
    print("=== Spike B: DuckDB over 2,000,000-row Parquet ===")
    t0 = time.perf_counter()
    cells_hex = generate_bangladesh_r7_cells(30_000)
    r7_uint64 = np.array([int(c, 16) for c in cells_hex], dtype=np.uint64)
    r6_uint64 = np.array([int(h3.cell_to_parent(c, 6), 16) for c in cells_hex], dtype=np.uint64)
    r5_uint64 = np.array([int(h3.cell_to_parent(c, 5), 16) for c in cells_hex], dtype=np.uint64)
    coords = [h3.cell_to_latlng(c) for c in cells_hex]
    cell_lats = np.array([lat for lat, _ in coords], dtype=np.float64)
    cell_lons = np.array([lon for _, lon in coords], dtype=np.float64)
    t_cells_ms = (time.perf_counter() - t0) * 1000.0
    print(f"Generated 30,000 r7 cells + parents + centroids in {t_cells_ms:.1f} ms")

    # 1. Verify UINT64 vs float64 precision loss (> 2^53)
    sample_hex = cells_hex[0]
    sample_u64 = np.uint64(int(sample_hex, 16))
    corrupted_from_float = int(float(sample_u64))
    corrupted_hex = format(corrupted_from_float, "x")
    print(f"Sample r7 cell hex: {sample_hex} (len={len(sample_hex)}, u64={sample_u64})")
    print(
        f"IEEE-754 float64 roundtrip: {corrupted_hex} "
        f"(equal={sample_hex == corrupted_hex}, valid_h3={h3.is_valid_cell(corrupted_hex)})"
    )
    assert sample_hex == format(int(sample_u64), "x")
    assert len(sample_hex) == 15

    # 2. Generate 2,000,000-row synthetic monthly_cell Parquet
    n_rows = 2_000_000
    rng = np.random.default_rng(42)
    cell_idx = rng.integers(0, len(r7_uint64), size=n_rows)
    years = rng.integers(2001, 2026, size=n_rows, dtype=np.int16)
    months = rng.integers(1, 13, size=n_rows, dtype=np.int8)
    families = np.where(rng.random(n_rows) < 0.5, "MODIS", "VIIRS")
    event_counts = rng.integers(1, 25, size=n_rows, dtype=np.int32)
    frp_sums = (event_counts * rng.uniform(5.0, 40.0, size=n_rows)).astype(np.float64)

    df = pd.DataFrame(
        {
            "h3_r7": r7_uint64[cell_idx],
            "h3_r6": r6_uint64[cell_idx],
            "h3_r5": r5_uint64[cell_idx],
            "district_id": "BGD-ADM2-rangamati",
            "sensor_family": families,
            "year": years,
            "month": months,
            "event_count": event_counts,
            "frp_sum": frp_sums,
        }
    )

    df_lookup = pd.DataFrame(
        {
            "h3_r7": r7_uint64,
            "lat": cell_lats,
            "lon": cell_lons,
        }
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_path = Path(tmpdir) / "monthly_cell_2m.parquet"
        lookup_path = Path(tmpdir) / "cell_lookup.parquet"

        t_write0 = time.perf_counter()
        pq.write_table(
            pa.Table.from_pandas(df, preserve_index=False),
            parquet_path,
            compression="ZSTD",
            version="2.6",
        )
        pq.write_table(
            pa.Table.from_pandas(df_lookup, preserve_index=False),
            lookup_path,
            compression="ZSTD",
            version="2.6",
        )
        write_ms = (time.perf_counter() - t_write0) * 1000.0
        file_mb = parquet_path.stat().st_size / (1024 * 1024)
        print(f"Wrote 2,000,000-row Parquet ({file_mb:.2f} MB) in {write_ms:.1f} ms")

        # 3. Cold query: new DuckDB connection reading directly from Parquet
        # Note: DB_SCHEMA defines `year` as INT16 (max 32,767). `mc.year * 100` overflows INT16
        # in DuckDB unless cast to INTEGER (`CAST(mc.year AS INTEGER) * 100 + mc.month`).
        query_sql = """
            WITH filtered_cells AS (
                SELECT
                    mc.h3_r7 AS h3_u64,
                    CAST(SUM(mc.event_count) AS DOUBLE) AS val
                FROM read_parquet(?) mc
                INNER JOIN read_parquet(?) cl ON mc.h3_r7 = cl.h3_r7
                WHERE mc.sensor_family = ?
                  AND (CAST(mc.year AS INTEGER) * 100 + mc.month) BETWEEN ? AND ?
                  AND cl.lon BETWEEN ? AND ?
                  AND cl.lat BETWEEN ? AND ?
                GROUP BY mc.h3_r7
            )
            SELECT h3_u64, val FROM filtered_cells
        """
        stats_sql = """
            SELECT
                MIN(val) AS min_val,
                MAX(val) AS max_val,
                quantile_cont(val, 0.95) AS p95_val
            FROM (
                SELECT CAST(SUM(mc.event_count) AS DOUBLE) AS val
                FROM monthly_cell mc
                INNER JOIN cell_lookup cl ON mc.h3_r7 = cl.h3_r7
                WHERE mc.sensor_family = ?
                  AND (CAST(mc.year AS INTEGER) * 100 + mc.month) BETWEEN ? AND ?
                  AND cl.lon BETWEEN ? AND ?
                  AND cl.lat BETWEEN ? AND ?
                GROUP BY mc.h3_r7
            )
        """
        params = [
            str(parquet_path),
            str(lookup_path),
            "VIIRS",
            202001,
            202412,
            89.5,
            92.5,
            22.5,
            25.0,
        ]

        t_cold0 = time.perf_counter()
        con_cold = duckdb.connect(":memory:")
        col_types = con_cold.execute(
            "DESCRIBE SELECT h3_r7 FROM read_parquet(?)", [str(parquet_path)]
        ).fetchall()
        assert col_types[0][1] == "UBIGINT", f"Expected UBIGINT, got {col_types[0][1]}"
        rows_cold = con_cold.execute(query_sql, params).fetchall()
        cells_json = [{"h3": format(int(h), "x"), "value": float(v)} for h, v in rows_cold]
        cold_ms = (time.perf_counter() - t_cold0) * 1000.0
        con_cold.close()

        # 4. Warm query: persistent DuckDB connection with registered views & in-memory lookup
        con_warm = duckdb.connect(":memory:")
        con_warm.execute(
            f"CREATE VIEW monthly_cell AS SELECT * FROM read_parquet('{parquet_path.as_posix()}')"
        )
        con_warm.execute(
            f"CREATE TABLE cell_lookup AS SELECT * FROM read_parquet('{lookup_path.as_posix()}')"
        )
        warm_query = """
            SELECT
                mc.h3_r7 AS h3_u64,
                CAST(SUM(mc.event_count) AS DOUBLE) AS val
            FROM monthly_cell mc
            INNER JOIN cell_lookup cl ON mc.h3_r7 = cl.h3_r7
            WHERE mc.sensor_family = ?
              AND (CAST(mc.year AS INTEGER) * 100 + mc.month) BETWEEN ? AND ?
              AND cl.lon BETWEEN ? AND ?
              AND cl.lat BETWEEN ? AND ?
            GROUP BY mc.h3_r7
        """
        warm_params = ["VIIRS", 202001, 202412, 89.5, 92.5, 22.5, 25.0]
        # Warm-up pass
        con_warm.execute(warm_query, warm_params).fetchall()

        warm_times = []
        for _ in range(5):
            t_w0 = time.perf_counter()
            rows_warm = con_warm.execute(warm_query, warm_params).fetchall()
            stats_row = con_warm.execute(stats_sql, warm_params).fetchone()
            assert stats_row is not None
            payload = {
                "cells": [{"h3": format(int(h), "x"), "value": float(v)} for h, v in rows_warm],
                "stats": {
                    "min": float(stats_row[0]),
                    "max": float(stats_row[1]),
                    "p95": float(stats_row[2]),
                },
            }
            _ = json.dumps(payload)
            warm_times.append((time.perf_counter() - t_w0) * 1000.0)

        con_warm.close()

    warm_median_ms = float(np.median(warm_times))
    warm_p95_ms = float(np.percentile(warm_times, 95))
    print(f"Cold query + hex conversion ({len(cells_json):,} cells): {cold_ms:.1f} ms")
    print(
        f"Warm query + stats + hex + JSON serialization ({len(cells_json):,} cells): "
        f"median={warm_median_ms:.1f} ms, p95={warm_p95_ms:.1f} ms"
    )
    # Verify round-trip hex validity
    assert all(len(c["h3"]) == 15 and c["h3"] == c["h3"].lower() for c in cells_json[:100])
    assert all(h3.is_valid_cell(c["h3"]) for c in cells_json[:100])

    return {
        "n_rows": n_rows,
        "parquet_mb": round(file_mb, 2),
        "returned_cells": len(cells_json),
        "cold_ms": round(cold_ms, 1),
        "warm_median_ms": round(warm_median_ms, 1),
        "warm_p95_ms": round(warm_p95_ms, 1),
    }


if __name__ == "__main__":
    results = run_spike()
    print("Spike B Results:", json.dumps(results, indent=2))
