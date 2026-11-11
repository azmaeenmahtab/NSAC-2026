"""Service logic and caching for `/api/calendar`."""

from __future__ import annotations

import math
from collections import OrderedDict

import duckdb
from pyroscope_pipeline.stats import (  # type: ignore[import-untyped]
    compute_anomalies,
    compute_climatology,
    compute_season_from_means,
)

from app.core.dataset import LoadedDataset
from app.core.errors import NotFoundAPIError, ValidationAPIError
from app.core.responses import ResponseMeta
from app.features.areas.service import resolve_area
from app.features.calendar.repository import (
    fetch_bbox_harmonized_monthly,
    fetch_calendar_grid,
    fetch_climatology,
    fetch_season,
)
from app.features.calendar.schemas import (
    CalendarCell,
    CalendarData,
    CalendarEnvelope,
    FireSeason,
    MonthClimatology,
)

_MAX_CACHE_ENTRIES = 256
_CALENDAR_CACHE: OrderedDict[tuple[object, ...], CalendarEnvelope] = OrderedDict()


def clear_calendar_cache() -> None:
    """Clear the in-process calendar LRU cache."""
    _CALENDAR_CACHE.clear()


def _provisional_ym(provisional_from: str | None) -> int | None:
    if not provisional_from:
        return None
    parts = provisional_from.strip().split("-")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return int(parts[0]) * 100 + int(parts[1])
    return None


def _compute_bbox_calendar(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    bbox: tuple[float, float, float, float],
    area_id: str,
    prov_ym: int | None,
) -> CalendarEnvelope:
    """Compute on-the-fly FireCalendar statistics for a custom bounding box."""
    df = fetch_bbox_harmonized_monthly(cursor, bbox)
    if df.empty:
        raise NotFoundAPIError(f"No active fire data found within bounding box '{area_id}'")

    if prov_ym is not None:
        df["provisional"] = (df["year"] * 100 + df["month"]) >= prov_ym
    else:
        df["provisional"] = False

    clim_df = compute_climatology(df)
    anom_df = compute_anomalies(df)

    if clim_df.empty or anom_df.empty:
        raise NotFoundAPIError(f"Insufficient fire history for bounding box '{area_id}'")

    means = clim_df.sort_values("month")["mean"].to_numpy(dtype=float)
    season_dict = compute_season_from_means(means)

    season = FireSeason(
        start_month=int(season_dict["start_month"]),
        peak_month=int(season_dict["peak_month"]),
        end_month=int(season_dict["end_month"]),
        share_of_annual=round(float(season_dict["share_of_annual"]), 4),
    )

    climatology = [
        MonthClimatology(
            month=int(row["month"]),
            mean=round(float(row["mean"]), 4),
            p50=round(float(row["p50"]), 4),
            p90=round(float(row["p90"]), 4),
            p95=round(float(row["p95"]), 4),
        )
        for _, row in clim_df.sort_values("month").iterrows()
    ]

    years_set: set[int] = set()
    grid: list[CalendarCell] = []
    for _, row in anom_df.sort_values(["year", "month"]).iterrows():
        y = int(row["year"])
        m = int(row["month"])
        years_set.add(y)
        is_prov = prov_ym is not None and (y * 100 + m) >= prov_ym
        cls_val = str(row["class"])
        if cls_val not in ("normal", "elevated", "extreme"):
            cls_val = "normal"
        pr = float(row["percentile_rank"])
        if math.isnan(pr):
            pr = 0.5
        grid.append(
            CalendarCell(
                year=y,
                month=m,
                value=round(float(row["value"]), 4),
                class_=cls_val,  # type: ignore[arg-type]
                percentile_rank=round(pr, 4),
                provisional=is_prov,
            )
        )

    return CalendarEnvelope(
        data=CalendarData(
            years=sorted(years_set),
            grid=grid,
            climatology=climatology,
            season=season,
        ),
        meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
    )


def get_calendar_envelope(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
) -> CalendarEnvelope:
    """Build the FireCalendar envelope for a given area."""
    cleaned_id = area_id.strip()
    if not cleaned_id:
        raise ValidationAPIError("area_id must not be empty")

    resolved = resolve_area(cursor, cleaned_id)

    cache_key = (dataset.data_version, resolved.area_id)
    if cache_key in _CALENDAR_CACHE:
        _CALENDAR_CACHE.move_to_end(cache_key)
        return _CALENDAR_CACHE[cache_key]

    prov_ym = _provisional_ym(dataset.provisional_from)

    if resolved.kind == "bbox" and resolved.bbox is not None:
        envelope = _compute_bbox_calendar(dataset, cursor, resolved.bbox, cleaned_id, prov_ym)
    else:
        target_id = resolved.area_id
        years, grid = fetch_calendar_grid(cursor, target_id, provisional_ym=prov_ym)
        if not grid and resolved.region_ids:
            # Fallback to first constituent region if preset doesn't have its own precomputed row
            target_id = resolved.region_ids[0]
            years, grid = fetch_calendar_grid(cursor, target_id, provisional_ym=prov_ym)

        if not grid:
            raise NotFoundAPIError(f"No calendar statistics found for area '{cleaned_id}'")

        climatology = fetch_climatology(cursor, target_id)
        season = fetch_season(cursor, target_id) or FireSeason(
            start_month=1,
            peak_month=1,
            end_month=1,
            share_of_annual=0.0,
        )

        envelope = CalendarEnvelope(
            data=CalendarData(
                years=years,
                grid=grid,
                climatology=climatology,
                season=season,
            ),
            meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
        )

    _CALENDAR_CACHE[cache_key] = envelope
    if len(_CALENDAR_CACHE) > _MAX_CACHE_ENTRIES:
        _CALENDAR_CACHE.popitem(last=False)

    return envelope
