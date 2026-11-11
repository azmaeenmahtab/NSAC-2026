"""Pydantic schemas for `/api/methodology`."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.core.responses import ResponseMeta


class JumpMetrics(BaseModel):
    """Jump metrics describing structural break before vs after harmonization."""

    naive_ratio: float = Field(..., examples=[3.77])
    harmonized_ratio: float = Field(..., examples=[1.0])
    overlap_cv_rmse: float | None = Field(default=None, examples=[0.0])
    overlap_cv_bias: float | None = Field(default=None, examples=[0.0])
    rank_correlation: float | None = Field(default=None, examples=[1.0])


class QQPoint(BaseModel):
    """Quantile-quantile empirical alignment point."""

    quantile: float
    modis: float
    viirs_raw: float
    viirs_harmonized: float


class MethodologyData(BaseModel):
    """Methodology diagnostics, parameters, calibration summary, and limitations."""

    parameters: dict[str, Any] = Field(default_factory=dict)
    calibration_summary: list[dict[str, Any]] = Field(default_factory=list)
    jump_metrics: JumpMetrics
    qq_data: list[QQPoint] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class MethodologyEnvelope(BaseModel):
    """Envelope returned by `GET /api/methodology`."""

    data: MethodologyData
    meta: ResponseMeta
