"""Unit and integration tests for A03 calendar, yearly stats, anomalies, and methodology."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.features.calendar.service import clear_calendar_cache
from app.features.methodology.service import METHODOLOGY_LIMITATIONS, clear_methodology_cache
from app.features.stats.service import clear_stats_cache
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
REFERENCE_DIR = REPO_ROOT / "data" / "reference"


@pytest.fixture
def client() -> TestClient:
    """Create a fresh TestClient bound to `data/fixtures` with cleared LRU caches."""
    clear_calendar_cache()
    clear_stats_cache()
    clear_methodology_cache()
    cfg = Settings(
        data_dir=str(FIXTURES_DIR),
        reference_dir=str(REFERENCE_DIR),
        web_origin="http://localhost:3000",
        rate_limit_default="120/minute",
    )
    return TestClient(create_app(cfg))


def test_calendar_alpha_season_and_extreme_anomaly(client: TestClient) -> None:
    """Fixture calendar for alpha: season start 4, peak 5, end 6, share ~0.7059; 2020-05 is extreme."""
    res = client.get("/api/calendar", params={"area_id": "BGD-ADM2-alpha"})
    assert res.status_code == 200
    payload = res.json()
    assert payload["meta"]["dataVersion"] == "v0.1.0-fixtures"

    data = payload["data"]

    # Season check: start 4, peak 5, end 6, share ~0.7059
    season = data["season"]
    assert season["start_month"] == 4
    assert season["peak_month"] == 5
    assert season["end_month"] == 6
    assert season["share_of_annual"] == pytest.approx(24.0 / 34.0, abs=1e-3)

    # Climatology check: 12 calendar months
    climatology = data["climatology"]
    assert len(climatology) == 12
    assert [c["month"] for c in climatology] == list(range(1, 13))

    # Grid check: 2020-05 cell must be 'extreme' with value 200.0 and percentile_rank 1.0
    grid = data["grid"]
    by_ym = {(c["year"], c["month"]): c for c in grid}

    cell_2020_05 = by_ym[(2020, 5)]
    assert cell_2020_05["value"] == pytest.approx(200.0, abs=1e-4)
    assert cell_2020_05["class"] == "extreme"
    assert cell_2020_05["percentile_rank"] == pytest.approx(1.0, abs=1e-4)

    # Normal month check: 2020-04 is normal
    cell_2020_04 = by_ym[(2020, 4)]
    assert cell_2020_04["class"] == "normal"


def test_yearly_stats_ranks_and_vs_mean_pct(client: TestClient) -> None:
    """Yearly ranks and vs_mean_pct match fixture values."""
    res = client.get("/api/stats/yearly", params={"area_id": "BGD-ADM2-alpha"})
    assert res.status_code == 200
    payload = res.json()
    rows = payload["data"]
    assert len(rows) == 25  # complete years 2001-2025

    by_year = {r["year"]: r for r in rows}

    # 2020 has rank 1 and vs_mean_pct > 0
    row_2020 = by_year[2020]
    assert row_2020["rank"] == 1
    assert row_2020["harmonized_total"] == pytest.approx(440.0, abs=1e-4)
    assert row_2020["vs_mean_pct"] > 0.0
    assert row_2020["peak_month"] == 5

    # 2019 is a baseline year with rank 2 and vs_mean_pct == 0.0
    row_2019 = by_year[2019]
    assert row_2019["rank"] == 2
    assert row_2019["harmonized_total"] == pytest.approx(340.0, abs=1e-4)
    assert row_2019["vs_mean_pct"] == pytest.approx(0.0, abs=1e-4)


def test_anomalies_filtering(client: TestClient) -> None:
    """Anomalies endpoint filters properly by year and class."""
    # Filter by class='extreme': in fixture, only 2020-05 is extreme for alpha
    res_extreme = client.get(
        "/api/anomalies",
        params={"area_id": "BGD-ADM2-alpha", "class": "extreme"},
    )
    assert res_extreme.status_code == 200
    items = res_extreme.json()["data"]
    assert len(items) == 1
    assert items[0]["year"] == 2020
    assert items[0]["month"] == 5
    assert items[0]["class"] == "extreme"

    # Filter by year=2021: all 12 months are normal
    res_2021 = client.get(
        "/api/anomalies",
        params={"area_id": "BGD-ADM2-alpha", "year": 2021},
    )
    assert res_2021.status_code == 200
    items_2021 = res_2021.json()["data"]
    assert len(items_2021) == 12
    assert all(it["class"] == "normal" for it in items_2021)


def test_methodology_keys_and_limitations(client: TestClient) -> None:
    """Methodology payload contains all required keys and limitations list is unchanged from brief."""
    res = client.get("/api/methodology")
    assert res.status_code == 200
    payload = res.json()
    data = payload["data"]

    assert "parameters" in data
    assert "jump_metrics" in data
    assert "limitations" in data
    assert "calibration_summary" in data

    jump = data["jump_metrics"]
    # 2012-2016 has 59 months of VIIRS (3x) and Jan 2012 MODIS (1x) -> naive ratio = 7620/2550 = 2.9882
    assert jump["naive_ratio"] == pytest.approx(2.988, abs=0.02)
    assert jump["harmonized_ratio"] == pytest.approx(1.0, abs=1e-2)

    limitations = data["limitations"]
    assert len(limitations) == 6
    assert limitations == list(METHODOLOGY_LIMITATIONS)
    assert any("MODIS-equivalent fire events" in s for s in limitations)


def test_validation_and_404_errors(client: TestClient) -> None:
    """Validation errors on bbox stubs, bad class filter, and 404 for unknown area."""
    # Bbox queries return 400 validation error explaining D07 prerequisite
    res_bbox = client.get("/api/calendar", params={"area_id": "bbox:88.0,20.5,92.8,26.7"})
    assert res_bbox.status_code == 400
    assert "Custom bbox" in res_bbox.json()["error"]["message"]

    res_bbox_stats = client.get("/api/stats/yearly", params={"area_id": "bbox:88.0,20.5,92.8,26.7"})
    assert res_bbox_stats.status_code == 400

    # 404 on unknown area
    res_404 = client.get("/api/calendar", params={"area_id": "nonexistent-area"})
    assert res_404.status_code == 404

    # Bad class filter on anomalies
    res_bad_class = client.get(
        "/api/anomalies",
        params={"area_id": "BGD", "class": "catastrophic"},
    )
    assert res_bad_class.status_code == 400
