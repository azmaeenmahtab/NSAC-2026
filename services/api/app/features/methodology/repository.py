"""DuckDB repository for methodology and jump metrics."""

from __future__ import annotations

from typing import Any

import duckdb
import numpy as np
import pandas as pd

from app.features.methodology.schemas import JumpMetrics, QQPoint


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

    overlap_rows = cursor.execute(
        """
        SELECT raw_modis, harmonized
        FROM harmonized_region
        WHERE region_id = ? AND in_overlap = true
          AND raw_modis IS NOT NULL AND harmonized IS NOT NULL
        """,
        [region_id],
    ).fetchall()

    if overlap_rows:
        m_arr = np.array([r[0] for r in overlap_rows], dtype=np.float64)
        h_arr = np.array([r[1] for r in overlap_rows], dtype=np.float64)
        rmse_val = float(np.sqrt(np.mean((h_arr - m_arr) ** 2)))
        bias_val = float(np.mean(h_arr - m_arr))
        rx = pd.Series(m_arr).rank(method="average").to_numpy(dtype=np.float64)
        ry = pd.Series(h_arr).rank(method="average").to_numpy(dtype=np.float64)
        if np.std(rx) == 0.0 or np.std(ry) == 0.0:
            rho_val = 1.0
        else:
            corr = float(np.corrcoef(rx, ry)[0, 1])
            rho_val = 1.0 if np.isnan(corr) else corr
    else:
        rmse_val = 0.0
        bias_val = 0.0
        rho_val = 1.0

    return JumpMetrics(
        naive_ratio=round(naive_r, 4),
        harmonized_ratio=round(harm_r, 4),
        overlap_cv_rmse=round(rmse_val, 4),
        overlap_cv_bias=round(bias_val, 4),
        rank_correlation=round(rho_val, 4),
    )


def fetch_qq_data(
    cursor: duckdb.DuckDBPyConnection,
    region_id: str = "BGD",
) -> list[QQPoint]:
    """Compute empirical quantile points for MODIS, raw VIIRS, and harmonized VIIRS in overlap."""
    rows = cursor.execute(
        """
        SELECT raw_modis, raw_viirs, harmonized
        FROM harmonized_region
        WHERE region_id = ? AND in_overlap = true
          AND raw_modis IS NOT NULL AND raw_viirs IS NOT NULL AND harmonized IS NOT NULL
        """,
        [region_id],
    ).fetchall()

    if not rows:
        return []

    modis_arr = np.array([r[0] for r in rows], dtype=np.float64)
    viirs_arr = np.array([r[1] for r in rows], dtype=np.float64)
    harm_arr = np.array([r[2] for r in rows], dtype=np.float64)

    quantiles = [0.05, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
    return [
        QQPoint(
            quantile=q,
            modis=round(float(np.percentile(modis_arr, q * 100)), 2),
            viirs_raw=round(float(np.percentile(viirs_arr, q * 100)), 2),
            viirs_harmonized=round(float(np.percentile(harm_arr, q * 100)), 2),
        )
        for q in quantiles
    ]


def fetch_calibration_summary(
    cursor: duckdb.DuckDBPyConnection,
    registered_views: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Fetch calibration report summary if available, with fallback to harmonized_region."""
    if "calibration_report" in registered_views:
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
                "unit_id": str(r[0]),
                "method_chosen": str(r[1]),
                "method": str(r[1]),
                "cv_rmse_qm": float(r[2]) if r[2] is not None else None,
                "cv_rmse_ratio": float(r[3]) if r[3] is not None else None,
                "fallback": bool(r[4]) if r[4] is not None else False,
                "fallback_to_parent": bool(r[4]) if r[4] is not None else False,
            }
            for r in rows
        ]

    unit_rows = cursor.execute(
        """
        SELECT DISTINCT calibration_unit_id, method
        FROM harmonized_region
        WHERE calibration_unit_id IS NOT NULL AND method != 'none'
        ORDER BY calibration_unit_id
        """
    ).fetchall()

    return [
        {
            "calibration_unit_id": str(u[0]),
            "unit_id": str(u[0]),
            "method_chosen": str(u[1]),
            "method": str(u[1]),
            "fallback": False,
            "fallback_to_parent": False,
        }
        for u in unit_rows
    ]
