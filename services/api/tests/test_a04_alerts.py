"""Unit and integration tests for A04 alert subscriptions, evaluation, and mailer."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.ratelimit import SlidingWindowRateLimitMiddleware
from app.features.alerts.evaluate import (
    above_normal,
    days_until_season_start,
    season_approaching,
)
from app.features.alerts.mailer import ConsoleMailer, set_mailer
from app.features.alerts.repository import (
    get_sqlite_connection,
    get_subscription_by_token,
)
from app.main import create_app
from scripts.send_alerts import evaluate_and_dispatch_alerts

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
REFERENCE_DIR = REPO_ROOT / "data" / "reference"


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Return a path to an isolated temporary SQLite database."""
    return tmp_path / "test_alerts.db"


@pytest.fixture
def console_mailer() -> ConsoleMailer:
    """Configure and return a fresh ConsoleMailer."""
    mailer = ConsoleMailer()
    set_mailer(mailer)
    return mailer


@pytest.fixture
def client(test_db_path: Path, console_mailer: ConsoleMailer) -> TestClient:
    """Create a TestClient with isolated SQLite app.db and ConsoleMailer."""
    get_sqlite_connection(test_db_path)
    cfg = Settings(
        data_dir=str(FIXTURES_DIR),
        reference_dir=str(REFERENCE_DIR),
        web_origin="http://localhost:3000",
        app_db_path=str(test_db_path),
        rate_limit_default="120/minute",
    )
    app = create_app(cfg)
    # Reset any rate limiter state between tests
    for middleware in app.user_middleware:
        if isinstance(middleware.cls, type) and issubclass(
            middleware.cls, SlidingWindowRateLimitMiddleware
        ):
            pass
    return TestClient(app)


def test_hand_verified_season_approaching_fixtures() -> None:
    """Verify the 4 hand-verified calendar season date fixtures from A04 specification.

    `season_approaching(today, season_start_month=3, lead_days=14)` (2027 is non-leap year):
    - today 2027-02-14: March 1 is 15 days ahead -> false
    - today 2027-02-15: 14 days ahead -> true
    - today 2027-03-01: 0 days ahead -> true
    - today 2027-03-02: next March 1 is 2028-03-01 (365 days ahead) -> false
    """
    # 2027-02-14: 15 days ahead -> False
    d1 = date(2027, 2, 14)
    assert days_until_season_start(d1, 3) == 15
    assert season_approaching(d1, 3, lead_days=14) is False

    # 2027-02-15: 14 days ahead -> True
    d2 = date(2027, 2, 15)
    assert days_until_season_start(d2, 3) == 14
    assert season_approaching(d2, 3, lead_days=14) is True

    # 2027-03-01: 0 days ahead -> True
    d3 = date(2027, 3, 1)
    assert days_until_season_start(d3, 3) == 0
    assert season_approaching(d3, 3, lead_days=14) is True

    # 2027-03-02: 365 days ahead -> False
    d4 = date(2027, 3, 2)
    assert days_until_season_start(d4, 3) == 365
    assert season_approaching(d4, 3, lead_days=14) is False


def test_above_normal_pure_evaluator() -> None:
    """Verify above_normal evaluates elevated and extreme as True, normal as False."""
    assert above_normal("elevated") is True
    assert above_normal("extreme") is True
    assert above_normal("EXTREME") is True
    assert above_normal("normal") is False
    assert above_normal("insufficient_data") is False
    assert above_normal(None) is False


