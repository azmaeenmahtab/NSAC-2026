"""Integration smoke tests for S02 deployment and offline fallback verification."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
REFERENCE_DIR = REPO_ROOT / "data" / "reference"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    """Create a fresh TestClient bound to `data/fixtures` with replay provider and SQLite db."""
    app_db = tmp_path / "app.db"
    cfg = Settings(
        data_dir=str(FIXTURES_DIR),
        reference_dir=str(REFERENCE_DIR),
        web_origin="http://localhost:3000",
        llm_provider="replay",
        app_db_path=str(app_db),
        rate_limit_default="120/minute",
    )
    return TestClient(create_app(cfg))


def test_s02_smoke_suite_passes(client: TestClient) -> None:
    """Execute the canonical 5-point deployment smoke test suite."""
    # 1. Health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    body_health = res_health.json()
    assert body_health["status"] == "healthy"
    assert body_health["dataLoaded"] is True
    assert "dataVersion" in body_health

    # 2. Meta parameters & attribution
    res_meta = client.get("/api/meta")
    assert res_meta.status_code == 200
    body_meta = res_meta.json()
    assert "dataVersion" in body_meta["data"]
    assert "attribution" in body_meta["data"]
    assert len(body_meta["data"]["sources"]) > 0

    # 3. Heatmap aggregation
    res_heatmap = client.get(
        "/api/heatmap",
        params={
            "bbox": "88.0,20.5,92.8,26.7",
            "from": "2020-05",
            "to": "2020-05",
            "metric": "harmonized",
            "res": 7,
        },
    )
    assert res_heatmap.status_code == 200
    body_heatmap = res_heatmap.json()
    assert len(body_heatmap["data"]["cells"]) > 0
    assert "stats" in body_heatmap["data"]

    # 4. FireCalendar & seasonal stats
    res_cal = client.get("/api/calendar", params={"area_id": "BGD-ADM2-alpha"})
    assert res_cal.status_code == 200
    body_cal = res_cal.json()
    assert len(body_cal["data"]["grid"]) > 0
    assert "season" in body_cal["data"]
    assert body_cal["data"]["season"]["start_month"] == 4

    # 5. Ask Assistant in offline replay mode
    res_ask = client.post(
        "/api/ask",
        json={
            "question": "When does fire season start in alpha and was 2020 unusual?",
            "area_id": "BGD-ADM2-alpha",
        },
    )
    assert res_ask.status_code == 200
    body_ask = res_ask.json()
    assert body_ask["data"]["mode"] == "replay"
    assert "April" in body_ask["data"]["answer"] or "month 4" in body_ask["data"]["answer"]
    assert len(body_ask["data"]["toolCalls"]) > 0


def test_s02_cors_and_origin_policy(client: TestClient) -> None:
    """Verify CORS headers only permit the configured WEB_ORIGIN."""
    # Permitted origin
    res_allowed = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert res_allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"

    # Disallowed origin
    res_disallowed = client.get(
        "/api/health",
        headers={"Origin": "http://evil-origin.com"},
    )
    assert res_disallowed.headers.get("access-control-allow-origin") is None
