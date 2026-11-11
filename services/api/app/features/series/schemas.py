"""Pydantic schemas for `/api/series`."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.core.responses import ResponseMeta


class SeriesPoint(BaseModel):
    """Single monthly record comparing raw MODIS, raw VIIRS, naive splice, and harmonized."""

    year: int
    month: int
    raw_modis: float | None = None
    raw_viirs: float | None = None
    naive_splice: float
    harmonized: float
    in_overlap: bool
    source_used: Literal["modis_raw", "viirs_calibrated"]
    provisional: bool = Field(default=False)


class SeriesEnvelope(BaseModel):
    """Envelope returned by `GET /api/series`."""

    data: list[SeriesPoint]
    meta: ResponseMeta
