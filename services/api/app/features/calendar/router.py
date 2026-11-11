"""FastAPI router for `/api/calendar`."""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.dataset import LoadedDataset
from app.core.db import get_dataset, get_db_cursor
from app.features.calendar.schemas import CalendarEnvelope
from app.features.calendar.service import get_calendar_envelope

router = APIRouter(prefix="/api", tags=["Calendar"])

DatasetDep = Annotated[LoadedDataset, Depends(get_dataset)]
CursorDep = Annotated[duckdb.DuckDBPyConnection, Depends(get_db_cursor)]


@router.get("/calendar", operation_id="getCalendar", response_model=CalendarEnvelope)
async def get_calendar(
    dataset: DatasetDep,
    cursor: CursorDep,
    area_id: Annotated[
        str | None,
        Query(description="Region ID or preset ID"),
    ] = None,
    area: Annotated[
        str | None,
        Query(description="Alias for area_id"),
    ] = None,
) -> CalendarEnvelope:
    """Grid of years x months with anomalies and climatology for FireCalendar."""
    target_area = area_id or area
    if not target_area:
        from app.core.errors import ValidationAPIError
        raise ValidationAPIError("Query parameter 'area_id' (or 'area') is required")
    return get_calendar_envelope(dataset=dataset, cursor=cursor, area_id=target_area)
