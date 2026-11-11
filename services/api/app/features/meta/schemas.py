"""Pydantic schemas for `/api/health` and `/api/meta`."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.core.responses import ResponseMeta


class HealthResponse(BaseModel):
    """Liveness and dataset readiness payload for `/api/health`."""

    status: str = Field(..., examples=["healthy"])
    service: str = Field(..., examples=["PyroScope API"])
    version: str = Field(..., examples=["0.1.0"])
    dataLoaded: bool = Field(default=True, examples=[True])
    dataVersion: str = Field(..., examples=["v0.1.0-fixtures"])


class MetaData(BaseModel):
    """Dataset lineage, parameters, and attribution payload for `/api/meta`."""

    dataVersion: str = Field(..., examples=["v0.1.0-fixtures"])
    asOf: str = Field(..., examples=["2025-12-31"])
    provisionalFrom: str | None = Field(default=None)
    parametersSummary: dict[str, Any] = Field(default_factory=dict)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    counts: dict[str, Any] = Field(default_factory=dict)
    attribution: str


class MetaEnvelope(BaseModel):
    """Envelope returned by `GET /api/meta`."""

    data: MetaData
    meta: ResponseMeta