def test_subscription_lifecycle_and_dispatch(
    client: TestClient,
    test_db_path: Path,
    console_mailer: ConsoleMailer,
) -> None:
    """End-to-end lifecycle: subscribe, confirm, dispatch once, deduplicate in same period, unsubscribe."""
    email = "researcher@example.org"
    area_id = "BGD-ADM2-alpha"

    # 1. Subscribe
    sub_res = client.post(
        "/api/alerts/subscriptions",
        json={
            "email": email,
            "area_id": area_id,
            "rule": "both",
            "lead_days": 14,
        },
    )
    assert sub_res.status_code == 200
    assert sub_res.json()["data"]["status"] == "pending_confirmation"

    # Confirmation message dispatched via ConsoleMailer
    assert len(console_mailer.sent_messages) == 1
    conf_msg = console_mailer.sent_messages[0]
    assert conf_msg["type"] == "confirmation"
    assert conf_msg["to"] == email
    token = conf_msg["token"]

    # Verify unconfirmed in database
    sub_row = get_subscription_by_token(token, db_path=test_db_path)
    assert sub_row is not None
    assert sub_row["confirmed"] is False

    # 2. Confirm
    conf_res = client.get("/api/alerts/subscriptions/confirm", params={"token": token})
    assert conf_res.status_code == 200
    assert conf_res.json()["data"]["confirmed"] is True

    # Verify confirmed in database
    sub_row = get_subscription_by_token(token, db_path=test_db_path)
    assert sub_row is not None
    assert sub_row["confirmed"] is True

    # 3. Dispatch alert (using simulated date 2020-05-15 where alpha has extreme fire anomaly)
    dispatch_summary = evaluate_and_dispatch_alerts(
        data_dir=FIXTURES_DIR,
        reference_dir=REFERENCE_DIR,
        db_path=test_db_path,
        today_override=date(2020, 5, 15),
    )
    assert dispatch_summary["subscriptions_evaluated"] == 1
    assert dispatch_summary["notifications_sent"] >= 1

    # Verify alert message contains advisory disclaimer and unsubscribe link
    alert_msgs = [m for m in console_mailer.sent_messages if m["type"] == "alert"]
    assert len(alert_msgs) >= 1
    assert "ADVISORY NOTICE" in alert_msgs[0]["body"]
    assert "NASA FIRMS" in alert_msgs[0]["body"]
    assert "unsubscribe" in alert_msgs[0]["body"].lower()

    # 4. Dispatch again in the same month (2020-05) -> must deduplicate (no second notification)
    dispatch_summary_2 = evaluate_and_dispatch_alerts(
        data_dir=FIXTURES_DIR,
        reference_dir=REFERENCE_DIR,
        db_path=test_db_path,
        today_override=date(2020, 5, 20),
    )
    assert dispatch_summary_2["notifications_sent"] == 0
    assert dispatch_summary_2["notifications_skipped_already_sent"] >= 1

    # 5. Unsubscribe
    unsub_res = client.delete("/api/alerts/subscriptions", params={"token": token})
    assert unsub_res.status_code == 200
    assert "Unsubscribed" in unsub_res.json()["data"]["message"]

    # Verify deleted from database
    assert get_subscription_by_token(token, db_path=test_db_path) is None


def test_active_alerts_endpoint(client: TestClient) -> None:
    """Verify `GET /api/alerts/active` for preset and custom bbox areas."""
    # Active alerts for alpha
    res = client.get("/api/alerts/active", params={"area_id": "BGD-ADM2-alpha"})
    assert res.status_code == 200
    payload = res.json()
    data = payload["data"]
    assert "season_approaching" in data
    assert "above_normal" in data
    assert "current_month_class" in data
    assert payload["meta"]["dataVersion"] == "v0.1.0-fixtures"

    # Active alerts for custom bbox
    res_bbox = client.get("/api/alerts/active", params={"area_id": "bbox:88.0,20.5,93.0,27.0"})
    assert res_bbox.status_code == 200
    assert "season_approaching" in res_bbox.json()["data"]


