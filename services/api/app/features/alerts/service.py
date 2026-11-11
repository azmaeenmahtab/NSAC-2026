"""Service logic for alert subscriptions, confirmation, and active status."""

from __future__ import annotations

import secrets
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal

import duckdb

from app.core.dataset import LoadedDataset
from app.core.errors import NotFoundAPIError, ValidationAPIError
from app.core.responses import ResponseMeta
from app.features.alerts.evaluate import (
    above_normal,
    days_until_season_start,
    season_approaching,
)
from app.features.alerts.mailer import get_mailer
from app.features.alerts.repository import (
    confirm_subscription,
    create_subscription,
    delete_subscription_by_token,
)
from app.features.alerts.schemas import (
    ActiveAlertsData,
    ActiveAlertsEnvelope,
    ConfirmResponseData,
    SubscriptionRequest,
    SubscriptionResponseData,
    UnsubscribeResponseData,
)
from app.features.areas.service import resolve_area
from app.features.calendar.repository import (
    fetch_bbox_harmonized_monthly,
    fetch_season,
)


def subscribe(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    req: SubscriptionRequest,
    db_path: str | Path | None = None,
) -> SubscriptionResponseData:
    """Create an unconfirmed alert subscription and dispatch confirmation email."""
    resolved = resolve_area(cursor, req.area_id)

    token = secrets.token_urlsafe(32)
    create_subscription(
        email=str(req.email),
        area_id=resolved.area_id,
        rule=req.rule,
        lead_days=req.lead_days,
        unsubscribe_token=token,
        db_path=db_path,
    )

    get_mailer().send_confirmation(
        to_email=str(req.email),
        area_id=resolved.area_id,
        token=token,
    )

    return SubscriptionResponseData(
        message=f"Confirmation email dispatched to {req.email}",
        status="pending_confirmation",
    )


def confirm(
    token: str,
    db_path: str | Path | None = None,
) -> ConfirmResponseData:
    """Confirm a pending alert subscription."""
    cleaned = token.strip()
    if not cleaned:
        raise ValidationAPIError("token parameter is required")

    success = confirm_subscription(cleaned, db_path=db_path)
    if not success:
        raise NotFoundAPIError("Invalid or expired confirmation token")

    return ConfirmResponseData(
        confirmed=True,
        message="Subscription confirmed successfully",
    )


def unsubscribe(
    token: str,
    db_path: str | Path | None = None,
) -> UnsubscribeResponseData:
    """Unsubscribe using the unique token."""
    cleaned = token.strip()
    if not cleaned:
        raise ValidationAPIError("token parameter is required")

    success = delete_subscription_by_token(cleaned, db_path=db_path)
    if not success:
        raise NotFoundAPIError("Invalid or unknown unsubscribe token")

    return UnsubscribeResponseData(
        message="Unsubscribed successfully",
    )


def get_active_alerts(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
    today_override: date | None = None,
) -> ActiveAlertsEnvelope:
    """Return the current advisory alert state for display."""
    cleaned_id = area_id.strip()
    if not cleaned_id:
        raise ValidationAPIError("area_id must not be empty")

    resolved = resolve_area(cursor, cleaned_id)
    today = today_override or datetime.now(UTC).date()

    season_appr = False
    days_left: int | None = None
    cur_class: Literal["normal", "elevated", "extreme"] = "normal"

    if resolved.kind == "bbox" and resolved.bbox is not None:
        df = fetch_bbox_harmonized_monthly(cursor, resolved.bbox)
        if not df.empty:
            from pyroscope_pipeline.stats import (  # type: ignore[import-untyped]
                compute_anomalies,
                compute_climatology,
                compute_season_from_means,
            )

            clim_df = compute_climatology(df)
            if not clim_df.empty:
                means = clim_df.sort_values("month")["mean"].to_numpy(dtype=float)
                s_dict = compute_season_from_means(means)
                start_m = int(s_dict["start_month"])
                days_left = days_until_season_start(today, start_m)
                season_appr = season_approaching(today, start_m, lead_days=14)

            anom_df = compute_anomalies(df)
            if not anom_df.empty:
                last_row = anom_df.sort_values(["year", "month"]).iloc[-1]
                cls_str = str(last_row["class"]).lower()
                if cls_str in ("normal", "elevated", "extreme"):
                    cur_class = cls_str  # type: ignore[assignment]
    else:
        target_id = resolved.area_id
        season = fetch_season(cursor, target_id)
        if not season and resolved.region_ids:
            season = fetch_season(cursor, resolved.region_ids[0])

        if season:
            days_left = days_until_season_start(today, season.start_month)
            season_appr = season_approaching(today, season.start_month, lead_days=14)

        anom_row = cursor.execute(
            """
            SELECT class
            FROM anomalies
            WHERE region_id = ? AND CAST(year AS INTEGER) = ? AND CAST(month AS INTEGER) = ?
            LIMIT 1
            """,
            [target_id, today.year, today.month],
        ).fetchone()

        if not anom_row:
            anom_row = cursor.execute(
                """
                SELECT class
                FROM anomalies
                WHERE region_id = ?
                ORDER BY year DESC, month DESC
                LIMIT 1
                """,
                [target_id],
            ).fetchone()

        if anom_row and anom_row[0]:
            cls_str = str(anom_row[0]).lower()
            if cls_str in ("normal", "elevated", "extreme"):
                cur_class = cls_str  # type: ignore[assignment]

    is_above = above_normal(cur_class)

    if season_appr and days_left is not None:
        reason = f"Fire season begins in {days_left} days"
    elif is_above:
        reason = f"Current month active burning is {cur_class}"
    else:
        reason = "Conditions within baseline ranges"

    return ActiveAlertsEnvelope(
        data=ActiveAlertsData(
            season_approaching=season_appr,
            above_normal=is_above,
            current_month_class=cur_class,
            days_until_season=days_left,
            reason=reason,
            provisional_as_of=dataset.as_of,
        ),
        meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
    )
