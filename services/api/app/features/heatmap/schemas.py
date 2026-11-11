"""Pydantic schemas for `/api/heatmap`."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.core.responses import ResponseMeta

HeatmapMetric = Literal["harmonized", "raw_modis", "raw_viirs"]


class HeatmapCell(BaseModel):
    """Single H3 hexagon density entry with lowercase hex string ID."""

    h3: str = Field(..., examples=["87642825fffffff"])
    value: float = Field(..., examples=[4.5])


class HeatmapStats(BaseModel):
    """Summary distribution statistics across returned heatmap cells."""

    min: float
    p50: float = 0.0
    p95: float
    max: float
    sum: float = 0.0
    count: int = 0


class HeatmapData(BaseModel):
    """Data payload for `GET /api/heatmap`."""

    res: int = Field(..., examples=[7])
    metric: HeatmapMetric = Field(default="harmonized")
    from_month: str = Field(..., serialization_alias="from", examples=["2020-01"])
    to_month: str = Field(..., serialization_alias="to", examples=["2020-12"])
    cells: list[HeatmapCell] = Field(default_factory=list)
    stats: HeatmapStats


class HeatmapEnvelope(BaseModel):
    """Envelope returned by `GET /api/heatmap`."""

    data: HeatmapData
    meta: ResponseMeta
