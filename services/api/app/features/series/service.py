"""Service logic and LRU caching for `/api/series`."""

from __future__ import annotations

from collections import OrderedDict
from typing import Literal, cast

import duckdb

from app.core.dataset import LoadedDataset
from app.core.errors import ValidationAPIError
from app.core.responses import ResponseMeta
from app.features.areas.service import resolve_area
from app.features.heatmap.service import parse_year_month
from app.features.series.repository import fetch_bbox_series, fetch_region_series
from app.features.series.schemas import SeriesEnvelope, SeriesPoint

_MAX_CACHE_ENTRIES = 256
_SERIES_CACHE: OrderedDict[tuple[object, ...], SeriesEnvelope] = OrderedDict()


def clear_series_cache() -> None:
    """Clear the in-process series LRU cache."""
    _SERIES_CACHE.clear()


def _provisional_ym_threshold(provisional_from: str | None) -> int | None:
    """Parse `provisional_from` (`YYYY-MM` or `YYYY-MM-DD`) into `year * 100 + month`."""
    if not provisional_from:
        return None
    parts = provisional_from.strip().split("-")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return int(parts[0]) * 100 + int(parts[1])
    return None


def get_series_envelope(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
    from_str: str | None = None,
    to_str: str | None = None,
) -> SeriesEnvelope:
    """Resolve `area_id`, query monthly series (with LRU cache), and build `SeriesEnvelope`."""
    resolved = resolve_area(cursor, area_id)

    ym_from: int | None = None
    ym_to: int | None = None
    canonical_from: str | None = None
    canonical_to: str | None = None

    if from_str is not None:
        _, _, ym_from, canonical_from = parse_year_month(from_str, param_name="from")
    if to_str is not None:
        _, _, ym_to, canonical_to = parse_year_month(to_str, param_name="to")

    if ym_from is not None and ym_to is not None and ym_from > ym_to:
        raise ValidationAPIError(
            f"Invalid date range: 'from' ({canonical_from}) must not be after 'to' ({canonical_to})"
        )

    cache_key = (dataset.data_version, resolved.area_id, ym_from, ym_to)
    if cache_key in _SERIES_CACHE:
        _SERIES_CACHE.move_to_end(cache_key)
        return _SERIES_CACHE[cache_key]

    if resolved.kind == "bbox":
        raw_rows = fetch_bbox_series(
            cursor=cursor,
            registered_views=dataset.registered_views,
            bbox=resolved.bbox,
            ym_from=ym_from,
            ym_to=ym_to,
        )
    else:
        raw_rows = fetch_region_series(
            cursor=cursor,
            region_ids=resolved.region_ids,
            ym_from=ym_from,
            ym_to=ym_to,
        )

    prov_ym = _provisional_ym_threshold(dataset.provisional_from)
    points: list[SeriesPoint] = []
    for y, m, raw_modis, raw_viirs, harmonized, in_overlap, source_used in raw_rows:
        ym = y * 100 + m
        # Naive splice: raw MODIS before the VIIRS overlap start (2012-02), raw VIIRS from then on
        if in_overlap and raw_viirs is not None:
            naive_splice = float(raw_viirs)
        else:
            naive_splice = float(raw_modis) if raw_modis is not None else 0.0

        src_literal = cast(
            Literal["modis_raw", "viirs_calibrated"],
            "viirs_calibrated" if source_used == "viirs_calibrated" else "modis_raw",
        )
        is_provisional = prov_ym is not None and ym >= prov_ym

        points.append(
            SeriesPoint(
                year=y,
                month=m,
                raw_modis=raw_modis,
                raw_viirs=raw_viirs,
                naive_splice=round(naive_splice, 6),
                harmonized=round(harmonized, 6),
                in_overlap=in_overlap,
                source_used=src_literal,
                provisional=is_provisional,
            )
        )

    envelope = SeriesEnvelope(
        data=points,
        meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
    )

    _SERIES_CACHE[cache_key] = envelope
    if len(_SERIES_CACHE) > _MAX_CACHE_ENTRIES:
        _SERIES_CACHE.popitem(last=False)

    return envelope
