"""DuckDB repository for yearly stats and anomalies."""

from __future__ import annotations

import duckdb

from app.features.stats.schemas import AnomalyItem, YearlyStatRow


def fetch_yearly_stats(
    cursor: duckdb.DuckDBPyConnection,
    region_id: str,
) -> list[YearlyStatRow]:
    """Fetch yearly burn statistics for a region."""
    rows = cursor.execute(
        """
        SELECT
            CAST(year AS INTEGER) AS y,
            CAST(harmonized_total AS DOUBLE) AS ht,
            CAST(frp_sum AS DOUBLE) AS frp,
            CAST(rank AS INTEGER) AS rk,
            CAST(vs_mean_pct AS DOUBLE) AS vmp,
            CAST(peak_month AS INTEGER) AS pm
        FROM yearly
        WHERE region_id = ?
        ORDER BY y
        """,
        [region_id],
    ).fetchall()

    return [
        YearlyStatRow(
            year=int(y),
            harmonized_total=round(float(ht), 4),
            frp_sum=round(float(frp), 4),
            rank=int(rk),
            vs_mean_pct=round(float(vmp), 4),
            peak_month=int(pm),
        )
        for y, ht, frp, rk, vmp, pm in rows
    ]


def fetch_anomalies(
    cursor: duckdb.DuckDBPyConnection,
    region_id: str,
    year: int | None = None,
    class_filter: str | None = None,
) -> list[AnomalyItem]:
    """Fetch anomalies for a region with optional year and class filters."""
    where_clauses = ["region_id = ?"]
    params: list[object] = [region_id]

    if year is not None:
        where_clauses.append("CAST(year AS INTEGER) = ?")
        params.append(year)
    if class_filter is not None:
        where_clauses.append("class = ?")
        params.append(class_filter)

    where_sql = " AND ".join(where_clauses)
    sql = f"""
        SELECT
            CAST(year AS INTEGER) AS y,
            CAST(month AS INTEGER) AS m,
            CAST(value AS DOUBLE) AS v,
            CAST(percentile_rank AS DOUBLE) AS pr,
            class
        FROM anomalies
        WHERE {where_sql}
        ORDER BY y, m
    """
    rows = cursor.execute(sql, params).fetchall()

    return [
        AnomalyItem(
            year=int(y),
            month=int(m),
            value=round(float(v), 4),
            percentile_rank=round(float(pr), 4),
            class_=str(cls),  # type: ignore[arg-type]
        )
        for y, m, v, pr, cls in rows
    ]
