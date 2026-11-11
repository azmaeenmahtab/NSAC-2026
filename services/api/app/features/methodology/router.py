"""FastAPI router for `/api/methodology`."""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends

from app.core.dataset import LoadedDataset
from app.core.db import get_dataset, get_db_cursor
from app.features.methodology.schemas import MethodologyEnvelope
from app.features.methodology.service import get_methodology_envelope

router = APIRouter(prefix="/api", tags=["Methodology"])

DatasetDep = Annotated[LoadedDataset, Depends(get_dataset)]
CursorDep = Annotated[duckdb.DuckDBPyConnection, Depends(get_db_cursor)]


@router.get("/methodology", operation_id="getMethodology", response_model=MethodologyEnvelope)
async def get_methodology(
    dataset: DatasetDep,
    cursor: CursorDep,
) -> MethodologyEnvelope:
    """Methodology report, cross-validation metrics, and jump statistics."""
    return get_methodology_envelope(dataset=dataset, cursor=cursor)
