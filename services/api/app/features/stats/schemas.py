"""Pydantic schemas for `/api/stats/yearly` and `/api/anomalies`."""

from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.core.responses import ResponseMeta

AnomalyClass = Literal["normal", "elevated", "extreme"]


class YearlyStatRow(BaseModel):
    """Yearly summary statistics row."""

    year: int
    harmonized_total: float
    frp_sum: float
    rank: int
    vs_mean_pct: float
    peak_month: int
    total_events: int | None = None
    total_frp_mw: float | None = None


class YearlyStatsEnvelope(BaseModel):
    """Envelope returned by `GET /api/stats/yearly`."""

    data: list[YearlyStatRow]
    meta: ResponseMeta


class AnomalyItem(BaseModel):
    """Anomalous month record."""

    model_config = ConfigDict(populate_by_name=True)

    year: int
    month: int
    value: float
    percentile_rank: float
    class_: AnomalyClass = Field(
        ...,
        validation_alias=AliasChoices("class", "class_"),
        serialization_alias="class",
    )


class AnomaliesEnvelope(BaseModel):
    """Envelope returned by `GET /api/anomalies`."""

    data: list[AnomalyItem]
    meta: ResponseMeta
