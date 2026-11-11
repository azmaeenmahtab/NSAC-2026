"""Comprehensive tests for A01 API foundation, data loading, meta, and areas."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.dataset import DatasetLoadError, load_dataset
from app.features.areas.service import resolve_area
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
REFERENCE_DIR = REPO_ROOT / "data" / "reference"
OPENAPI_CONTRACT_PATH = REPO_ROOT / "contracts" / "openapi.yaml"


@pytest.fixture
def client() -> TestClient:
    """Create a fresh TestClient bound to `data/fixtures`."""
    cfg = Settings(
        data_dir=str(FIXTURES_DIR),
        reference_dir=str(REFERENCE_DIR),
        web_origin="http://localhost:3000",
        rate_limit_default="120/minute",
    )
    return TestClient(create_app(cfg))


def test_health_meta_and_areas_endpoints(client: TestClient) -> None:
    """Verify `/api/health`, `/api/meta`, and `/api/areas` match the OpenAPI contract."""
    # 1. Health
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    body_health = res_health.json()
    assert body_health["status"] == "healthy"
    assert body_health["service"] == "PyroScope API"
    assert body_health["version"] == "0.1.0"
    assert body_health["dataLoaded"] is True
    assert body_health["dataVersion"] == "v0.1.0-fixtures"

    # 2. Meta
    res_meta = client.get("/api/meta")
    assert res_meta.status_code == 200
    body_meta = res_meta.json()
    assert body_meta["meta"] == {
        "dataVersion": "v0.1.0-fixtures",
        "asOf": "2025-12-31",
    }
    meta_data = body_meta["data"]
    assert meta_data["dataVersion"] == "v0.1.0-fixtures"
    assert meta_data["asOf"] == "2025-12-31"
    assert meta_data["provisionalFrom"] is None
    assert "eps_spatial_meters" in meta_data["parametersSummary"]
    assert isinstance(meta_data["sources"], list) and len(meta_data["sources"]) == 1
    assert meta_data["counts"]["detections_raw"] == 10000
    assert "NASA" in meta_data["attribution"] and "FIRMS" in meta_data["attribution"]

    # 3. Areas (unfiltered and filtered by level)
    res_areas = client.get("/api/areas")
    assert res_areas.status_code == 200
    body_areas = res_areas.json()
    assert body_areas["meta"]["dataVersion"] == "v0.1.0-fixtures"
    items = body_areas["data"]
    assert len(items) == 3
    ids = [item["id"] for item in items]
    assert ids == ["BGD", "BGD-ADM2-alpha", "BGD-ADM2-beta"]

    res_country = client.get("/api/areas", params={"level": "country"})
    assert res_country.status_code == 200
    assert [a["id"] for a in res_country.json()["data"]] == ["BGD"]

    # Both `adm2` and `district` match the fixture district rows
    res_adm2 = client.get("/api/areas", params={"level": "adm2"})
    assert res_adm2.status_code == 200
    assert len(res_adm2.json()["data"]) == 2

    res_district = client.get("/api/areas", params={"level": "district"})
    assert res_district.status_code == 200
    assert len(res_district.json()["data"]) == 2


def test_bad_level_and_bad_bbox_return_400_error_envelope(client: TestClient) -> None:
    """Verify invalid `level` and invalid `bbox` return 400 with `{ error: { code, message, requestId } }`."""
    res_bad_level = client.get("/api/areas", params={"level": "continent"}, headers={"X-Request-ID": "req-test-400"})
    assert res_bad_level.status_code == 400
    err_body = res_bad_level.json()
    assert "error" in err_body
    assert err_body["error"]["code"] == "VALIDATION_ERROR"
    assert err_body["error"]["requestId"] == "req-test-400"

    dataset = load_dataset(FIXTURES_DIR, reference_dir=REFERENCE_DIR)
    cursor = dataset.cursor()
    try:
        # Valid bbox resolves cleanly
        resolved_bbox = resolve_area(cursor, "bbox:88.0,20.5,92.8,26.7")
        assert resolved_bbox.kind == "bbox"
        assert resolved_bbox.bbox == (88.0, 20.5, 92.8, 26.7)

        # Bad bbox: west >= east
        with pytest.raises(Exception) as exc_w_e:
            resolve_area(cursor, "bbox:92.8,20.5,88.0,26.7")
        assert getattr(exc_w_e.value, "status_code", None) == 400

        # Bad bbox: out of range latitude
        with pytest.raises(Exception) as exc_range:
            resolve_area(cursor, "bbox:88.0,-95.0,92.8,26.7")
        assert getattr(exc_range.value, "status_code", None) == 400

        # Bad bbox: non-numeric
        with pytest.raises(Exception) as exc_nan:
            resolve_area(cursor, "bbox:88.0,abc,92.8,26.7")
        assert getattr(exc_nan.value, "status_code", None) == 400
    finally:
        cursor.close()
        dataset.connection.close()


def test_unknown_area_returns_404() -> None:
    """Verify resolving an unknown `area_id` raises a 404 `NotFoundAPIError`."""
    dataset = load_dataset(FIXTURES_DIR, reference_dir=REFERENCE_DIR)
    cursor = dataset.cursor()
    try:
        resolved_alpha = resolve_area(cursor, "BGD-ADM2-alpha")
        assert resolved_alpha.area_id == "BGD-ADM2-alpha"
        assert resolved_alpha.region_ids == ("BGD-ADM2-alpha",)

        with pytest.raises(Exception) as exc_404:
            resolve_area(cursor, "BGD-ADM2-nonexistent")
        assert getattr(exc_404.value, "status_code", None) == 404
        assert getattr(exc_404.value, "code", None) == "NOT_FOUND"
    finally:
        cursor.close()
        dataset.connection.close()


def test_cors_and_rate_limiting() -> None:
    """Verify CORS header is absent for disallowed origins and the 121st request returns 429."""
    cfg = Settings(
        data_dir=str(FIXTURES_DIR),
        reference_dir=str(REFERENCE_DIR),
        web_origin="http://localhost:3000",
        rate_limit_default="120/minute",
    )
    test_client = TestClient(create_app(cfg))

    # Allowed origin receives Access-Control-Allow-Origin
    res_allowed = test_client.get(
        "/api/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert res_allowed.status_code == 200
    assert res_allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"

    # Different origin does NOT receive Access-Control-Allow-Origin
    res_disallowed = test_client.get(
        "/api/health",
        headers={"Origin": "https://evil.example.com"},
    )
    assert res_disallowed.status_code == 200
    assert "access-control-allow-origin" not in res_disallowed.headers

    # Exhaust remaining 118 requests (2 already sent above -> 120 total)
    for _ in range(118):
        r = test_client.get("/api/health")
        assert r.status_code == 200

    # 121st request returns 429 with Retry-After and ErrorEnvelope
    res_121 = test_client.get("/api/health")
    assert res_121.status_code == 429
    assert "retry-after" in res_121.headers
    err = res_121.json()
    assert err["error"]["code"] == "RATE_LIMITED"
    assert "requestId" in err["error"]


def test_startup_fails_when_manifest_or_parquet_missing(tmp_path: Path) -> None:
    """Verify startup fails with a clear `DatasetLoadError` if `manifest.json` or a Parquet file is absent."""
    # Case 1: Empty directory without manifest.json
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(DatasetLoadError, match=r"Missing manifest\.json"):
        load_dataset(empty_dir)

    # Case 2: Copy fixtures but remove one required Parquet file (`seasons.parquet`)
    partial_dir = tmp_path / "partial"
    shutil.copytree(FIXTURES_DIR, partial_dir)
    (partial_dir / "seasons.parquet").unlink()

    with pytest.raises(DatasetLoadError, match=r"seasons\.parquet"):
        load_dataset(partial_dir)


def test_openapi_contract_matches_implemented_paths(client: TestClient) -> None:
    """Contract test: `/api/openapi.json` matches committed `contracts/openapi.yaml` for implemented paths."""
    res = client.get("/api/openapi.json")
    assert res.status_code == 200
    generated = res.json()

    committed = yaml.safe_load(OPENAPI_CONTRACT_PATH.read_text(encoding="utf-8"))
    committed_paths = committed["paths"]
    generated_paths = generated["paths"]

    implemented = [("/health", "/api/health"), ("/meta", "/api/meta"), ("/areas", "/api/areas")]
    for contract_path, route_path in implemented:
        assert contract_path in committed_paths
        assert route_path in generated_paths
        contract_get = committed_paths[contract_path]["get"]
        gen_get = generated_paths[route_path]["get"]
        assert gen_get["operationId"] == contract_get["operationId"]
        assert "200" in gen_get["responses"]

