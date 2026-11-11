"""Pydantic schemas for `/api/guidance`."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.core.responses import ResponseMeta

GuidanceStage = Literal[
    "pre_season",
    "in_season",
    "post_season",
    "extreme",
    "off_season",
]

GuidanceAudience = Literal["community", "land_manager", "responder"]


class GuidanceItem(BaseModel):
    """A rule-based wildland action or mitigation checklist item."""

    id: str = Field(..., description="Unique checklist item identifier")
    stage: GuidanceStage = Field(..., description="Fire calendar readiness/action stage")
    audience: str = Field(..., description="Target audience (community, land_manager, responder)")
    text: str = Field(..., description="Actionable checklist recommendation")
    source_title: str | None = Field(default=None, description="Title of the citing publication")
    source_url: str | None = Field(default=None, description="URL of reference document")
    verified: bool = Field(..., description="Whether human field verified against cited source")


class GuidanceMeta(ResponseMeta):
    """Metadata envelope for guidance response, including stage and advisory disclaimer."""

    stage: GuidanceStage | None = Field(
        default=None,
        description="Resolved fire calendar stage for the requested area and month",
    )
    disclaimer: str = Field(
        default="Alerts, fire season stages, and action guidance are advisory, not an official warning system; follow local authorities.",
        description="Advisory disclaimer",
    )


class GuidanceEnvelope(BaseModel):
    """Envelope returned by `GET /api/guidance`."""

    data: list[GuidanceItem]
    meta: GuidanceMeta

