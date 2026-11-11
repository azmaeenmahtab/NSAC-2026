"""FastAPI router for `/api/stats/yearly` and `/api/anomalies`."""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.dataset import LoadedDataset
from app.core.db import get_dataset, get_db_cursor
from app.features.stats.schemas import AnomaliesEnvelope, YearlyStatsEnvelope
from app.features.stats.service import get_anomalies_envelope, get_yearly_stats_envelope

router = APIRouter(prefix="/api", tags=["Stats"])

DatasetDep = Annotated[LoadedDataset, Depends(get_dataset)]
CursorDep = Annotated[duckdb.DuckDBPyConnection, Depends(get_db_cursor)]


@router.get("/stats/yearly", operation_id="getYearlyStats", response_model=YearlyStatsEnvelope)
async def get_yearly_stats(
    dataset: DatasetDep,
    cursor: CursorDep,
    area_id: Annotated[str, Query(description="Region ID or preset ID")],
) -> YearlyStatsEnvelope:
    """Yearly aggregated burning statistics."""
    return get_yearly_stats_envelope(dataset=dataset, cursor=cursor, area_id=area_id)


@router.get("/anomalies", operation_id="getAnomalies", response_model=AnomaliesEnvelope)
async def get_anomalies(
    dataset: DatasetDep,
    cursor: CursorDep,
    area_id: Annotated[str, Query(description="Region ID or preset ID")],
    year: Annotated[int | None, Query(description="Filter by year")] = None,
    class_filter: Annotated[
        str | None,
        Query(alias="class", description="Filter by class: normal | elevated | extreme"),
    ] = None,
) -> AnomaliesEnvelope:
    """Anomalous fire months."""
    return get_anomalies_envelope(
        dataset=dataset,
        cursor=cursor,
        area_id=area_id,
        year=year,
        class_filter=class_filter,
    )
