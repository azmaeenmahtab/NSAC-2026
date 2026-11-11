"""Typed tool: get_anomalies."""

from __future__ import annotations

from typing import Any

import duckdb
from pydantic import BaseModel, Field

from app.core.dataset import LoadedDataset
from app.features.stats.service import get_anomalies_envelope


class GetAnomaliesInput(BaseModel):
    """Input parameters for get_anomalies tool."""

    area_id: str = Field(..., description="Canonical area ID")
    year: int | None = Field(default=None, description="Optional year filter")


def execute_get_anomalies(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
    year: int | None = None,
) -> dict[str, Any]:
    """Execute get_anomalies tool for an area and optional year."""
    envelope = get_anomalies_envelope(dataset, cursor, area_id=area_id, year=year)
    items = envelope.data

    years_list = sorted({item.year for item in items}) if items else ([year] if year else [])
    anomalies_data = [
        {
            "year": item.year,
            "month": item.month,
            "value": round(item.value, 2),
            "percentile_rank": round(item.percentile_rank, 4),
            "class": getattr(item, "class_", "normal"),
        }
        for item in items
    ]

    return {
        "area_id": area_id,
        "anomalies": anomalies_data,
        "evidence": {
            "tool": "get_anomalies",
            "areaId": area_id,
            "years": years_list,
            "dataVersion": dataset.data_version,
        },
    }
