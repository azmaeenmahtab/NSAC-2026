"""Pydantic schemas for `/api/alerts` subscriptions and active status."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.responses import ResponseMeta

AlertRule = Literal["season_approaching", "above_normal", "both"]
AnomalyClass = Literal["normal", "elevated", "extreme"]

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class SubscriptionRequest(BaseModel):
    """Payload for creating a new alert subscription."""

    email: str
    area_id: str
    rule: AlertRule
    lead_days: int = Field(default=14, ge=1, le=60)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip()
        if not _EMAIL_REGEX.match(cleaned):
            raise ValueError(f"Invalid email format: '{v}'")
        return cleaned


class SubscriptionResponseData(BaseModel):
    """Data payload for accepted subscription."""

    message: str
    status: str = "pending_confirmation"


class SubscriptionEnvelope(BaseModel):
    """Envelope returned on successful subscription creation."""

    data: SubscriptionResponseData
    meta: ResponseMeta | None = None


class ConfirmResponseData(BaseModel):
    """Data payload for confirmed subscription."""

    confirmed: bool = True
    message: str = "Subscription confirmed successfully"


class ConfirmEnvelope(BaseModel):
    """Envelope returned on subscription confirmation."""

    data: ConfirmResponseData


class UnsubscribeResponseData(BaseModel):
    """Data payload for subscription removal."""

    unsubscribed: bool = True
    message: str = "Unsubscribed successfully"


class UnsubscribeEnvelope(BaseModel):
    """Envelope returned on unsubscription."""

    data: UnsubscribeResponseData


class ActiveAlertsData(BaseModel):
    """Active advisory alert status for an area."""

    model_config = ConfigDict(populate_by_name=True)

    season_approaching: bool
    above_normal: bool
    current_month_class: AnomalyClass | None = None
    days_until_season: int | None = None
    reason: str | None = None
    provisional_as_of: str | None = None


class ActiveAlertsEnvelope(BaseModel):
    """Envelope returned by `GET /api/alerts/active`."""

    data: ActiveAlertsData
    meta: ResponseMeta
