"""DuckDB repository for `/api/series` monthly queries."""

from __future__ import annotations

import math

import duckdb


def _clean_nullable_float(val: object) -> float | None:
    if val is None:
        return None
    f = float(val)  # type: ignore[arg-type]
    if math.isnan(f):
        return None
    return round(f, 6)


def fetch_region_series(
    cursor: duckdb.DuckDBPyConnection,
    region_ids: tuple[str, ...],
    ym_from: int | None = None,
    ym_to: int | None = None,
) -> list[tuple[int, int, float | None, float | None, float, bool, str]]:
    """Query `harmonized_region` for one or more `region_ids`, summing if multiple."""
    if not region_ids:
        return []

    placeholders = ", ".join("?" for _ in region_ids)
    params: list[object] = list(region_ids)
    where_clauses = [f"region_id IN ({placeholders})"]

    if ym_from is not None:
        where_clauses.append("(CAST(year AS INTEGER) * 100 + month) >= ?")
        params.append(ym_from)
    if ym_to is not None:
        where_clauses.append("(CAST(year AS INTEGER) * 100 + month) <= ?")
        params.append(ym_to)

    where_sql = " AND ".join(where_clauses)
    sql = f"""
        SELECT
            CAST(year AS INTEGER) AS y,
            CAST(month AS INTEGER) AS m,
            SUM(CASE WHEN raw_modis IS NOT NULL AND NOT isnan(raw_modis) THEN raw_modis ELSE 0.0 END) AS modis_sum,
            COUNT(CASE WHEN raw_modis IS NOT NULL AND NOT isnan(raw_modis) THEN 1 END) AS modis_cnt,
            SUM(CASE WHEN raw_viirs IS NOT NULL AND NOT isnan(raw_viirs) THEN raw_viirs ELSE 0.0 END) AS viirs_sum,
            COUNT(CASE WHEN raw_viirs IS NOT NULL AND NOT isnan(raw_viirs) THEN 1 END) AS viirs_cnt,
            CAST(SUM(harmonized) AS DOUBLE) AS harm_sum,
            BOOL_OR(in_overlap) AS in_ov,
            MAX(source_used) AS src
        FROM harmonized_region
        WHERE {where_sql}
        GROUP BY y, m
        ORDER BY y, m
    """
    rows = cursor.execute(sql, params).fetchall()
    result: list[tuple[int, int, float | None, float | None, float, bool, str]] = []
    for y, m, modis_sum, modis_cnt, viirs_sum, viirs_cnt, harm_sum, in_ov, src in rows:
        rm = round(float(modis_sum), 6) if int(modis_cnt) > 0 else None
        rv = round(float(viirs_sum), 6) if int(viirs_cnt) > 0 else None
        result.append(
            (
                int(y),
                int(m),
                rm,
                rv,
                round(float(harm_sum), 6),
                bool(in_ov),
                str(src),
            )
        )
    return result


