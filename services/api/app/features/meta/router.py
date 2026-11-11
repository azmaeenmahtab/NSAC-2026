"""FastAPI router for `/api/health` and `/api/meta`."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dataset import LoadedDataset
from app.core.db import get_dataset
from app.features.meta.schemas import HealthResponse, MetaEnvelope
from app.features.meta.service import build_health_response, build_meta_envelope

router = APIRouter(prefix="/api", tags=["Meta"])

DatasetDep = Annotated[LoadedDataset, Depends(get_dataset)]


@router.get("/health", operation_id="getHealth", response_model=HealthResponse)
async def get_health(dataset: DatasetDep) -> HealthResponse:
    """Health check and service status."""
    return build_health_response(dataset)


@router.get("/meta", operation_id="getMeta", response_model=MetaEnvelope)
async def get_meta(dataset: DatasetDep) -> MetaEnvelope:
    """Metadata, active data version, and data lineage summary."""
    return build_meta_envelope(dataset)
