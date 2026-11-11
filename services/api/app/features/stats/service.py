"""Service logic and caching for yearly stats and anomalies."""

from __future__ import annotations

from collections import OrderedDict

import duckdb

from app.core.dataset import LoadedDataset
from app.core.errors import NotFoundAPIError, ValidationAPIError
from app.core.responses import ResponseMeta
from app.features.areas.service import resolve_area
from app.features.stats.repository import fetch_anomalies, fetch_yearly_stats
from app.features.stats.schemas import (
    AnomaliesEnvelope,
    YearlyStatsEnvelope,
)

_MAX_CACHE_ENTRIES = 256
_STATS_CACHE: OrderedDict[tuple[object, ...], object] = OrderedDict()
_VALID_CLASSES = {"normal", "elevated", "extreme"}


def clear_stats_cache() -> None:
    """Clear in-process cache for stats and anomalies."""
    _STATS_CACHE.clear()


def get_yearly_stats_envelope(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
) -> YearlyStatsEnvelope:
    """Return yearly aggregated burning stats envelope."""
    cleaned_id = area_id.strip()
    if not cleaned_id:
        raise ValidationAPIError("area_id must not be empty")

    if cleaned_id.lower().startswith("bbox:"):
        raise ValidationAPIError(
            "Custom bbox yearly statistics are currently unavailable pending D07 "
            "pipeline stats engine. Please specify a named region or preset."
        )

    resolved = resolve_area(cursor, cleaned_id)

    cache_key = ("yearly", dataset.data_version, resolved.area_id)
    if cache_key in _STATS_CACHE:
        _STATS_CACHE.move_to_end(cache_key)
        return _STATS_CACHE[cache_key]  # type: ignore[return-value]

    target_id = resolved.area_id
    rows = fetch_yearly_stats(cursor, target_id)
    if not rows and resolved.region_ids:
        target_id = resolved.region_ids[0]
        rows = fetch_yearly_stats(cursor, target_id)

    if not rows:
        raise NotFoundAPIError(f"No yearly statistics found for area '{cleaned_id}'")

    envelope = YearlyStatsEnvelope(
        data=rows,
        meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
    )

    _STATS_CACHE[cache_key] = envelope
    if len(_STATS_CACHE) > _MAX_CACHE_ENTRIES:
        _STATS_CACHE.popitem(last=False)

    return envelope


def get_anomalies_envelope(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
    year: int | None = None,
    class_filter: str | None = None,
) -> AnomaliesEnvelope:
    """Return anomalous fire months envelope with optional filters."""
    cleaned_id = area_id.strip()
    if not cleaned_id:
        raise ValidationAPIError("area_id must not be empty")

    if cleaned_id.lower().startswith("bbox:"):
        raise ValidationAPIError(
            "Custom bbox anomalies are currently unavailable pending D07 "
            "pipeline stats engine. Please specify a named region or preset."
        )

    if class_filter is not None:
        cleaned_class = class_filter.strip().lower()
        if cleaned_class not in _VALID_CLASSES:
            raise ValidationAPIError(
                f"Invalid class filter '{class_filter}'. Allowed: normal, elevated, extreme"
            )
        class_filter = cleaned_class

    resolved = resolve_area(cursor, cleaned_id)

    cache_key = ("anomalies", dataset.data_version, resolved.area_id, year, class_filter)
    if cache_key in _STATS_CACHE:
        _STATS_CACHE.move_to_end(cache_key)
        return _STATS_CACHE[cache_key]  # type: ignore[return-value]

    target_id = resolved.area_id
    rows = fetch_anomalies(cursor, target_id, year=year, class_filter=class_filter)
    if not rows and resolved.region_ids:
        target_id = resolved.region_ids[0]
        rows = fetch_anomalies(cursor, target_id, year=year, class_filter=class_filter)

    envelope = AnomaliesEnvelope(
        data=rows,
        meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
    )

    _STATS_CACHE[cache_key] = envelope
    if len(_STATS_CACHE) > _MAX_CACHE_ENTRIES:
        _STATS_CACHE.popitem(last=False)

    return envelope
