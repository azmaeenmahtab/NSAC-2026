"""Pure evaluation functions for fire season, anomaly alerts, and plain-English risk emails."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

AnomalyClass = Literal["normal", "elevated", "extreme"]
ThreatLevel = Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]

_MONTH_NAMES = (
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def month_name(month: int) -> str:
    """Return full English month name for 1..12."""
    if 1 <= month <= 12:
        return _MONTH_NAMES[month]
    return f"Month {month}"


def days_until_season_start(today: date, season_start_month: int) -> int:
    """Calculate calendar days from `today` until the 1st of `season_start_month`."""
    if not (1 <= season_start_month <= 12):
        raise ValueError(f"season_start_month must be 1..12, got {season_start_month}")

    target = date(today.year, season_start_month, 1)
    if target < today:
        target = date(today.year + 1, season_start_month, 1)

    return (target - today).days


def season_approaching(
    today: date,
    season_start_month: int,
    lead_days: int = 14,
) -> bool:
    """Return True if the next fire season starts between 0 and `lead_days` days ahead."""
    if lead_days < 0:
        raise ValueError(f"lead_days must be non-negative, got {lead_days}")

    days = days_until_season_start(today, season_start_month)
    return 0 <= days <= lead_days


def above_normal(month_to_date_class: str | None) -> bool:
    """Return True if the current monthly burning anomaly class is elevated or extreme."""
    if not month_to_date_class:
        return False
    return month_to_date_class.strip().lower() in ("elevated", "extreme")


@dataclass(frozen=True)
class ThreatAssessment:
    """Plain-English fire risk summary derived strictly from processed data."""

    level: ThreatLevel
    headline: str
    explanation: str


def compute_threat_level(
    is_season_approaching: bool,
    in_fire_season: bool,
    anomaly_class: str | None,
    nearby_events_count: int = 0,
) -> ThreatAssessment:
    """Determine plain-English satellite risk tier from processed seasonal & anomaly signals."""
    cls_norm = (anomaly_class or "normal").strip().lower()

    if cls_norm == "extreme" or (cls_norm == "elevated" and nearby_events_count >= 3):
        return ThreatAssessment(
            level="CRITICAL",
            headline="Very High Fire Activity",
            explanation=(
                "Fire activity in this area is much higher than usual for this time of year."
            ),
        )

    if cls_norm == "elevated" or nearby_events_count >= 1:
        return ThreatAssessment(
            level="HIGH",
            headline="Elevated Fire Activity",
            explanation=(
                "Recent fires were spotted near this area, or activity is higher than normal."
            ),
        )

    if is_season_approaching or in_fire_season:
        return ThreatAssessment(
            level="MODERATE",
            headline="Fire Season Watch",
            explanation=(
                "The dry burning season is starting soon or currently active in this area."
            ),
        )

    return ThreatAssessment(
        level="LOW",
        headline="Normal Conditions",
        explanation="Fire activity is quiet and within normal seasonal levels.",
    )


def format_preseason_station_email(
    recipient_label: str,
    area_name: str,
    days_left: int,
    start_month: int,
    end_month: int,
    risk: ThreatAssessment,
) -> tuple[str, str]:
    """Format a simple, jargon-free 14-day pre-season readiness email."""
    start_name = month_name(start_month)
    end_name = month_name(end_month)
    subject = f"[{risk.level} Risk] Fire season starts in {days_left} days - {area_name}"
    body = (
        f"Hello {recipient_label},\n\n"
        f"Based on past fire records, the main burning season in {area_name} usually begins "
        f"in {days_left} days (around {start_name} 1).\n\n"
        f"- Risk Level: {risk.level} ({risk.headline})\n"
        f"- Usual Busy Months: {start_name} to {end_name}\n"
        f"- Why you are getting this: Early reminder so your team and local community "
        f"can prepare before dry weather arrives.\n"
    )
    return subject, body


def format_activity_station_email(
    recipient_label: str,
    area_name: str,
    risk: ThreatAssessment,
    nearby_events: int,
    radius_km: float,
    center_lat: float | None = None,
    center_lon: float | None = None,
    latest_date: str | None = None,
) -> tuple[str, str]:
    """Format a simple, jargon-free post-pass satellite activity report email."""
    if nearby_events > 0:
        subject = f"[{risk.level} Risk] Satellite Spotted {nearby_events} Fire(s) Near {area_name}"
        activity_line = (
            f"NASA satellites spotted {nearby_events} recent fire spot(s) within "
            f"{int(radius_km)} km of your area"
            + (f" (latest pass: {latest_date})." if latest_date else ".")
        )
    else:
        subject = f"[{risk.level} Risk] Fire Activity Update - {area_name}"
        activity_line = f"Fire activity in {area_name} has reached {risk.level} levels."

    location_line = (
        f"- Location Area: Near {center_lat:.3f}N, {center_lon:.3f}E ({area_name})\n"
        if center_lat is not None and center_lon is not None
        else f"- Area: {area_name}\n"
    )

    body = (
        f"Hello {recipient_label},\n\n"
        f"{activity_line}\n\n"
        f"- Risk Level: {risk.level} ({risk.explanation})\n"
        f"{location_line}"
        f"- Why you are getting this: Satellites pass overhead a few times a day, so these fires "
        f"may have started hours ago. We sent this report for your awareness in case no local "
        f"report reached your station.\n"
    )
    return subject, body
