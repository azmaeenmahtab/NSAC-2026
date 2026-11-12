"""Daily automated batch evaluation and dispatch script for alert subscriptions."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, date, datetime
from pathlib import Path

# Add services/api to path if invoked directly
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import duckdb

from app.core.config import settings
from app.core.dataset import load_dataset
from app.features.alerts.evaluate import (
    above_normal,
    compute_threat_level,
    days_until_season_start,
    format_activity_station_email,
    format_preseason_station_email,
    season_approaching,
)
from app.features.alerts.mailer import get_mailer
from app.features.alerts.repository import (
    has_notification_been_sent,
    list_confirmed_subscriptions,
    record_notification_sent,
)
from app.features.areas.service import resolve_area
from app.features.calendar.repository import fetch_season

logger = logging.getLogger("pyroscope.alerts.cron")


def _count_recent_district_events(
    cursor: duckdb.DuckDBPyConnection,
    district_ids: list[str],
    registered_views: tuple[str, ...],
) -> tuple[int, float | None, float | None, str | None]:
    """Count events in the latest month for `district_ids` when `events` view exists."""
    if "events" not in registered_views or not district_ids:
        return 0, None, None, None
    placeholders = ", ".join(["?"] * len(district_ids))
    row = cursor.execute(
        f"""
        WITH latest AS (
            SELECT MAX(CAST(year AS INTEGER) * 100 + CAST(month AS INTEGER)) AS ym
            FROM events
        )
        SELECT COUNT(*), AVG(lat), AVG(lon), CAST(MAX(end_ts) AS VARCHAR)
        FROM events, latest
        WHERE district_id IN ({placeholders})
          AND (CAST(year AS INTEGER) * 100 + CAST(month AS INTEGER)) = latest.ym
        """,
        district_ids,
    ).fetchone()
    if not row or not row[0]:
        return 0, None, None, None
    return (
        int(row[0]),
        float(row[1]) if row[1] is not None else None,
        float(row[2]) if row[2] is not None else None,
        str(row[3])[:10] if row[3] is not None else None,
    )


def evaluate_and_dispatch_alerts(
    data_dir: str | Path | None = None,
    reference_dir: str | Path | None = None,
    db_path: str | Path | None = None,
    today_override: date | None = None,
) -> dict[str, int]:
    """Evaluate all confirmed subscriptions and dispatch plain-English advisory notices."""
    dataset = load_dataset(
        data_dir=data_dir or settings.data_dir,
        reference_dir=reference_dir or settings.reference_dir,
    )
    cursor = dataset.cursor()
    active_db = db_path or settings.app_db_path

    subs = list_confirmed_subscriptions(active_db)
    today = today_override or datetime.now(UTC).date()
    period = today.strftime("%Y-%m")

    sent_count = 0
    skipped_count = 0
    mailer = get_mailer()

    for sub in subs:
        sub_id = int(sub["id"])
        area_id = str(sub["area_id"])
        rule = str(sub["rule"])
        lead_days = int(sub["lead_days"])
        to_email = str(sub["email"])
        unsub_token = str(sub["unsubscribe_token"])
        sub_type = str(sub.get("subscriber_type") or "public")
        station_name = sub.get("station_name")
        radius_km = float(sub.get("radius_km") or 25.0)
        recipient_label = (
            f"{station_name} Team"
            if station_name
            else ("Fire Station Team" if sub_type == "fire_station" else "Subscriber")
        )

        try:
            resolved = resolve_area(cursor, area_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to resolve area %s for sub %s: %s", area_id, sub_id, exc)
            continue

        target_id = resolved.area_id
        season = fetch_season(cursor, target_id)
        if not season and resolved.region_ids:
            season = fetch_season(cursor, resolved.region_ids[0])

        is_approaching = bool(season and season_approaching(today, season.start_month, lead_days))
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

        anom_row = cursor.execute(
            """
            SELECT class, value
            FROM anomalies
            WHERE region_id = ? AND CAST(year AS INTEGER) = ? AND CAST(month AS INTEGER) = ?
            LIMIT 1
            """,
            [target_id, today.year, today.month],
        ).fetchone()
        if not anom_row:
            anom_row = cursor.execute(
                """
                SELECT class, value
                FROM anomalies
                WHERE region_id = ?
                ORDER BY year DESC, month DESC
                LIMIT 1
                """,
                [target_id],
            ).fetchone()

        cls_str = str(anom_row[0]).lower() if anom_row and anom_row[0] else "normal"
        nearby_events, ev_lat, ev_lon, latest_dt = _count_recent_district_events(
            cursor, list(resolved.region_ids), dataset.registered_views
        )

        risk = compute_threat_level(
            is_season_approaching=is_approaching,
            in_fire_season=in_season,
            anomaly_class=cls_str,
            nearby_events_count=nearby_events,
        )

        # 1. Evaluate season_approaching (14-day pre-season alert)
        if season and rule in ("season_approaching", "both") and is_approaching:
            days_left = days_until_season_start(today, season.start_month)
            if not has_notification_been_sent(sub_id, "season_approaching", period, active_db):
                subject, body = format_preseason_station_email(
                    recipient_label=recipient_label,
                    area_name=resolved.name,
                    days_left=days_left,
                    start_month=season.start_month,
                    end_month=season.end_month,
                    risk=risk,
                )
                mailer.send_alert(to_email, resolved.area_id, subject, body, unsub_token)
                record_notification_sent(sub_id, "season_approaching", period, active_db)
                sent_count += 1
            else:
                skipped_count += 1

        # 2. Evaluate above_normal OR post-pass fire report for subscribed fire stations
        should_send_activity = above_normal(cls_str) or (
            sub_type == "fire_station" and nearby_events > 0
        )
        if rule in ("above_normal", "both") and should_send_activity:
            if not has_notification_been_sent(sub_id, "above_normal", period, active_db):
                subject, body = format_activity_station_email(
                    recipient_label=recipient_label,
                    area_name=resolved.name,
                    risk=risk,
                    nearby_events=nearby_events,
                    radius_km=radius_km,
                    center_lat=ev_lat,
                    center_lon=ev_lon,
                    latest_date=latest_dt,
                )
                mailer.send_alert(to_email, resolved.area_id, subject, body, unsub_token)
                record_notification_sent(sub_id, "above_normal", period, active_db)
                sent_count += 1
            else:
                skipped_count += 1

    summary = {
        "subscriptions_evaluated": len(subs),
        "notifications_sent": sent_count,
        "notifications_skipped_already_sent": skipped_count,
    }
    logger.info("Alert dispatch run complete: %s", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate and dispatch fire advisories")
    parser.add_argument("--data-dir", default=None, help="Path to processed data directory")
    parser.add_argument("--db-path", default=None, help="Path to SQLite app.db")
    args = parser.parse_args()

    summary = evaluate_and_dispatch_alerts(data_dir=args.data_dir, db_path=args.db_path)
    print(summary)


if __name__ == "__main__":
    main()
