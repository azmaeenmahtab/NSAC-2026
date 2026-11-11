"""Typed tool: get_calendar."""

from __future__ import annotations

from typing import Any

import duckdb
from pydantic import BaseModel, Field

from app.core.dataset import LoadedDataset
from app.features.calendar.service import get_calendar_envelope


class GetCalendarInput(BaseModel):
    """Input parameters for get_calendar tool."""

    area_id: str = Field(..., description="Canonical area ID")
    year: int | None = Field(default=None, description="Optional single year to filter grid cells")


def execute_get_calendar(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
    year: int | None = None,
) -> dict[str, Any]:
    """Execute get_calendar tool returning grid cells and climatology."""
    calendar_env = get_calendar_envelope(dataset, cursor, area_id)
    grid = calendar_env.data.grid

    if year is not None:
        filtered_grid = [c for c in grid if c.year == year]
        years_list = [year]
    else:
        filtered_grid = grid
        years_list = sorted({c.year for c in grid})

    grid_data = [
        {
            "year": c.year,
            "month": c.month,
            "value": round(c.value, 2),
            "class": getattr(c, "class_", "normal"),
            "percentile_rank": round(c.percentile_rank, 4),
        }
        for c in filtered_grid
    ]

    climatology_data = [
        {
            "month": clim.month,
            "mean": round(clim.mean, 2),
            "p50": round(clim.p50, 2),
            "p90": round(clim.p90, 2),
            "p95": round(clim.p95, 2),
        }
        for clim in calendar_env.data.climatology
    ]

    return {
        "area_id": area_id,
        "grid": grid_data,
        "climatology": climatology_data,
        "evidence": {
            "tool": "get_calendar",
            "areaId": area_id,
            "years": years_list,
            "dataVersion": dataset.data_version,
        },
    }
