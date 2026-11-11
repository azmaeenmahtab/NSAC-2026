"""DuckDB repository for `/api/heatmap` cell aggregations."""

from __future__ import annotations

import duckdb

from app.features.heatmap.schemas import HeatmapMetric

_RES_COLUMN_WHITELIST: dict[int, str] = {
    5: "h3_r5",
    6: "h3_r6",
    7: "h3_r7",
}


def fetch_latest_year_month(cursor: duckdb.DuckDBPyConnection) -> tuple[int, int]:
    """Return the latest `(year, month)` present in `harmonized_cell`."""
    row = cursor.execute(
        """
        SELECT year, month
        FROM harmonized_cell
        ORDER BY CAST(year AS INTEGER) * 100 + month DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return (2025, 12)
    return (int(row[0]), int(row[1]))


def query_heatmap_cells(
    cursor: duckdb.DuckDBPyConnection,
    registered_views: tuple[str, ...],
    bbox: tuple[float, float, float, float],
    ym_from: int,
    ym_to: int,
    metric: HeatmapMetric,
    res: int,
) -> list[tuple[int, float]]:
    """Aggregate H3 cells inside `bbox` and `[ym_from, ym_to]` at resolution `res`.

    Uses whitelisted column identifier `h3_r{5|6|7}` and bound parameters for all filters.
    """
    if res not in _RES_COLUMN_WHITELIST:
        raise ValueError(f"Unsupported H3 resolution: {res}")
    col = _RES_COLUMN_WHITELIST[res]
    west, south, east, north = bbox

    if metric == "harmonized":
        sql = f"""
            SELECT hc.{col} AS cell_id, CAST(SUM(hc.harmonized) AS DOUBLE) AS val
            FROM harmonized_cell hc
            JOIN cell_centroids cc ON hc.h3_r7 = cc.h3_r7
            WHERE cc.lon BETWEEN ? AND ?
              AND cc.lat BETWEEN ? AND ?
              AND (CAST(hc.year AS INTEGER) * 100 + hc.month) BETWEEN ? AND ?
            GROUP BY hc.{col}
            HAVING SUM(hc.harmonized) > 0
            ORDER BY hc.{col}
        """
        rows = cursor.execute(sql, [west, east, south, north, ym_from, ym_to]).fetchall()
        return [(int(r[0]), float(r[1])) for r in rows]

    sensor_family = "MODIS" if metric == "raw_modis" else "VIIRS"
    if "monthly_cell" in registered_views:
        sql = f"""
            SELECT mc.{col} AS cell_id, CAST(SUM(mc.event_count) AS DOUBLE) AS val
            FROM monthly_cell mc
            JOIN cell_centroids cc ON mc.h3_r7 = cc.h3_r7
            WHERE mc.sensor_family = ?
              AND cc.lon BETWEEN ? AND ?
              AND cc.lat BETWEEN ? AND ?
              AND (CAST(mc.year AS INTEGER) * 100 + mc.month) BETWEEN ? AND ?
            GROUP BY mc.{col}
            HAVING SUM(mc.event_count) > 0
            ORDER BY mc.{col}
        """
        rows = cursor.execute(
            sql,
            [sensor_family, west, east, south, north, ym_from, ym_to],
        ).fetchall()
        return [(int(r[0]), float(r[1])) for r in rows]

    # Fixture fallback when `monthly_cell.parquet` is not present:
    # Scale `harmonized_cell` by `(raw_modis / harmonized)` or `(raw_viirs / harmonized)` per district-month
    raw_col = "raw_modis" if metric == "raw_modis" else "raw_viirs"
    sql = f"""
        SELECT
            hc.{col} AS cell_id,
            CAST(
                SUM(
                    CASE
                        WHEN hr.harmonized > 0 AND hr.{raw_col} IS NOT NULL AND NOT isnan(hr.{raw_col})
                        THEN hc.harmonized * (hr.{raw_col} / hr.harmonized)
                        ELSE 0.0
                    END
                ) AS DOUBLE
            ) AS val
        FROM harmonized_cell hc
        JOIN cell_centroids cc ON hc.h3_r7 = cc.h3_r7
        JOIN harmonized_region hr
          ON hc.district_id = hr.region_id
         AND hc.year = hr.year
         AND hc.month = hr.month
        WHERE cc.lon BETWEEN ? AND ?
          AND cc.lat BETWEEN ? AND ?
          AND (CAST(hc.year AS INTEGER) * 100 + hc.month) BETWEEN ? AND ?
        GROUP BY hc.{col}
        HAVING val > 0
        ORDER BY hc.{col}
    """
    rows = cursor.execute(sql, [west, east, south, north, ym_from, ym_to]).fetchall()
    return [(int(r[0]), float(r[1])) for r in rows]
