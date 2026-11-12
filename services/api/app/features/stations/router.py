"""HTTP router for `/api/stations/nearby`."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.core.dataset import LoadedDataset
from app.features.stations.schemas import NearbyStationsEnvelope
from app.features.stations.service import find_nearby_stations

router = APIRouter(prefix="/api/stations", tags=["Stations"])


@router.get("/nearby", response_model=NearbyStationsEnvelope, operation_id="getNearbyStations")
def get_nearby_stations(
    request: Request,
    lat: float | None = Query(default=None, description="User GPS latitude (WGS84)"),
    lon: float | None = Query(default=None, description="User GPS longitude (WGS84)"),
    area_id: str = Query(default="PRESET-CHT", description="Fallback region or bbox ID"),
    radius_km: float = Query(default=50.0, ge=5.0, le=300.0),
    limit: int = Query(default=5, ge=1, le=20),
) -> NearbyStationsEnvelope:
    """Return nearest fire service stations with direct dial and plain-English email templates."""
    dataset: LoadedDataset = request.app.state.dataset
    cursor = dataset.cursor()
    try:
        return find_nearby_stations(
            dataset=dataset,
            cursor=cursor,
            lat=lat,
            lon=lon,
            area_id=area_id,
            radius_km=radius_km,
            limit=limit,
        )
    finally:
        cursor.close()
