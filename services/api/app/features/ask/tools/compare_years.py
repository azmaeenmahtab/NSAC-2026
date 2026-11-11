"""Typed tool: compare_years."""

from __future__ import annotations

from typing import Any

import duckdb
from pydantic import BaseModel, Field

from app.core.dataset import LoadedDataset
from app.features.stats.service import get_yearly_stats_envelope


class CompareYearsInput(BaseModel):
    """Input parameters for compare_years tool."""

    area_id: str = Field(..., description="Canonical area ID")
    year_a: int = Field(..., description="Baseline comparison year (e.g. 2019)")
    year_b: int = Field(..., description="Target comparison year (e.g. 2020)")


def execute_compare_years(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
    year_a: int,
    year_b: int,
) -> dict[str, Any]:
    """Compare fire activity and total harmonized events between two years."""
    envelope = get_yearly_stats_envelope(dataset, cursor, area_id)
    by_year = {r.year: r for r in envelope.data}

    rec_a = by_year.get(year_a)
    rec_b = by_year.get(year_b)

    tot_a = rec_a.harmonized_total if rec_a else 0.0
    tot_b = rec_b.harmonized_total if rec_b else 0.0

    ratio = round(tot_b / tot_a, 2) if tot_a > 0 else None
    diff = round(tot_b - tot_a, 2)

    return {
        "area_id": area_id,
        "year_a": {
            "year": year_a,
            "harmonized_total": tot_a,
            "peak_month": rec_a.peak_month if rec_a else None,
            "rank": rec_a.rank if rec_a else None,
        },
        "year_b": {
            "year": year_b,
            "harmonized_total": tot_b,
            "peak_month": rec_b.peak_month if rec_b else None,
            "rank": rec_b.rank if rec_b else None,
        },
        "ratio_b_to_a": ratio,
        "difference": diff,
        "evidence": {
            "tool": "compare_years",
            "areaId": area_id,
            "years": [year_a, year_b],
            "dataVersion": dataset.data_version,
        },
    }

