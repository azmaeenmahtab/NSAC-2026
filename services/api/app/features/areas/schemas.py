"""Pydantic schemas and resolved area structures for `/api/areas`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from app.core.responses import ResponseMeta

AreaLevelParam = Literal["country", "adm1", "adm2", "division", "district", "preset"]


class AreaItem(BaseModel):
    """Region or preset definition returned by `/api/areas`."""

    id: str = Field(..., examples=["BGD"])
    name: str = Field(..., examples=["Bangladesh"])
    level: str = Field(..., examples=["country"])
    parent_id: str | None = Field(default=None)
    bbox: list[float] = Field(..., examples=[[88.0, 20.5, 92.8, 26.7]])
    aliases: list[str] = Field(default_factory=list)


class AreasEnvelope(BaseModel):
    """Envelope returned by `GET /api/areas`."""

    data: list[AreaItem]
    meta: ResponseMeta


@dataclass(frozen=True)
class ResolvedArea:
    """Resolved area specification used by downstream series, calendar, and stats features."""

    area_id: str
    kind: Literal["region", "preset", "bbox"]
    level: str
    name: str
    region_ids: tuple[str, ...]
    bbox: tuple[float, float, float, float]
