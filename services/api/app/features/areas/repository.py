"""DuckDB repository for querying `regions` view with bound parameters."""

from __future__ import annotations

import duckdb

from app.features.areas.schemas import AreaItem

_LEVEL_EQUIVALENTS: dict[str, tuple[str, ...]] = {
    "country": ("country",),
    "adm1": ("adm1", "division"),
    "division": ("adm1", "division"),
    "adm2": ("adm2", "district"),
    "district": ("adm2", "district"),
    "preset": ("preset",),
}


def _row_to_area_item(row: tuple[object, ...]) -> AreaItem:
    region_id, name, level, parent_id, bbox_raw, aliases_raw = row
    bbox_list = [float(x) for x in bbox_raw] if isinstance(bbox_raw, (list, tuple)) else []
    aliases_list = [str(x) for x in aliases_raw] if isinstance(aliases_raw, (list, tuple)) else []
    return AreaItem(
        id=str(region_id),
        name=str(name),
        level=str(level),
        parent_id=str(parent_id) if parent_id is not None else None,
        bbox=bbox_list,
        aliases=aliases_list,
    )


def fetch_areas(
    cursor: duckdb.DuckDBPyConnection,
    level: str | None = None,
) -> list[AreaItem]:
    """Fetch all areas from the `regions` DuckDB view, optionally filtered by `level`."""
    if level is None:
        rows = cursor.execute(
            """
            SELECT region_id, name, level, parent_id, bbox, aliases
            FROM regions
            ORDER BY region_id
            """
        ).fetchall()
    else:
        allowed_levels = _LEVEL_EQUIVALENTS.get(level, (level,))
        if len(allowed_levels) == 1:
            rows = cursor.execute(
                """
                SELECT region_id, name, level, parent_id, bbox, aliases
                FROM regions
                WHERE level = ?
                ORDER BY region_id
                """,
                [allowed_levels[0]],
            ).fetchall()
        else:
            rows = cursor.execute(
                """
                SELECT region_id, name, level, parent_id, bbox, aliases
                FROM regions
                WHERE level IN (?, ?)
                ORDER BY region_id
                """,
                [allowed_levels[0], allowed_levels[1]],
            ).fetchall()

    return [_row_to_area_item(r) for r in rows]


def fetch_area_by_id(
    cursor: duckdb.DuckDBPyConnection,
    region_id: str,
) -> AreaItem | None:
    """Fetch a single region or preset by its `region_id`."""
    row = cursor.execute(
        """
        SELECT region_id, name, level, parent_id, bbox, aliases
        FROM regions
        WHERE region_id = ?
        LIMIT 1
        """,
        [region_id],
    ).fetchone()
    if row is None:
        return None
    return _row_to_area_item(row)


def fetch_child_region_ids(
    cursor: duckdb.DuckDBPyConnection,
    parent_id: str,
) -> list[str]:
    """Fetch child `region_id`s whose `parent_id` matches `parent_id`."""
    rows = cursor.execute(
        """
        SELECT region_id
        FROM regions
        WHERE parent_id = ?
        ORDER BY region_id
        """,
        [parent_id],
    ).fetchall()
    return [str(r[0]) for r in rows]
