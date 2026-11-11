"""FastAPI router for `/api/series`."""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.dataset import LoadedDataset
from app.core.db import get_dataset, get_db_cursor
from app.features.series.schemas import SeriesEnvelope
from app.features.series.service import get_series_envelope

router = APIRouter(prefix="/api", tags=["Series"])

DatasetDep = Annotated[LoadedDataset, Depends(get_dataset)]
CursorDep = Annotated[duckdb.DuckDBPyConnection, Depends(get_db_cursor)]


@router.get("/series", operation_id="getSeries", response_model=SeriesEnvelope)
async def get_series(
    dataset: DatasetDep,
    cursor: CursorDep,
    area_id: Annotated[str, Query(description="Region ID, preset ID, or bbox:w,s,e,n")],
    from_param: Annotated[
        str | None,
        Query(alias="from", description="Optional start year-month YYYY-MM"),
    ] = None,
    to_param: Annotated[
        str | None,
        Query(alias="to", description="Optional end year-month YYYY-MM"),
    ] = None,
) -> SeriesEnvelope:
    """Monthly time series comparing raw vs harmonized values."""
    return get_series_envelope(
        dataset=dataset,
        cursor=cursor,
        area_id=area_id,
        from_str=from_param,
        to_str=to_param,
    )
