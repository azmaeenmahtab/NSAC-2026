"""Typed tool: get_season."""

from __future__ import annotations

from typing import Any

import duckdb
from pydantic import BaseModel, Field

from app.core.dataset import LoadedDataset
from app.features.calendar.service import get_calendar_envelope


class GetSeasonInput(BaseModel):
    """Input parameters for get_season tool."""

    area_id: str = Field(..., description="Canonical area ID (e.g. 'PRESET-CHT', 'BGD-ADM2-rangamati')")


def execute_get_season(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
) -> dict[str, Any]:
    """Execute get_season tool for a specified area."""
    calendar_env = get_calendar_envelope(dataset, cursor, area_id)
    season = calendar_env.data.season

    start_m = season.start_month
    end_m = season.end_month
    window_length = (end_m - start_m + 1) if end_m >= start_m else (end_m + 12 - start_m + 1)

    return {
        "area_id": area_id,
        "start_month": season.start_month,
        "peak_month": season.peak_month,
        "end_month": season.end_month,
        "share_of_annual": round(season.share_of_annual, 4),
        "window_length": window_length,
        "evidence": {
            "tool": "get_season",
            "areaId": area_id,
            "years": [],
            "dataVersion": dataset.data_version,
        },
    }
