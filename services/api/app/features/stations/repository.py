"""DuckDB read-only queries for fire stations and local risk signals."""

from __future__ import annotations

from typing import Any

import duckdb


def fetch_all_fire_stations(
    cursor: duckdb.DuckDBPyConnection,
    registered_views: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Fetch all reference fire stations when `fire_stations` view is available."""
    if "fire_stations" not in registered_views:
        return []

    rows = cursor.execute(
        """
        SELECT station_id, name, district_id, district_name, lat, lon,
               hotline, national_emergency, phone, email
        FROM fire_stations
        ORDER BY station_id
        """
    ).fetchall()

    return [
        {
            "station_id": str(r[0]),
            "name": str(r[1]),
            "district_id": str(r[2] or ""),
            "district_name": str(r[3] or ""),
            "lat": float(r[4]),
            "lon": float(r[5]),
            "hotline": str(r[6] or "102"),
            "national_emergency": str(r[7] or "999"),
            "phone": str(r[8]) if r[8] is not None else None,
            "email": str(r[9]) if r[9] is not None else None,
        }
        for r in rows
    ]


def fetch_latest_anomaly_class(
    cursor: duckdb.DuckDBPyConnection,
    region_id: str,
) -> str:
    """Return the latest recorded anomaly class ('normal', 'elevated', 'extreme') for a region."""
    row = cursor.execute(
        """
        SELECT class
        FROM anomalies
        WHERE region_id = ?
        ORDER BY year DESC, month DESC
        LIMIT 1
        """,
        [region_id],
    ).fetchone()
    if row and row[0]:
        return str(row[0]).lower()
    return "normal"


def fetch_recent_events_in_box(
    cursor: duckdb.DuckDBPyConnection,
    registered_views: tuple[str, ...],
    lat: float,
    lon: float,
    degree_margin: float = 0.25,
) -> int:
    """Count fire events from the latest active month within a box around `(lat, lon)`."""
    if "events" not in registered_views:
        return 0
    row = cursor.execute(
        """
        WITH latest AS (
            SELECT MAX(CAST(year AS INTEGER) * 100 + CAST(month AS INTEGER)) AS ym
            FROM events
        )
        SELECT COUNT(*)
        FROM events, latest
        WHERE (CAST(year AS INTEGER) * 100 + CAST(month AS INTEGER)) = latest.ym
          AND lat BETWEEN ? AND ?
          AND lon BETWEEN ? AND ?
        """,
        [lat - degree_margin, lat + degree_margin, lon - degree_margin, lon + degree_margin],
    ).fetchone()
    return int(row[0]) if row and row[0] else 0

