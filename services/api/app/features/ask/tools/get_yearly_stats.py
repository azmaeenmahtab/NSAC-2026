"""Typed tool: get_yearly_stats."""

from __future__ import annotations

from typing import Any

import duckdb
from pydantic import BaseModel, Field

from app.core.dataset import LoadedDataset
from app.features.stats.service import get_yearly_stats_envelope


class GetYearlyStatsInput(BaseModel):
    """Input parameters for get_yearly_stats tool."""

    area_id: str = Field(..., description="Canonical area ID")
    year: int | None = Field(default=None, description="Optional single year to filter stats")


def execute_get_yearly_stats(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
    year: int | None = None,
) -> dict[str, Any]:
    """Execute get_yearly_stats tool for an area."""
    envelope = get_yearly_stats_envelope(dataset, cursor, area_id)
    records = envelope.data

    if year is not None:
        filtered = [r for r in records if r.year == year]
        years_list = [year]
    else:
        filtered = records
        years_list = [r.year for r in records]

    stats_data = [
        {
            "year": r.year,
            "harmonized_total": round(r.harmonized_total, 2),
            "frp_sum": round(r.frp_sum, 2),
            "rank": r.rank,
            "vs_mean_pct": round(r.vs_mean_pct, 2),
            "peak_month": r.peak_month,
        }
        for r in filtered
    ]

    return {
        "area_id": area_id,
        "stats": stats_data,
        "evidence": {
            "tool": "get_yearly_stats",
            "areaId": area_id,
            "years": years_list,
            "dataVersion": dataset.data_version,
        },
    }

