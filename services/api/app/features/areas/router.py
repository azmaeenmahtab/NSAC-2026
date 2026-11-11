"""FastAPI router for `/api/areas`."""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.dataset import LoadedDataset
from app.core.db import get_dataset, get_db_cursor
from app.features.areas.schemas import AreasEnvelope
from app.features.areas.service import list_areas_envelope

router = APIRouter(prefix="/api", tags=["Areas"])

DatasetDep = Annotated[LoadedDataset, Depends(get_dataset)]
CursorDep = Annotated[duckdb.DuckDBPyConnection, Depends(get_db_cursor)]


@router.get("/areas", operation_id="getAreas", response_model=AreasEnvelope)
async def get_areas(
    dataset: DatasetDep,
    cursor: CursorDep,
    level: Annotated[
        str | None,
        Query(description="Filter areas by administrative or preset level"),
    ] = None,
) -> AreasEnvelope:
    """List all available regions and presets."""
    return list_areas_envelope(dataset=dataset, cursor=cursor, level=level)
