"""Pure rule evaluation engine for wildland fire calendar stages."""

from __future__ import annotations

from app.features.calendar.schemas import FireSeason
from app.features.guidance.schemas import GuidanceStage


def stage_for(
    month: int,
    season: FireSeason,
    latest_class: str = "normal",
) -> GuidanceStage:
    """Determine the wildland action stage from calendar month, season, and anomaly class.

    Pure function with no I/O, network, or clock dependencies.

    Rules:
    - If current or latest month class is 'extreme' -> 'extreme'
    - 'pre_season': within 30 days before season window start (defined as the calendar
      month immediately preceding start_month)
    - 'in_season': calendar month falls inside the season window [start_month, end_month]
    - 'post_season': calendar month immediately following season window end_month
    - otherwise: 'off_season'
    """
    if not (1 <= month <= 12):
        raise ValueError(f"month must be an integer between 1 and 12, got {month}")

    if latest_class.strip().lower() == "extreme":
        return "extreme"

    start = season.start_month
    end = season.end_month

    if not (1 <= start <= 12 and 1 <= end <= 12):
        return "off_season"

    # Pre-season: calendar month immediately before start_month (circular 1-12)
    pre_month = 12 if start == 1 else start - 1
    if month == pre_month:
        return "pre_season"

    # In-season: inside season window
    if start <= end:
        in_season = start <= month <= end
    else:
        # Cross-year season window (e.g. Nov-Feb: 11..2)
        in_season = month >= start or month <= end

    if in_season:
        return "in_season"

    # Post-season: calendar month immediately after end_month (circular 1-12)
    post_month = 1 if end == 12 else end + 1
    if month == post_month:
        return "post_season"

    return "off_season"

