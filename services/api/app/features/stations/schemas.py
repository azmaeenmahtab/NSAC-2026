"""Pydantic schemas for `/api/stations/nearby`."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.responses import ResponseMeta
from app.features.alerts.evaluate import ThreatLevel


class NearbyStationItem(BaseModel):
    """A fire station near the user's location or selected region."""

    station_id: str
    name: str
    district_id: str
    district_name: str
    lat: float
    lon: float
    distance_km: float
    hotline: str
    national_emergency: str
    phone: str | None = None
    email: str | None = None
    dial_number: str
    email_subject: str
    email_body: str


class ThreatSummary(BaseModel):
    """Plain-English risk summary for the queried area."""

    level: ThreatLevel
    headline: str
    explanation: str
    nearby_recent_events: int = 0


class NearbyStationsData(BaseModel):
    """Payload returned by `GET /api/stations/nearby`."""

    center_lat: float
    center_lon: float
    location_source: str
    area_id: str
    area_name: str
    threat: ThreatSummary
    stations: list[NearbyStationItem] = Field(default_factory=list)


class NearbyStationsEnvelope(BaseModel):
    """Envelope returned by `GET /api/stations/nearby`."""

    data: NearbyStationsData
    meta: ResponseMeta

