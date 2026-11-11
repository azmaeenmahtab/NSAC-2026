"""Pure NRT update planner: determine missing UTC days and FIRMS API fetch windows.

Pure functions: no file, network, or clock access.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class FetchWindow:
    """Contiguous FIRMS Area API date range (`1 <= days <= 10`)."""

    start_date: str
    days: int
    end_date: str


def parse_iso_date(value: str | date) -> date:
    """Parse an ISO `YYYY-MM-DD` string or return a `date` instance."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(value.strip()[:10])


def plan_missing_days(
    as_of_date: str | date,
    today_utc: str | date,
    max_lookback_days: int | None = None,
) -> list[date]:
    """Return sorted UTC calendar dates missing between `as_of_date` and yesterday (UTC).

    Inputs:
        as_of_date: Last date already covered in the active processed dataset (`YYYY-MM-DD`).
        today_utc: Current UTC date (`YYYY-MM-DD` or `date`); passed explicitly for purity.
        max_lookback_days: Optional retention cap limiting how many trailing days to fetch.
    Outputs:
        Ordered list of missing `datetime.date` objects up to `today_utc - 1 day`.
    """
    last_covered = parse_iso_date(as_of_date)
    today = parse_iso_date(today_utc)
    yesterday = today - timedelta(days=1)
    start = last_covered + timedelta(days=1)

    if start > yesterday:
        return []

    if max_lookback_days is not None:
        if max_lookback_days < 1:
            raise ValueError(f"max_lookback_days must be >= 1, got {max_lookback_days}")
        earliest_allowed = yesterday - timedelta(days=max_lookback_days - 1)
        start = max(start, earliest_allowed)

    n_days = (yesterday - start).days + 1
    return [start + timedelta(days=offset) for offset in range(n_days)]


def chunk_fetch_windows(
    missing_days: Sequence[date],
    max_days_per_call: int = 5,
) -> list[FetchWindow]:
    """Partition sorted missing dates into contiguous FIRMS API `FetchWindow` batches.

    FIRMS NRT Area API accepts `DAY_RANGE` up to 5 days per request (up to 10 on SP).
    """
    if not (1 <= max_days_per_call <= 10):
        raise ValueError(f"max_days_per_call must be in [1, 10], got {max_days_per_call}")
    if not missing_days:
        return []

    sorted_days = sorted(set(missing_days))
    windows: list[FetchWindow] = []

    run_start = sorted_days[0]
    run_prev = sorted_days[0]
    run_len = 1

    for d in sorted_days[1:]:
        is_contiguous = (d - run_prev).days == 1
        if is_contiguous and run_len < max_days_per_call:
            run_prev = d
            run_len += 1
        else:
            windows.append(
                FetchWindow(
                    start_date=run_start.isoformat(),
                    days=run_len,
                    end_date=run_prev.isoformat(),
                )
            )
            run_start = d
            run_prev = d
            run_len = 1

    windows.append(
        FetchWindow(
            start_date=run_start.isoformat(),
            days=run_len,
            end_date=run_prev.isoformat(),
        )
    )
    return windows


def plan_fetch_windows(
    as_of_date: str | date,
    today_utc: str | date,
    max_days_per_call: int = 5,
    max_lookback_days: int | None = None,
) -> list[FetchWindow]:
    """Compute FIRMS API fetch windows for all missing days from `as_of_date` to yesterday."""
    days = plan_missing_days(
        as_of_date=as_of_date,
        today_utc=today_utc,
        max_lookback_days=max_lookback_days,
    )
    return chunk_fetch_windows(days, max_days_per_call=max_days_per_call)
