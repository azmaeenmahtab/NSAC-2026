"""Unit and integration tests for A06 guidance and Wildland Action Planner."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.features.calendar.schemas import FireSeason
from app.features.guidance.repository import (
    clear_guidance_cache,
    filter_guidance_items,
    get_all_guidance_items,
    load_guidance_items,
)
from app.features.guidance.rules import stage_for
from app.features.guidance.schemas import GuidanceItem
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
REFERENCE_DIR = REPO_ROOT / "data" / "reference"


@pytest.fixture
def client() -> TestClient:
    """Create fresh TestClient pointing to test fixtures and reference data."""
    clear_guidance_cache()
    cfg = Settings(
        data_dir=str(FIXTURES_DIR),
        reference_dir=str(REFERENCE_DIR),
        web_origin="http://localhost:3000",
        rate_limit_default="120/minute",
    )
    return TestClient(create_app(cfg))


# ---------------------------------------------------------------------------
# 1. Pure Engine Tests (The 5 Hand-Verified Fixtures from A06-guidance.md)
# ---------------------------------------------------------------------------


def test_hand_verified_fixture_1_pre_season() -> None:
    """Season start 3, end 5: month 2 -> pre_season (month before start)."""
    season = FireSeason(start_month=3, peak_month=4, end_month=5, share_of_annual=0.8)
    assert stage_for(month=2, season=season, latest_class="normal") == "pre_season"


def test_hand_verified_fixture_2_in_season() -> None:
    """Season start 3, end 5: month 4 -> in_season (inside season window)."""
    season = FireSeason(start_month=3, peak_month=4, end_month=5, share_of_annual=0.8)
    assert stage_for(month=4, season=season, latest_class="normal") == "in_season"


def test_hand_verified_fixture_3_post_season() -> None:
    """Season start 3, end 5: month 6 -> post_season (month after end)."""
    season = FireSeason(start_month=3, peak_month=4, end_month=5, share_of_annual=0.8)
    assert stage_for(month=6, season=season, latest_class="normal") == "post_season"


def test_hand_verified_fixture_4_extreme() -> None:
    """Season start 3, end 5: month 9 with latest class 'extreme' -> extreme."""
    season = FireSeason(start_month=3, peak_month=4, end_month=5, share_of_annual=0.8)
    assert stage_for(month=9, season=season, latest_class="extreme") == "extreme"


def test_hand_verified_fixture_5_off_season() -> None:
    """Season start 3, end 5: month 9 with normal class -> off_season."""
    season = FireSeason(start_month=3, peak_month=4, end_month=5, share_of_annual=0.8)
    assert stage_for(month=9, season=season, latest_class="normal") == "off_season"


def test_rules_circular_year_wrap() -> None:
    """Circular calendar arithmetic: Jan start has Dec pre_season; cross-year season."""
    # Season start in Jan (1) -> pre_season is Dec (12)
    jan_season = FireSeason(start_month=1, peak_month=2, end_month=3, share_of_annual=0.7)
    assert stage_for(month=12, season=jan_season) == "pre_season"
    assert stage_for(month=1, season=jan_season) == "in_season"
    assert stage_for(month=4, season=jan_season) == "post_season"

    # Cross-year season: Nov (11) to Feb (2)
    winter_season = FireSeason(start_month=11, peak_month=12, end_month=2, share_of_annual=0.7)
    assert stage_for(month=10, season=winter_season) == "pre_season"
    assert stage_for(month=11, season=winter_season) == "in_season"
    assert stage_for(month=1, season=winter_season) == "in_season"
    assert stage_for(month=2, season=winter_season) == "in_season"
    assert stage_for(month=3, season=winter_season) == "post_season"
    assert stage_for(month=7, season=winter_season) == "off_season"


def test_rules_invalid_month_raises() -> None:
    """Invalid month must raise ValueError."""
    season = FireSeason(start_month=3, peak_month=4, end_month=5, share_of_annual=0.8)
    with pytest.raises(ValueError, match="month must be an integer between 1 and 12"):
        stage_for(month=0, season=season)
    with pytest.raises(ValueError, match="month must be an integer between 1 and 12"):
        stage_for(month=13, season=season)


# ---------------------------------------------------------------------------
# 2. Reference Content Tests (data/reference/guidance.json)
# ---------------------------------------------------------------------------


def test_guidance_json_content() -> None:
    """guidance.json contains 10-20 items, all valid schema, covering all stages & audiences."""
    guidance_file = REFERENCE_DIR / "guidance.json"
    assert guidance_file.exists(), f"Missing {guidance_file}"

    items = load_guidance_items(guidance_file)
    assert 10 <= len(items) <= 20, f"Expected 10-20 items, got {len(items)}"

    stages = {item.stage for item in items}
    expected_stages = {"pre_season", "in_season", "post_season", "extreme", "off_season"}
    assert stages == expected_stages, f"Missing stages: {expected_stages - stages}"

    audiences = {item.audience for item in items}
    assert {"community", "land_manager", "responder"}.issubset(audiences)

    for item in items:
        assert isinstance(item, GuidanceItem)
        assert item.id.startswith("g-")
        assert len(item.text) > 10
        assert item.source_title is not None and len(item.source_title) > 0
        assert item.source_url is not None and item.source_url.startswith("http")
        assert isinstance(item.verified, bool)


def test_repository_filtering() -> None:
    """filter_guidance_items filters correctly by stage and audience."""
    all_items = get_all_guidance_items()
    assert len(all_items) >= 10

    pre_items = filter_guidance_items(all_items, stage="pre_season")
    assert all(item.stage == "pre_season" for item in pre_items)
    assert len(pre_items) > 0

    comm_items = filter_guidance_items(pre_items, audience="community")
    assert all(item.audience == "community" for item in comm_items)
    assert len(comm_items) > 0


# ---------------------------------------------------------------------------
# 3. API Endpoint Tests (GET /api/guidance)
# ---------------------------------------------------------------------------


def test_get_guidance_alpha_default_month(client: TestClient) -> None:
    """GET /api/guidance with area_id returns stage and items envelope."""
    res = client.get("/api/guidance", params={"area_id": "BGD-ADM2-alpha"})
    assert res.status_code == 200
    payload = res.json()

    assert "data" in payload
    assert "meta" in payload
    assert payload["meta"]["dataVersion"] == "v0.1.0-fixtures"
    assert payload["meta"]["asOf"] == "2025-12-31"
    assert "stage" in payload["meta"]
    assert "advisory" in payload["meta"]["disclaimer"].lower()

    items = payload["data"]
    assert isinstance(items, list)
    for item in items:
        assert "id" in item
        assert "stage" in item
        assert "audience" in item
        assert "text" in item
        assert "verified" in item


def test_get_guidance_seasonal_transitions(client: TestClient) -> None:
    """Test seasonal stages for alpha (season start=4, peak=5, end=6)."""
    # Month 3 is pre_season for season starting in April (4)
    res_pre = client.get("/api/guidance", params={"area_id": "BGD-ADM2-alpha", "month": 3})
    assert res_pre.status_code == 200
    assert res_pre.json()["meta"]["stage"] == "pre_season"
    assert all(i["stage"] == "pre_season" for i in res_pre.json()["data"])

    # Month 5 is in_season
    res_in = client.get("/api/guidance", params={"area_id": "BGD-ADM2-alpha", "month": 5})
    assert res_in.status_code == 200
    assert res_in.json()["meta"]["stage"] == "in_season"
    assert all(i["stage"] == "in_season" for i in res_in.json()["data"])

    # Month 7 is post_season
    res_post = client.get("/api/guidance", params={"area_id": "BGD-ADM2-alpha", "month": 7})
    assert res_post.status_code == 200
    assert res_post.json()["meta"]["stage"] == "post_season"
    assert all(i["stage"] == "post_season" for i in res_post.json()["data"])

    # Month 10 is off_season
    res_off = client.get("/api/guidance", params={"area_id": "BGD-ADM2-alpha", "month": 10})
    assert res_off.status_code == 200
    assert res_off.json()["meta"]["stage"] == "off_season"
    assert all(i["stage"] == "off_season" for i in res_off.json()["data"])


def test_get_guidance_stage_override(client: TestClient) -> None:
    """Explicit stage override returns requested stage checklist."""
    res = client.get("/api/guidance", params={"area_id": "BGD-ADM2-alpha", "stage": "extreme"})
    assert res.status_code == 200
    assert res.json()["meta"]["stage"] == "extreme"
    assert all(i["stage"] == "extreme" for i in res.json()["data"])


def test_get_guidance_audience_filtering(client: TestClient) -> None:
    """Filter by audience returns only matching audience items."""
    res = client.get(
        "/api/guidance",
        params={"area_id": "BGD-ADM2-alpha", "month": 5, "audience": "responder"},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) > 0
    assert all(i["audience"] == "responder" for i in data)


def test_get_guidance_not_found_area(client: TestClient) -> None:
    """Unknown area ID returns 404."""
    res = client.get("/api/guidance", params={"area_id": "UNKNOWN-9999"})
    assert res.status_code == 404


def test_get_guidance_invalid_month(client: TestClient) -> None:
    """Month out of bounds (0 or 13) returns 400 validation error."""
    res = client.get("/api/guidance", params={"area_id": "BGD-ADM2-alpha", "month": 13})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"
