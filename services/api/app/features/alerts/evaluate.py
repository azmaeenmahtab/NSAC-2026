"""Pure evaluation functions for fire season and anomaly alerts."""

from __future__ import annotations

from datetime import date
from typing import Literal

AnomalyClass = Literal["normal", "elevated", "extreme"]


def days_until_season_start(today: date, season_start_month: int) -> int:
    """Calculate the number of calendar days from `today` until the next season start date.

    The next season start date is the 1st day of `season_start_month`.
    If the start date in `today.year` is in the past (strictly before `today`),
    the next occurrence is the 1st day of `season_start_month` in `today.year + 1`.
    """
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
    """Return True if the next fire season starts between 0 and `lead_days` days ahead.

    Hand-verified fixtures for start_month=3, lead_days=14 (2027 non-leap year):
    - today 2027-02-14: March 1 is 15 days ahead -> False
    - today 2027-02-15: 14 days ahead -> True
    - today 2027-03-01: 0 days ahead -> True
    - today 2027-03-02: next March 1 is 2028-03-01 (365 days ahead) -> False
    """
    if lead_days < 0:
        raise ValueError(f"lead_days must be non-negative, got {lead_days}")

    days = days_until_season_start(today, season_start_month)
    return 0 <= days <= lead_days


def above_normal(month_to_date_class: str | None) -> bool:
    """Return True if the current monthly burning anomaly class is elevated or extreme."""
    if not month_to_date_class:
        return False
    return month_to_date_class.strip().lower() in ("elevated", "extreme")
