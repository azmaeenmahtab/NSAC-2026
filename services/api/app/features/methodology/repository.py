"""DuckDB repository for methodology and jump metrics."""

from __future__ import annotations

from typing import Any

import duckdb

from app.features.methodology.schemas import JumpMetrics


def compute_jump_metrics(
    cursor: duckdb.DuckDBPyConnection,
    region_id: str = "BGD",
) -> JumpMetrics:
    """Compute naive and harmonized jump metrics from harmonized_region.

    naive_ratio = mean annual naive splice (2012-2016) / mean annual raw MODIS (2007-2011)
    harmonized_ratio = mean annual harmonized (2012-2016) / mean annual harmonized (2007-2011)
    """
    row_pre = cursor.execute(
        """
        SELECT
            AVG(annual_modis) AS avg_modis_pre,
            AVG(annual_harm) AS avg_harm_pre
        FROM (
            SELECT
                year,
                SUM(raw_modis) AS annual_modis,
                SUM(harmonized) AS annual_harm
            FROM harmonized_region
            WHERE region_id = ?
              AND CAST(year AS INTEGER) BETWEEN 2007 AND 2011
            GROUP BY year
        )
        """,
        [region_id],
    ).fetchone()

    row_post = cursor.execute(
        """
        SELECT
            AVG(annual_viirs) AS avg_viirs_post,
            AVG(annual_harm) AS avg_harm_post
        FROM (
            SELECT
                year,
                SUM(CASE WHEN in_overlap THEN raw_viirs ELSE raw_modis END) AS annual_viirs,
                SUM(harmonized) AS annual_harm
            FROM harmonized_region
            WHERE region_id = ?
              AND CAST(year AS INTEGER) BETWEEN 2012 AND 2016
            GROUP BY year
        )
        """,
        [region_id],
    ).fetchone()

    avg_modis_pre = float(row_pre[0]) if row_pre and row_pre[0] is not None else 1.0
    avg_harm_pre = float(row_pre[1]) if row_pre and row_pre[1] is not None else 1.0

    avg_viirs_post = float(row_post[0]) if row_post and row_post[0] is not None else 1.0
    avg_harm_post = float(row_post[1]) if row_post and row_post[1] is not None else 1.0

    naive_r = (avg_viirs_post / avg_modis_pre) if avg_modis_pre > 0 else 1.0
    harm_r = (avg_harm_post / avg_harm_pre) if avg_harm_pre > 0 else 1.0

    return JumpMetrics(
        naive_ratio=round(naive_r, 4),
        harmonized_ratio=round(harm_r, 4),
        overlap_cv_rmse=0.0,
        overlap_cv_bias=0.0,
    )


def fetch_calibration_summary(
    cursor: duckdb.DuckDBPyConnection,
    registered_views: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Fetch calibration report summary if available."""
    if "calibration_report" not in registered_views:
        return []

    rows = cursor.execute(
        """
        SELECT
            calibration_unit_id,
            method_chosen,
            cv_rmse_qm,
            cv_rmse_ratio,
            fallback_to_parent
        FROM calibration_report
        ORDER BY calibration_unit_id
        """
    ).fetchall()

    return [
        {
            "calibration_unit_id": str(r[0]),
            "method_chosen": str(r[1]),
            "cv_rmse_qm": float(r[2]) if r[2] is not None else None,
            "cv_rmse_ratio": float(r[3]) if r[3] is not None else None,
            "fallback_to_parent": bool(r[4]) if r[4] is not None else False,
        }
        for r in rows
    ]
