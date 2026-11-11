"""Family coverage helpers: determine month ranges for sensor family coverage.

Pure functions: no file, network, or clock access.
"""

from __future__ import annotations

import calendar

import pandas as pd


def family_coverage_start(
    events_df: pd.DataFrame,
    family: str,
    explicit_start_ym: tuple[int, int] | None = None,
) -> tuple[int, int]:
    """Return the (year, month) of the first complete coverage month for a family.

    Specification:
    - MODIS: starts from 2000-11.
    - VIIRS: from the first complete month found in the data (expected 2012-02).
      If the earliest detection is on day 1 of the month, that month is complete.
      If on day > 1, the next calendar month is the first complete month.

    Args:
        events_df: DataFrame with 'sensor_family', and optionally 'start_ts'.
        family: 'MODIS' or 'VIIRS'.
        explicit_start_ym: Optional explicit override for testing.

    Returns:
        (year, month) tuple of the first complete month.
    """
    if explicit_start_ym is not None:
        return explicit_start_ym

    if family == "MODIS":
        return (2000, 11)

    if family == "VIIRS":
        fam_mask = events_df["sensor_family"] == family
        fam_df = events_df.loc[fam_mask]
        if fam_df.empty:
            return (2012, 2)

        if "start_ts" in fam_df.columns:
            min_ts = pd.to_datetime(fam_df["start_ts"], utc=True).min()
            if min_ts.day == 1:
                return (int(min_ts.year), int(min_ts.month))
            next_m = int(min_ts.month) + 1
            next_y = int(min_ts.year)
            if next_m > 12:
                next_y += 1
                next_m = 1
            return (next_y, next_m)

        return (2012, 2)

    raise ValueError(f"Unknown sensor family: {family}")


def determine_last_complete_month(
    events_df: pd.DataFrame,
    explicit_end_ym: tuple[int, int] | None = None,
) -> tuple[int, int]:
    """Determine the last *complete* calendar month present in events data.

    If data extends to the last day of the maximum month, that month is complete.
    If data terminates mid-month (partial month), the previous month is returned.
    If the dataset only spans a single distinct month (e.g. test fixture), that
    month is returned.

    Args:
        events_df: DataFrame with 'start_ts' (or 'year' and 'month').
        explicit_end_ym: Optional explicit (year, month) override.

    Returns:
        (year, month) of the last complete month.
    """
    if explicit_end_ym is not None:
        return explicit_end_ym

    if events_df.empty:
        raise ValueError("Cannot determine last complete month from empty data")

    unique_ym = events_df[["year", "month"]].drop_duplicates()
    if len(unique_ym) <= 1:
        row = unique_ym.iloc[0]
        return (int(row["year"]), int(row["month"]))

    if "start_ts" in events_df.columns:
        max_ts = pd.to_datetime(events_df["start_ts"], utc=True).max()
        y = int(max_ts.year)
        m = int(max_ts.month)
        d = int(max_ts.day)
        days_in_m = calendar.monthrange(y, m)[1]
        if d >= days_in_m:
            return (y, m)
        prev_m = m - 1
        prev_y = y
        if prev_m < 1:
            prev_y -= 1
            prev_m = 12
        return (prev_y, prev_m)

    max_y = int(events_df["year"].max())
    max_m = int(events_df.loc[events_df["year"] == max_y, "month"].max())
    prev_m = max_m - 1
    prev_y = max_y
    if prev_m < 1:
        prev_y -= 1
        prev_m = 12
    return (prev_y, prev_m)


def generate_dense_months(
    start_ym: tuple[int, int],
    end_ym: tuple[int, int],
) -> list[tuple[int, int]]:
    """Generate a list of (year, month) tuples from start to end inclusive.

    Args:
        start_ym: (year, month) start, e.g. (2000, 11).
        end_ym: (year, month) end inclusive, e.g. (2026, 10).

    Returns:
        Sorted list of (year, month) tuples.
    """
    sy, sm = start_ym
    ey, em = end_ym
    if (sy, sm) > (ey, em):
        return []

    result: list[tuple[int, int]] = []
    y, m = sy, sm
    while (y, m) <= (ey, em):
        result.append((y, m))
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1
    return result
