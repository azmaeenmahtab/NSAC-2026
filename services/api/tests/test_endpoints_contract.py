"""End-to-end contract and smoke verification across all 15 PyroScope API endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.features.alerts.mailer import ConsoleMailer, set_mailer
from app.features.alerts.repository import get_sqlite_connection, get_subscription_by_token
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
REFERENCE_DIR = REPO_ROOT / "data" / "reference"
OPENAPI_CONTRACT_PATH = REPO_ROOT / "contracts" / "openapi.yaml"


@pytest.fixture
def endpoint_client(tmp_path: Path) -> tuple[TestClient, Path]:
    """Create isolated FastAPI TestClient backed by fixture Parquet tables and temp SQLite."""
    db_path = tmp_path / "endpoints_test.db"
    get_sqlite_connection(db_path)
    set_mailer(ConsoleMailer())
    cfg = Settings(
        data_dir=str(FIXTURES_DIR),
        reference_dir=str(REFERENCE_DIR),
        web_origin="http://localhost:3000",
        app_db_path=str(db_path),
        rate_limit_default="1000/minute",
    )
    app = create_app(cfg)
    return TestClient(app), db_path


def test_all_openapi_operations_match_fastapi(endpoint_client: tuple[TestClient, Path]) -> None:
    """Verify complete 1:1 symmetry between `contracts/openapi.yaml` and `/api/openapi.json`."""
    client, _ = endpoint_client
    res = client.get("/api/openapi.json")
    assert res.status_code == 200
    generated = res.json()["paths"]

    committed = yaml.safe_load(OPENAPI_CONTRACT_PATH.read_text(encoding="utf-8"))["paths"]
    contract_ops: dict[tuple[str, str], str] = {}
    for path, methods in committed.items():
        api_path = path if path.startswith("/api") else f"/api{path}"
        for method, spec in methods.items():
            if method.lower() in {"get", "post", "put", "delete", "patch"}:
                contract_ops[(api_path, method.lower())] = spec["operationId"]

    fastapi_ops: dict[tuple[str, str], str] = {}
    for path, methods in generated.items():
        for method, spec in methods.items():
            if method.lower() in {"get", "post", "put", "delete", "patch"}:
                fastapi_ops[(path, method.lower())] = spec["operationId"]

    assert set(contract_ops.keys()) == set(fastapi_ops.keys())
    for key, expected_op_id in contract_ops.items():
        assert fastapi_ops[key] == expected_op_id, f"operationId mismatch on {key}"


def test_all_15_endpoints_live_and_frontend_compatible(
    endpoint_client: tuple[TestClient, Path],
) -> None:
    """Verify every endpoint succeeds with expected envelopes and frontend query variants."""
    client, db_path = endpoint_client

    # 1. GET /api/health
    r_health = client.get("/api/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"
    assert r_health.json()["dataLoaded"] is True

    # 2. GET /api/meta
    r_meta = client.get("/api/meta")
    assert r_meta.status_code == 200
    assert r_meta.json()["data"]["dataVersion"]

    # 3. GET /api/areas
    r_areas = client.get("/api/areas")
    assert r_areas.status_code == 200
    assert len(r_areas.json()["data"]) >= 3

    # 4. GET /api/heatmap (bbox, area region, and custom bbox: prefix)
    heatmap_cases: list[dict[str, str | int]] = [
        {"bbox": "88.0,20.5,92.8,26.7", "res": 6},
        {"area": "BGD-ADM2-alpha", "from": "2020-01", "to": "2020-12", "res": 7},
        {"area": "bbox:88.0,20.5,92.8,26.7", "res": 6},
    ]
    for hm_params in heatmap_cases:
        r_hm = client.get("/api/heatmap", params=hm_params)
        assert r_hm.status_code == 200, f"heatmap failed with {hm_params}: {r_hm.text}"
        stats = r_hm.json()["data"]["stats"]
        for key in ("min", "p50", "p95", "max", "sum", "count"):
            assert key in stats

    # 5. GET /api/series (area_id and area alias)
    for ser_params in [{"area_id": "BGD"}, {"area": "BGD-ADM2-alpha"}]:
        r_ser = client.get("/api/series", params=ser_params)
        assert r_ser.status_code == 200
        assert len(r_ser.json()["data"]) > 0

    # 6. GET /api/calendar (area_id and frontend ?area= variant)
    for cal_params in [{"area_id": "BGD"}, {"area": "BGD-ADM2-alpha"}]:
        r_cal = client.get("/api/calendar", params=cal_params)
        assert r_cal.status_code == 200
        cal_data = r_cal.json()["data"]
        assert "grid" in cal_data and "climatology" in cal_data and "season" in cal_data

    # 7. GET /api/stats/yearly
    r_yearly = client.get("/api/stats/yearly", params={"area_id": "BGD"})
    assert r_yearly.status_code == 200
    first_year = r_yearly.json()["data"][0]
    assert "harmonized_total" in first_year and "total_events" in first_year

    # 8. GET /api/anomalies
    r_anom = client.get("/api/anomalies", params={"area_id": "BGD"})
    assert r_anom.status_code == 200
    assert isinstance(r_anom.json()["data"], list)

    # 9. GET /api/methodology
    r_meth = client.get("/api/methodology")
    assert r_meth.status_code == 200
    meth_data = r_meth.json()["data"]
    assert len(meth_data["qq_data"]) == 7
    assert meth_data["jump_metrics"]["rank_correlation"] is not None

    # 10. GET /api/guidance
    r_guid = client.get("/api/guidance", params={"area_id": "BGD-ADM2-alpha"})
    assert r_guid.status_code == 200
    assert len(r_guid.json()["data"]) > 0

    # 11. POST /api/ask
    r_ask = client.post(
        "/api/ask",
        json={"question": "When is peak fire season in Alpha District?", "area_id": "BGD-ADM2-alpha"},
    )
    assert r_ask.status_code == 200
    ask_data = r_ask.json()["data"]
    assert ask_data["answer"]
    assert ask_data["mode"] in {"live", "replay"}

    # 12. GET /api/alerts/active
    r_act = client.get("/api/alerts/active", params={"area_id": "BGD"})
    assert r_act.status_code == 200
    assert "season_approaching" in r_act.json()["data"]

    # 13, 14, 15. Subscribe -> Confirm -> Unsubscribe
    r_sub = client.post(
        "/api/alerts/subscriptions",
        json={"email": "audit@example.org", "area_id": "BGD", "rule": "both", "lead_days": 14},
    )
    assert r_sub.status_code == 200
    assert r_sub.json()["data"]["status"] == "pending_confirmation"

    conn = get_sqlite_connection(db_path)
    row = conn.execute(
        "SELECT unsubscribe_token FROM alert_subscriptions WHERE email = ?", ["audit@example.org"]
    ).fetchone()
    conn.close()
    assert row is not None
    token = str(row[0])

    r_conf = client.get("/api/alerts/subscriptions/confirm", params={"token": token})
    assert r_conf.status_code == 200
    assert r_conf.json()["data"]["confirmed"] is True

    r_unsub = client.delete("/api/alerts/subscriptions", params={"token": token})
    assert r_unsub.status_code == 200
    assert r_unsub.json()["data"]["unsubscribed"] is True
    assert get_subscription_by_token(token, db_path=db_path) is None
