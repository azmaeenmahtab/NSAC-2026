"""DuckDB repository for `/api/calendar` data access."""

from __future__ import annotations

import duckdb

from app.features.calendar.schemas import CalendarCell, FireSeason, MonthClimatology


def fetch_calendar_grid(
    cursor: duckdb.DuckDBPyConnection,
    region_id: str,
    provisional_ym: int | None = None,
) -> tuple[list[int], list[CalendarCell]]:
    """Fetch calendar monthly anomaly cells for a region."""
    rows = cursor.execute(
        """
        SELECT
            CAST(year AS INTEGER) AS y,
            CAST(month AS INTEGER) AS m,
            CAST(value AS DOUBLE) AS v,
            CAST(percentile_rank AS DOUBLE) AS pr,
            class
        FROM anomalies
        WHERE region_id = ?
        ORDER BY y, m
        """,
        [region_id],
    ).fetchall()

    years_set: set[int] = set()
    cells: list[CalendarCell] = []
    for y, m, v, pr, cls in rows:
        years_set.add(int(y))
        is_prov = provisional_ym is not None and (int(y) * 100 + int(m)) >= provisional_ym
        cells.append(
            CalendarCell(
                year=int(y),
                month=int(m),
                value=round(float(v), 4),
                class_=str(cls),  # type: ignore[arg-type]
                percentile_rank=round(float(pr), 4),
                provisional=is_prov,
            )
        )
    return sorted(years_set), cells


def fetch_climatology(
    cursor: duckdb.DuckDBPyConnection,
    region_id: str,
) -> list[MonthClimatology]:
    """Fetch 12-month climatology baselines for a region."""
    rows = cursor.execute(
        """
        SELECT
            CAST(month AS INTEGER) AS m,
            CAST(mean AS DOUBLE) AS mn,
            CAST(p50 AS DOUBLE) AS p50,
            CAST(p90 AS DOUBLE) AS p90,
            CAST(p95 AS DOUBLE) AS p95
        FROM climatology
        WHERE region_id = ?
        ORDER BY m
        """,
        [region_id],
    ).fetchall()

    return [
        MonthClimatology(
            month=int(m),
            mean=round(float(mn), 4),
            p50=round(float(p50), 4),
            p90=round(float(p90), 4),
            p95=round(float(p95), 4),
        )
        for m, mn, p50, p90, p95 in rows
    ]


def fetch_season(
    cursor: duckdb.DuckDBPyConnection,
    region_id: str,
) -> FireSeason | None:
    """Fetch fire season metrics for a region."""
    row = cursor.execute(
        """
        SELECT
            CAST(start_month AS INTEGER) AS sm,
            CAST(peak_month AS INTEGER) AS pm,
            CAST(end_month AS INTEGER) AS em,
            CAST(share_of_annual AS DOUBLE) AS soa
        FROM seasons
        WHERE region_id = ?
        LIMIT 1
        """,
        [region_id],
    ).fetchone()

    if row is None:
        return None

    return FireSeason(
        start_month=int(row[0]),
        peak_month=int(row[1]),
        end_month=int(row[2]),
        share_of_annual=round(float(row[3]), 4),
    )
