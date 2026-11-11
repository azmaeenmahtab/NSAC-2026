"""FastAPI router for `/api/stats/yearly` and `/api/anomalies`."""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.dataset import LoadedDataset
from app.core.db import get_dataset, get_db_cursor
from app.core.errors import ValidationAPIError
from app.features.stats.schemas import AnomaliesEnvelope, YearlyStatsEnvelope
from app.features.stats.service import get_anomalies_envelope, get_yearly_stats_envelope

router = APIRouter(prefix="/api", tags=["Stats"])

DatasetDep = Annotated[LoadedDataset, Depends(get_dataset)]
CursorDep = Annotated[duckdb.DuckDBPyConnection, Depends(get_db_cursor)]


@router.get("/stats/yearly", operation_id="getYearlyStats", response_model=YearlyStatsEnvelope)
async def get_yearly_stats(
    dataset: DatasetDep,
    cursor: CursorDep,
    area_id: Annotated[str | None, Query(description="Region ID or preset ID")] = None,
    area: Annotated[str | None, Query(description="Alias for area_id")] = None,
) -> YearlyStatsEnvelope:
    """Yearly aggregated burning statistics."""
    target_area = area_id or area
    if not target_area:
        raise ValidationAPIError("Query parameter 'area_id' (or 'area') is required")
    return get_yearly_stats_envelope(dataset=dataset, cursor=cursor, area_id=target_area)


@router.get("/anomalies", operation_id="getAnomalies", response_model=AnomaliesEnvelope)
async def get_anomalies(
    dataset: DatasetDep,
    cursor: CursorDep,
    area_id: Annotated[str | None, Query(description="Region ID or preset ID")] = None,
    area: Annotated[str | None, Query(description="Alias for area_id")] = None,
    year: Annotated[int | None, Query(description="Filter by year")] = None,
    class_filter: Annotated[
        str | None,
        Query(alias="class", description="Filter by class: normal | elevated | extreme"),
    ] = None,
) -> AnomaliesEnvelope:
    """Anomalous fire months."""
    target_area = area_id or area
    if not target_area:
        raise ValidationAPIError("Query parameter 'area_id' (or 'area') is required")
    return get_anomalies_envelope(
        dataset=dataset,
        cursor=cursor,
        area_id=target_area,
        year=year,
        class_filter=class_filter,
    )
