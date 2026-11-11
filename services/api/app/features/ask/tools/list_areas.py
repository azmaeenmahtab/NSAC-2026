"""Typed tool: list_areas."""

from __future__ import annotations

from typing import Any

import duckdb
from pydantic import BaseModel

from app.core.dataset import LoadedDataset
from app.features.areas.service import list_areas_envelope


class ListAreasInput(BaseModel):
    """Input parameters for list_areas tool."""

    level: str | None = None


def execute_list_areas(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    level: str | None = None,
) -> dict[str, Any]:
    """Execute list_areas and return areas catalog with evidence."""
    envelope = list_areas_envelope(dataset, cursor, level=level)
    areas_data = [
        {
            "id": a.id,
            "name": a.name,
            "level": a.level,
            "parent_id": a.parent_id,
        }
        for a in envelope.data
    ]
    return {
        "areas": areas_data,
        "evidence": {
            "tool": "list_areas",
            "areaId": None,
            "years": [],
            "dataVersion": dataset.data_version,
        },
    }

