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

from app.core.config import settings
from app.core.dataset import load_dataset

logger = logging.getLogger("pyroscope.alerts.cron")
from app.features.alerts.evaluate import (
    above_normal,
    days_until_season_start,
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


def evaluate_and_dispatch_alerts(
    data_dir: str | Path | None = None,
    reference_dir: str | Path | None = None,
    db_path: str | Path | None = None,
    today_override: date | None = None,
) -> dict[str, int]:
    """Evaluate all confirmed subscriptions and dispatch pending advisory notices."""
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

        try:
            resolved = resolve_area(cursor, area_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to resolve area %s for sub %s: %s", area_id, sub_id, exc)
            continue

        target_id = resolved.area_id
        season = fetch_season(cursor, target_id)
        if not season and resolved.region_ids:
            season = fetch_season(cursor, resolved.region_ids[0])

        # Evaluate season_approaching
        if (
            season
            and rule in ("season_approaching", "both")
            and season_approaching(today, season.start_month, lead_days)
        ):
            days_left = days_until_season_start(today, season.start_month)
            if not has_notification_been_sent(sub_id, "season_approaching", period, active_db):
                subject = (
                    f"[PyroScope Advisory] Fire season starts in {days_left} days ({resolved.name})"
                )
                body = (
                    f"Advisory Notice for {resolved.name} ({resolved.area_id}):\n\n"
                    f"The climatological fire season is projected to start on calendar month "
                    f"{season.start_month} (in {days_left} days).\n"
                    f"Historic annual burn share during peak window: {season.share_of_annual * 100:.1f}%.\n"
                )
                mailer.send_alert(to_email, resolved.area_id, subject, body, unsub_token)
                record_notification_sent(sub_id, "season_approaching", period, active_db)
                sent_count += 1
            else:
                skipped_count += 1

        # Evaluate above_normal
        if rule in ("above_normal", "both"):
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

            if anom_row:
                cls_str = str(anom_row[0]).lower()
                val = float(anom_row[1])
                if above_normal(cls_str):
                    if not has_notification_been_sent(sub_id, "above_normal", period, active_db):
                        subject = f"[PyroScope Advisory] Active fire anomaly: {cls_str.upper()} ({resolved.name})"
                        body = (
                            f"Advisory Notice for {resolved.name} ({resolved.area_id}):\n\n"
                            f"The current month fire activity has reached {cls_str.upper()} levels "
                            f"(observed: {val:.1f} MODIS-equivalent events).\n"
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
