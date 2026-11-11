"""Service logic and caching for `/api/calendar`."""

from __future__ import annotations

from collections import OrderedDict

import duckdb

from app.core.dataset import LoadedDataset
from app.core.errors import NotFoundAPIError, ValidationAPIError
from app.core.responses import ResponseMeta
from app.features.areas.service import resolve_area
from app.features.calendar.repository import (
    fetch_calendar_grid,
    fetch_climatology,
    fetch_season,
)
from app.features.calendar.schemas import (
    CalendarData,
    CalendarEnvelope,
    FireSeason,
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


def get_calendar_envelope(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
) -> CalendarEnvelope:
    """Build the FireCalendar envelope for a given area."""
    cleaned_id = area_id.strip()
    if not cleaned_id:
        raise ValidationAPIError("area_id must not be empty")

    if cleaned_id.lower().startswith("bbox:"):
        raise ValidationAPIError(
            "Custom bbox calendar statistics are currently unavailable pending D07 "
            "pipeline stats engine. Please specify a named region or preset."
        )

    resolved = resolve_area(cursor, cleaned_id)

    cache_key = (dataset.data_version, resolved.area_id)
    if cache_key in _CALENDAR_CACHE:
        _CALENDAR_CACHE.move_to_end(cache_key)
        return _CALENDAR_CACHE[cache_key]

    target_id = resolved.area_id
    prov_ym = _provisional_ym(dataset.provisional_from)

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
