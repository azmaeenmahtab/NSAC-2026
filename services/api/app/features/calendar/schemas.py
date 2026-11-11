"""Pydantic schemas for `/api/calendar`."""

from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.core.responses import ResponseMeta


class CalendarCell(BaseModel):
    """Monthly calendar cell with fire density value, classification, and percentile rank."""

    model_config = ConfigDict(populate_by_name=True)

    year: int
    month: int
    value: float
    class_: Literal["normal", "elevated", "extreme"] = Field(
        ...,
        validation_alias=AliasChoices("class", "class_"),
        serialization_alias="class",
    )
    percentile_rank: float
    provisional: bool = False


class MonthClimatology(BaseModel):
    """Climatological baseline stats for a single calendar month."""

    month: int
    mean: float
    p50: float
    p90: float
    p95: float


class FireSeason(BaseModel):
    """Fire season summary metrics for an area."""

    start_month: int
    peak_month: int
    end_month: int
    share_of_annual: float


class CalendarData(BaseModel):
    """Calendar data container."""

    years: list[int] = Field(default_factory=list)
    grid: list[CalendarCell] = Field(default_factory=list)
    climatology: list[MonthClimatology] = Field(default_factory=list)
    season: FireSeason


class CalendarEnvelope(BaseModel):
    """Envelope returned by `GET /api/calendar`."""

    data: CalendarData
    meta: ResponseMeta
