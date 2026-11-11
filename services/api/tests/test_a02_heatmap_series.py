"""Unit and integration tests for A02 `/api/heatmap` and `/api/series` endpoints."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import h3
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.dataset import load_dataset
from app.features.heatmap.service import clear_heatmap_cache, get_heatmap_envelope
from app.features.series.service import clear_series_cache, get_series_envelope
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
REFERENCE_DIR = REPO_ROOT / "data" / "reference"


@pytest.fixture
def client() -> TestClient:
    """Create a fresh TestClient bound to `data/fixtures` with cleared LRU caches."""
    clear_heatmap_cache()
    clear_series_cache()
    cfg = Settings(
        data_dir=str(FIXTURES_DIR),
        reference_dir=str(REFERENCE_DIR),
        web_origin="http://localhost:3000",
        rate_limit_default="120/minute",
    )
    return TestClient(create_app(cfg))


def test_heatmap_200_cells_conservation_and_hex_validity(client: TestClient) -> None:
    """Fixture heatmap for the 200 cells: sum equals fixture district totals and hex IDs are valid."""
    # For 2020-05 in S01 fixture: alpha=200.0, beta=100.0 -> total BGD=300.0
    res = client.get(
        "/api/heatmap",
        params={
            "bbox": "88.0,20.5,92.8,26.7",
            "from": "2020-05",
            "to": "2020-05",
            "metric": "harmonized",
            "res": 7,
        },
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["meta"]["dataVersion"] == "v0.1.0-fixtures"

    data = payload["data"]
    assert data["res"] == 7
    assert data["metric"] == "harmonized"
    assert data["from"] == "2020-05"
    assert data["to"] == "2020-05"

    cells = data["cells"]
    assert len(cells) == 200

    total_val = sum(c["value"] for c in cells)
    assert total_val == pytest.approx(300.0, abs=1e-5)

    for c in cells:
        hex_str = c["h3"]
        assert isinstance(hex_str, str)
        assert len(hex_str) == 15
        assert hex_str == hex_str.lower()
        assert h3.is_valid_cell(hex_str)
        assert h3.get_resolution(hex_str) == 7

    # Also verify full-year 2021 (normal year): alpha=340.0, beta=170.0 -> BGD=510.0
    res_2021 = client.get(
        "/api/heatmap",
        params={
            "bbox": "88.0,20.5,92.8,26.7",
            "from": "2021-01",
            "to": "2021-12",
            "metric": "harmonized",
            "res": 7,
        },
    )
    assert res_2021.status_code == 200
    cells_2021 = res_2021.json()["data"]["cells"]
    assert len(cells_2021) == 200
    assert sum(c["value"] for c in cells_2021) == pytest.approx(510.0, abs=1e-4)


def test_heatmap_res_5_and_6_aggregate_to_parents_and_conserve_total(client: TestClient) -> None:
    """Resolutions 5 and 6 aggregate to parent H3 cells and their sums equal the r7 total."""
    params_base = {
        "bbox": "88.0,20.5,92.8,26.7",
        "from": "2020-01",
        "to": "2020-12",
        "metric": "harmonized",
    }
    r7 = client.get("/api/heatmap", params={**params_base, "res": 7}).json()["data"]["cells"]
    r6 = client.get("/api/heatmap", params={**params_base, "res": 6}).json()["data"]["cells"]
    r5 = client.get("/api/heatmap", params={**params_base, "res": 5}).json()["data"]["cells"]

    sum_r7 = sum(c["value"] for c in r7)
    sum_r6 = sum(c["value"] for c in r6)
    sum_r5 = sum(c["value"] for c in r5)

    assert len(r6) < len(r7)
    assert len(r5) <= len(r6)
    assert sum_r6 == pytest.approx(sum_r7, abs=1e-4)
    assert sum_r5 == pytest.approx(sum_r7, abs=1e-4)

    for c6 in r6:
        assert len(c6["h3"]) == 15
        assert h3.is_valid_cell(c6["h3"])
        assert h3.get_resolution(c6["h3"]) == 6

    for c5 in r5:
        assert len(c5["h3"]) == 15
        assert h3.is_valid_cell(c5["h3"])
        assert h3.get_resolution(c5["h3"]) == 5


def test_series_naive_splice_3x_jump_vs_flat_harmonized(client: TestClient) -> None:
    """Series `naive_splice` equals MODIS before 2012-02 and raw VIIRS (3x) after, while harmonized does not jump."""
    res = client.get(
        "/api/series",
        params={"area_id": "BGD", "from": "2011-01", "to": "2013-12"},
    )
    assert res.status_code == 200
    points = res.json()["data"]
    assert len(points) == 36

    by_ym = {(p["year"], p["month"]): p for p in points}

    # Before 2012-02 (e.g. 2012-01): in_overlap is False, raw_viirs is None, naive_splice == raw_modis == harmonized
    jan_2012 = by_ym[(2012, 1)]
    assert jan_2012["in_overlap"] is False
    assert jan_2012["raw_viirs"] is None
    assert jan_2012["source_used"] == "modis_raw"
    assert jan_2012["naive_splice"] == pytest.approx(jan_2012["raw_modis"], abs=1e-6)
    assert jan_2012["harmonized"] == pytest.approx(jan_2012["raw_modis"], abs=1e-6)

    # Compare May 2011 (pre-VIIRS) vs May 2012 (overlap: VIIRS = 3 x MODIS)
    may_2011 = by_ym[(2011, 5)]
    may_2012 = by_ym[(2012, 5)]
    assert may_2012["in_overlap"] is True
    assert may_2012["source_used"] == "viirs_calibrated"
    assert may_2012["raw_viirs"] == pytest.approx(3.0 * may_2012["raw_modis"], abs=1e-6)
    assert may_2012["naive_splice"] == pytest.approx(may_2012["raw_viirs"], abs=1e-6)

    # Naive splice jumps 3x between May 2011 and May 2012, whereas harmonized stays equal (1x)
    assert may_2012["naive_splice"] / may_2011["naive_splice"] == pytest.approx(3.0, abs=1e-6)
    assert may_2012["harmonized"] / may_2011["harmonized"] == pytest.approx(1.0, abs=1e-6)

    # Custom bbox covering all fixture cells reproduces the BGD series
    res_bbox = client.get(
        "/api/series",
        params={"area_id": "bbox:88.0,20.5,92.8,26.7", "from": "2011-05", "to": "2012-05"},
    )
    assert res_bbox.status_code == 200
    bbox_pts = {(p["year"], p["month"]): p for p in res_bbox.json()["data"]}
    assert bbox_pts[(2011, 5)]["harmonized"] == pytest.approx(may_2011["harmonized"], abs=1e-4)
    assert bbox_pts[(2012, 5)]["naive_splice"] == pytest.approx(may_2012["naive_splice"], abs=1e-4)


def test_validation_errors_on_heatmap_and_series(client: TestClient) -> None:
    """Bad dates, `from` after `to`, bad metric, bad res, and exceeding max_cells return 400."""
    # Bad date format
    assert (
        client.get("/api/heatmap", params={"bbox": "88,20,92,26", "from": "2020/01", "to": "2020-12"}).status_code
        == 400
    )

    # `from` after `to`
    assert (
        client.get("/api/heatmap", params={"bbox": "88,20,92,26", "from": "2022-05", "to": "2021-05"}).status_code
        == 400
    )
    assert (
        client.get("/api/series", params={"area_id": "BGD", "from": "2022-05", "to": "2021-05"}).status_code
        == 400
    )

    # Bad metric
    assert (
        client.get("/api/heatmap", params={"bbox": "88,20,92,26", "metric": "burned_area"}).status_code
        == 400
    )

    # Bad resolution
    assert (
        client.get("/api/heatmap", params={"bbox": "88,20,92,26", "res": 9}).status_code
        == 400
    )

    # Exceeding max_cells cap raises 400 ValidationAPIError
    dataset = load_dataset(FIXTURES_DIR, reference_dir=REFERENCE_DIR)
    cursor = dataset.cursor()
    try:
        with pytest.raises(Exception) as exc_cap:
            get_heatmap_envelope(
                dataset=dataset,
                cursor=cursor,
                bbox_str="88.0,20.5,92.8,26.7",
                from_str="2020-05",
                to_str="2020-05",
                metric="harmonized",
                res=7,
                max_cells=50,
            )
        assert getattr(exc_cap.value, "status_code", None) == 400
        assert "exceeding maximum" in str(exc_cap.value)
    finally:
        cursor.close()
        dataset.connection.close()


def test_lru_cache_returns_identical_payloads_and_isolates_data_versions() -> None:
    """Cache returns identical payloads for the same version and does not leak across data versions."""
    clear_heatmap_cache()
    clear_series_cache()
    ds_v1 = load_dataset(FIXTURES_DIR, reference_dir=REFERENCE_DIR)
    ds_v2 = replace(ds_v1, data_version="v0.2.0-other")
    cursor = ds_v1.cursor()
    try:
        hm1 = get_heatmap_envelope(ds_v1, cursor, "88.0,20.5,92.8,26.7", "2020-05", "2020-05")
        hm1_cached = get_heatmap_envelope(ds_v1, cursor, "88.0,20.5,92.8,26.7", "2020-05", "2020-05")
        assert hm1 is hm1_cached

        hm2 = get_heatmap_envelope(ds_v2, cursor, "88.0,20.5,92.8,26.7", "2020-05", "2020-05")
        assert hm2 is not hm1
        assert hm2.meta.dataVersion == "v0.2.0-other"
        assert hm1.meta.dataVersion == "v0.1.0-fixtures"

        sr1 = get_series_envelope(ds_v1, cursor, "BGD", "2020-01", "2020-12")
        sr1_cached = get_series_envelope(ds_v1, cursor, "BGD", "2020-01", "2020-12")
        assert sr1 is sr1_cached

        sr2 = get_series_envelope(ds_v2, cursor, "BGD", "2020-01", "2020-12")
        assert sr2 is not sr1
        assert sr2.meta.dataVersion == "v0.2.0-other"
    finally:
        cursor.close()
        ds_v1.connection.close()
