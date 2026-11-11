"""FastAPI router for `/api/guidance`."""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.dataset import LoadedDataset
from app.core.db import get_dataset, get_db_cursor
from app.features.guidance.schemas import GuidanceEnvelope
from app.features.guidance.service import get_guidance

router = APIRouter(prefix="/api", tags=["guidance"])

DatasetDep = Annotated[LoadedDataset, Depends(get_dataset)]
CursorDep = Annotated[duckdb.DuckDBPyConnection, Depends(get_db_cursor)]


@router.get(
    "/guidance",
    response_model=GuidanceEnvelope,
    summary="Wildland action planner rule-based checklist",
    operation_id="getGuidance",
)
def get_guidance_endpoint(
    area_id: Annotated[str, Query(description="Target area or region ID")],
    dataset: DatasetDep,
    cursor: CursorDep,
    month: Annotated[int | None, Query(ge=1, le=12, description="Calendar month (1-12)")] = None,
    stage: Annotated[str | None, Query(description="Optional override stage filter")] = None,
    audience: Annotated[
        str | None,
        Query(description="Optional audience filter (community, land_manager, responder)"),
    ] = None,
) -> GuidanceEnvelope:
    """Return wildland fire checklist items and advisory stage for the area."""
    return get_guidance(
        dataset=dataset,
        cursor=cursor,
        area_id=area_id,
        month=month,
        stage_override=stage,
        audience=audience,
    )
