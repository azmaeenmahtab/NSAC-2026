"""Tests for nearby fire stations, threat level assessment, and plain-English station alerts."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.features.alerts.evaluate import (
    compute_threat_level,
    format_activity_station_email,
    format_preseason_station_email,
)
from app.features.alerts.mailer import ConsoleMailer, set_mailer
from app.features.alerts.repository import get_sqlite_connection
from app.features.stations.service import haversine_km
from app.main import create_app
from scripts.send_alerts import evaluate_and_dispatch_alerts

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
REFERENCE_DIR = REPO_ROOT / "data" / "reference"
PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "current"


@pytest.fixture
def stations_client() -> TestClient:
    data_dir = PROCESSED_DIR if (PROCESSED_DIR / "manifest.json").is_file() else FIXTURES_DIR
    cfg = Settings(
        data_dir=str(data_dir),
        reference_dir=str(REFERENCE_DIR),
        web_origin="http://localhost:3000",
        rate_limit_default="120/minute",
    )
    return TestClient(create_app(cfg))


def test_haversine_km_pure() -> None:
    # Dhaka (23.8103, 90.4125) to Chattogram (22.3569, 91.7832) ~ 214 km
    dist = haversine_km(23.8103, 90.4125, 22.3569, 91.7832)
    assert 205.0 < dist < 225.0
    assert haversine_km(22.65, 92.18, 22.65, 92.18) == 0.0


def test_compute_threat_level_four_tiers() -> None:
    low = compute_threat_level(False, False, "normal", 0)
    assert low.level == "LOW"

    mod = compute_threat_level(True, False, "normal", 0)
    assert mod.level == "MODERATE"

    high_anom = compute_threat_level(False, True, "elevated", 0)
    assert high_anom.level == "HIGH"

    high_events = compute_threat_level(False, True, "normal", 2)
    assert high_events.level == "HIGH"

    crit_extreme = compute_threat_level(False, True, "extreme", 0)
    assert crit_extreme.level == "CRITICAL"

    crit_combo = compute_threat_level(False, True, "elevated", 3)
    assert crit_combo.level == "CRITICAL"


def test_plain_english_station_emails_have_no_jargon() -> None:
    risk_mod = compute_threat_level(True, False, "normal", 0)
    subj, body = format_preseason_station_email(
        recipient_label="Rangamati Fire Station Team",
        area_name="Rangamati",
        days_left=14,
        start_month=3,
        end_month=4,
        risk=risk_mod,
    )
    assert "[MODERATE Risk]" in subj
    assert "14 days" in body
    assert "ST-DBSCAN" not in body
    assert "p95" not in body

    risk_high = compute_threat_level(False, True, "elevated", 2)
    subj2, body2 = format_activity_station_email(
        recipient_label="Rangamati Fire Station Team",
        area_name="Rangamati",
        risk=risk_high,
        nearby_events=2,
        radius_km=25.0,
        center_lat=22.65,
        center_lon=92.18,
    )
    assert "[HIGH Risk]" in subj2
    assert "2 recent fire spot(s)" in body2
    assert "MODIS-equivalent" not in body2


def test_nearby_stations_endpoint_gps_and_fallback(stations_client: TestClient) -> None:
    # 1. With Rangamati GPS coordinates
    res = stations_client.get(
        "/api/stations/nearby",
        params={"lat": 22.65, "lon": 92.18, "area_id": "BGD", "limit": 3},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["location_source"] == "gps"
    assert len(data["stations"]) == 3
    assert data["stations"][0]["distance_km"] <= data["stations"][1]["distance_km"]
    assert data["stations"][0]["dial_number"] == "102"
    assert "Risk]" in data["stations"][0]["email_subject"]
    assert data["threat"]["level"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")

    # 2. Without GPS (selected area fallback)
    area_id = "PRESET-CHT" if (PROCESSED_DIR / "manifest.json").is_file() else "BGD"
    res2 = stations_client.get("/api/stations/nearby", params={"area_id": area_id, "limit": 2})
    assert res2.status_code == 200
    assert res2.json()["data"]["location_source"] == "selected_area"
    assert len(res2.json()["data"]["stations"]) == 2

    # 3. Outside Bangladesh GPS falls back to selected area
    res3 = stations_client.get(
        "/api/stations/nearby",
        params={"lat": 40.71, "lon": -74.0, "area_id": area_id},
    )
    assert res3.status_code == 200
    assert res3.json()["data"]["location_source"] == "area_fallback_outside_bd"

    # 4. Partial lat without lon -> 400 validation error
    res4 = stations_client.get("/api/stations/nearby", params={"lat": 22.65})
    assert res4.status_code == 400


def test_fire_station_subscription_and_plain_dispatch(tmp_path: Path) -> None:
    db_path = tmp_path / "stations_alerts.db"
    get_sqlite_connection(db_path)
    mailer = ConsoleMailer()
    set_mailer(mailer)

    cfg = Settings(
        data_dir=str(FIXTURES_DIR),
        reference_dir=str(REFERENCE_DIR),
        web_origin="http://localhost:3000",
        app_db_path=str(db_path),
        rate_limit_default="120/minute",
    )
    client = TestClient(create_app(cfg))

    res = client.post(
        "/api/alerts/subscriptions",
        json={
            "email": "rangamati-station@fireservice.gov.bd",
            "area_id": "BGD-ADM2-alpha",
            "rule": "both",
            "lead_days": 14,
            "subscriber_type": "fire_station",
            "station_id": "FSCD-node-5776723114",
            "station_name": "Rangamati Fire Station",
            "phone": "01730-000000",
            "radius_km": 25.0,
        },
    )
    assert res.status_code == 200
    token = mailer.sent_messages[0]["token"]
    assert (
        client.get("/api/alerts/subscriptions/confirm", params={"token": token}).status_code == 200
    )

    # Alpha has season start month 4 and extreme anomaly in 2020-05
    summary = evaluate_and_dispatch_alerts(
        data_dir=FIXTURES_DIR,
        reference_dir=REFERENCE_DIR,
        db_path=db_path,
        today_override=date(2020, 5, 15),
    )
    assert summary["notifications_sent"] >= 1
    alerts = [m for m in mailer.sent_messages if m["type"] == "alert"]
    assert alerts
    assert "[CRITICAL Risk]" in alerts[0]["subject"]
    assert "Rangamati Fire Station Team" in alerts[0]["body"]