def fetch_bbox_series(
    cursor: duckdb.DuckDBPyConnection,
    registered_views: tuple[str, ...],
    bbox: tuple[float, float, float, float],
    ym_from: int | None = None,
    ym_to: int | None = None,
) -> list[tuple[int, int, float | None, float | None, float, bool, str]]:
    """Aggregate monthly series over H3 cells whose centroid lies inside `bbox`."""
    west, south, east, north = bbox
    params: list[object] = [west, east, south, north]
    time_clauses: list[str] = []
    if ym_from is not None:
        time_clauses.append("(CAST(hc.year AS INTEGER) * 100 + hc.month) >= ?")
        params.append(ym_from)
    if ym_to is not None:
        time_clauses.append("(CAST(hc.year AS INTEGER) * 100 + hc.month) <= ?")
        params.append(ym_to)
    time_sql = (" AND " + " AND ".join(time_clauses)) if time_clauses else ""

    if "monthly_cell" in registered_views:
        sql = f"""
            WITH bbox_cells AS (
                SELECT h3_r7 FROM cell_centroids
                WHERE lon BETWEEN ? AND ? AND lat BETWEEN ? AND ?
            ),
            harm AS (
                SELECT
                    CAST(hc.year AS INTEGER) AS y,
                    CAST(hc.month AS INTEGER) AS m,
                    CAST(SUM(hc.harmonized) AS DOUBLE) AS harm_sum,
                    MAX(hc.source_used) AS src
                FROM harmonized_cell hc
                JOIN bbox_cells bc ON hc.h3_r7 = bc.h3_r7
                WHERE 1=1 {time_sql}
                GROUP BY y, m
            ),
            raw_m AS (
                SELECT
                    CAST(mc.year AS INTEGER) AS y,
                    CAST(mc.month AS INTEGER) AS m,
                    SUM(CASE WHEN mc.sensor_family = 'MODIS' THEN mc.event_count ELSE 0 END) AS modis_sum,
                    SUM(CASE WHEN mc.sensor_family = 'VIIRS' THEN mc.event_count ELSE 0 END) AS viirs_sum
                FROM monthly_cell mc
                JOIN bbox_cells bc ON mc.h3_r7 = bc.h3_r7
                GROUP BY y, m
            )
            SELECT
                harm.y,
                harm.m,
                CAST(COALESCE(raw_m.modis_sum, 0.0) AS DOUBLE) AS modis_val,
                CASE
                    WHEN (harm.y * 100 + harm.m) >= 201202
                    THEN CAST(COALESCE(raw_m.viirs_sum, 0.0) AS DOUBLE)
                    ELSE NULL
                END AS viirs_val,
                harm.harm_sum,
                (harm.y * 100 + harm.m) >= 201202 AS in_ov,
                harm.src
            FROM harm
            LEFT JOIN raw_m ON harm.y = raw_m.y AND harm.m = raw_m.m
            ORDER BY harm.y, harm.m
        """
    else:
        sql = f"""
            SELECT
                CAST(hc.year AS INTEGER) AS y,
                CAST(hc.month AS INTEGER) AS m,
                CAST(
                    SUM(
                        CASE
                            WHEN hr.harmonized > 0 AND hr.raw_modis IS NOT NULL AND NOT isnan(hr.raw_modis)
                            THEN hc.harmonized * (hr.raw_modis / hr.harmonized)
                            ELSE 0.0
                        END
                    ) AS DOUBLE
                ) AS modis_val,
                CASE
                    WHEN BOOL_OR(hr.in_overlap)
                    THEN CAST(
                        SUM(
                            CASE
                                WHEN hr.harmonized > 0 AND hr.raw_viirs IS NOT NULL AND NOT isnan(hr.raw_viirs)
                                THEN hc.harmonized * (hr.raw_viirs / hr.harmonized)
                                ELSE 0.0
                            END
                        ) AS DOUBLE
                    )
                    ELSE NULL
                END AS viirs_val,
                CAST(SUM(hc.harmonized) AS DOUBLE) AS harm_sum,
                BOOL_OR(hr.in_overlap) AS in_ov,
                MAX(hc.source_used) AS src
            FROM harmonized_cell hc
            JOIN cell_centroids cc ON hc.h3_r7 = cc.h3_r7
            JOIN harmonized_region hr
              ON hc.district_id = hr.region_id
             AND hc.year = hr.year
             AND hc.month = hr.month
            WHERE cc.lon BETWEEN ? AND ?
              AND cc.lat BETWEEN ? AND ?
              {time_sql}
            GROUP BY y, m
            ORDER BY y, m
        """

    rows = cursor.execute(sql, params).fetchall()
    result: list[tuple[int, int, float | None, float | None, float, bool, str]] = []
    for y, m, modis_val, viirs_val, harm_sum, in_ov, src in rows:
        result.append(
            (
                int(y),
                int(m),
                _clean_nullable_float(modis_val),
                _clean_nullable_float(viirs_val),
                round(float(harm_sum), 6),
                bool(in_ov),
                str(src),
            )
        )
    return result