def test_validation_and_error_handling(client: TestClient) -> None:
    """Validation errors for bad email, unknown area, bad lead_days, and missing tokens."""
    # Bad email format -> 400
    res_bad_email = client.post(
        "/api/alerts/subscriptions",
        json={"email": "not-an-email", "area_id": "BGD", "rule": "both"},
    )
    assert res_bad_email.status_code == 400

    # Unknown area -> 404
    res_unknown_area = client.post(
        "/api/alerts/subscriptions",
        json={"email": "valid@example.org", "area_id": "nonexistent-area", "rule": "both"},
    )
    assert res_unknown_area.status_code == 404

    # Lead days outside 1..60 -> 400
    res_bad_lead = client.post(
        "/api/alerts/subscriptions",
        json={
            "email": "valid@example.org",
            "area_id": "BGD",
            "rule": "both",
            "lead_days": 100,
        },
    )
    assert res_bad_lead.status_code == 400

    # Unknown confirm token -> 404
    res_bad_confirm = client.get(
        "/api/alerts/subscriptions/confirm",
        params={"token": "unknown-token-12345"},
    )
    assert res_bad_confirm.status_code == 404

    # Unknown unsubscribe token -> 404
    res_bad_unsub = client.delete(
        "/api/alerts/subscriptions",
        params={"token": "unknown-token-12345"},
    )
    assert res_bad_unsub.status_code == 404


def test_rate_limiting_subscriptions(client: TestClient) -> None:
    """Verify per-IP rate limit of 5 requests per hour on `/api/alerts/subscriptions`."""
    headers = {"X-Forwarded-For": "198.51.100.42"}

    # First 5 succeed
    for i in range(5):
        res = client.post(
            "/api/alerts/subscriptions",
            json={
                "email": f"user{i}@example.org",
                "area_id": "BGD",
                "rule": "both",
            },
            headers=headers,
        )
        assert res.status_code == 200

    # 6th is rate limited with 429
    res_limited = client.post(
        "/api/alerts/subscriptions",
        json={
            "email": "user6@example.org",
            "area_id": "BGD",
            "rule": "both",
        },
        headers=headers,
    )
    assert res_limited.status_code == 429
    assert res_limited.json()["error"]["code"] == "RATE_LIMITED"
    assert "Retry-After" in res_limited.headers


def test_dispatch_season_approaching_alert(
    client: TestClient,
    test_db_path: Path,
    console_mailer: ConsoleMailer,
) -> None:
    """Verify season approaching alert is dispatched when within lead days of season start."""
    email = "forester@example.org"
    area_id = "BGD-ADM2-alpha"  # season starts April 1 (month 4)

    # Subscribe with rule="season_approaching"
    sub_res = client.post(
        "/api/alerts/subscriptions",
        json={
            "email": email,
            "area_id": area_id,
            "rule": "season_approaching",
            "lead_days": 14,
        },
    )
    assert sub_res.status_code == 200
    token = console_mailer.sent_messages[0]["token"]

    # Confirm subscription
    conf_res = client.get("/api/alerts/subscriptions/confirm", params={"token": token})
    assert conf_res.status_code == 200
    console_mailer.clear()

    # 1. Evaluate on 2027-03-10: March 10 is 22 days before April 1 (> 14 days) -> not sent
    summary_early = evaluate_and_dispatch_alerts(
        data_dir=FIXTURES_DIR,
        reference_dir=REFERENCE_DIR,
        db_path=test_db_path,
        today_override=date(2027, 3, 10),
    )
    assert summary_early["notifications_sent"] == 0

    # 2. Evaluate on 2027-03-20: March 20 is 12 days before April 1 (<= 14 days) -> sent!
    summary_trigger = evaluate_and_dispatch_alerts(
        data_dir=FIXTURES_DIR,
        reference_dir=REFERENCE_DIR,
        db_path=test_db_path,
        today_override=date(2027, 3, 20),
    )
    assert summary_trigger["notifications_sent"] == 1
    assert len(console_mailer.sent_messages) == 1
    msg = console_mailer.sent_messages[0]
    assert "Fire season starts in 12 days" in msg["subject"]
    assert "ADVISORY NOTICE" in msg["body"]
