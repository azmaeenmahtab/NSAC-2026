"""Pure spatial matching and plain-English emergency contact formatting for nearby stations."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import duckdb

from app.core.dataset import LoadedDataset
from app.core.errors import ValidationAPIError
from app.core.responses import ResponseMeta
from app.features.alerts.evaluate import (
    ThreatAssessment,
    compute_threat_level,
    season_approaching,
)
from app.features.areas.service import resolve_area
from app.features.calendar.repository import fetch_season
from app.features.stations.repository import (
    fetch_all_fire_stations,
    fetch_latest_anomaly_class,
    fetch_recent_events_in_box,
)
from app.features.stations.schemas import (
    NearbyStationItem,
    NearbyStationsData,
    NearbyStationsEnvelope,
    ThreatSummary,
)

_EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance in kilometers between two WGS84 points."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return 2.0 * _EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def build_citizen_report_email(
    station_name: str,
    area_name: str,
    lat: float,
    lon: float,
    threat: ThreatAssessment,
) -> tuple[str, str]:
    """Build a short, plain-English fire report email for one-click citizen sending."""
    now_dhaka = datetime.now(UTC) + timedelta(hours=6)
    time_str = now_dhaka.strftime("%Y-%m-%d %I:%M %p (Bangladesh Time)")
    subject = f"[{threat.level} Risk] Fire Alert Report Near {area_name}"
    body = (
        f"Hello {station_name},\n\n"
        f"I am reporting a possible fire near {area_name}.\n\n"
        f"- Location: {lat:.4f}N, {lon:.4f}E (https://maps.google.com/?q={lat:.5f},{lon:.5f})\n"
        f"- Time Reported: {time_str}\n"
        f"- Current Area Risk: {threat.level} ({threat.headline})\n\n"
        f"Please check this location when possible.\n"
    )
    return subject, body


def _is_near_bangladesh(lat: float, lon: float) -> bool:
    return 19.5 <= lat <= 27.5 and 87.5 <= lon <= 93.5


def find_nearby_stations(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    lat: float | None = None,
    lon: float | None = None,
    area_id: str = "PRESET-CHT",
    radius_km: float = 50.0,
    limit: int = 5,
) -> NearbyStationsEnvelope:
    """Find nearest fire stations and compute plain-English area threat summary."""
    if (lat is None) != (lon is None):
        raise ValidationAPIError("Both 'lat' and 'lon' must be provided together.")

    if lat is not None and (lat < -90 or lat > 90):
        raise ValidationAPIError("Latitude must be between -90 and 90.")
    if lon is not None and (lon < -180 or lon > 180):
        raise ValidationAPIError("Longitude must be between -180 and 180.")

    resolved = resolve_area(cursor, area_id)
    bbox = resolved.bbox or [88.0, 20.5, 92.8, 26.7]
    area_center_lon = (bbox[0] + bbox[2]) / 2.0
    area_center_lat = (bbox[1] + bbox[3]) / 2.0

    if lat is not None and lon is not None:
        if _is_near_bangladesh(lat, lon):
            center_lat, center_lon = lat, lon
            loc_source = "gps"
        else:
            center_lat, center_lon = area_center_lat, area_center_lon
            loc_source = "area_fallback_outside_bd"
    else:
        center_lat, center_lon = area_center_lat, area_center_lon
        loc_source = "selected_area"

    # Compute plain-English area risk
    today = datetime.now(UTC).date()
    target_id = resolved.area_id
    season = fetch_season(cursor, target_id)
    if not season and resolved.region_ids:
        season = fetch_season(cursor, resolved.region_ids[0])

    is_appr = bool(season and season_approaching(today, season.start_month, lead_days=14))
    in_season = bool(
        season
        and (
            (
                season.start_month <= season.end_month
                and season.start_month <= today.month <= season.end_month
            )
            or (
                season.start_month > season.end_month
                and (today.month >= season.start_month or today.month <= season.end_month)
            )
        )
    )
    anom_cls = fetch_latest_anomaly_class(cursor, target_id)
    nearby_events = fetch_recent_events_in_box(
        cursor, dataset.registered_views, center_lat, center_lon
    )
    threat = compute_threat_level(
        is_season_approaching=is_appr,
        in_fire_season=in_season,
        anomaly_class=anom_cls,
        nearby_events_count=nearby_events,
    )

    all_stations = fetch_all_fire_stations(cursor, dataset.registered_views)
    ranked: list[tuple[float, dict[str, object]]] = []
    for st in all_stations:
        dist = haversine_km(center_lat, center_lon, float(st["lat"]), float(st["lon"]))
        ranked.append((dist, st))
    ranked.sort(key=lambda item: item[0])

    within_radius = [item for item in ranked if item[0] <= radius_km]
    chosen = (within_radius if within_radius else ranked)[:limit]

    station_items: list[NearbyStationItem] = []
    for dist, st in chosen:
        st_name = str(st["name"])
        st_dist_name = str(st["district_name"] or resolved.name)
        phone_val = str(st["phone"]) if st.get("phone") else None
        hotline = str(st.get("hotline") or "102")
        subj, body = build_citizen_report_email(
            station_name=st_name,
            area_name=st_dist_name,
            lat=center_lat,
            lon=center_lon,
            threat=threat,
        )
        station_items.append(
            NearbyStationItem(
                station_id=str(st["station_id"]),
                name=st_name,
                district_id=str(st["district_id"]),
                district_name=st_dist_name,
                lat=float(st["lat"]),  # type: ignore[arg-type]
                lon=float(st["lon"]),  # type: ignore[arg-type]
                distance_km=round(dist, 1),
                hotline=hotline,
                national_emergency=str(st.get("national_emergency") or "999"),
                phone=phone_val,
                email=str(st["email"]) if st.get("email") else None,
                dial_number=phone_val or hotline,
                email_subject=subj,
                email_body=body,
            )
        )

    return NearbyStationsEnvelope(
        data=NearbyStationsData(
            center_lat=round(center_lat, 5),
            center_lon=round(center_lon, 5),
            location_source=loc_source,
            area_id=resolved.area_id,
            area_name=resolved.name,
            threat=ThreatSummary(
                level=threat.level,
                headline=threat.headline,
                explanation=threat.explanation,
                nearby_recent_events=nearby_events,
            ),
            stations=station_items,
        ),
        meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
    )
