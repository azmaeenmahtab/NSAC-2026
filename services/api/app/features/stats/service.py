"""Service logic and caching for yearly stats and anomalies."""

from __future__ import annotations

import math
from collections import OrderedDict

import duckdb
from pyroscope_pipeline.stats import (  # type: ignore[import-untyped]
    compute_anomalies,
    compute_yearly,
)

from app.core.dataset import LoadedDataset
from app.core.errors import NotFoundAPIError, ValidationAPIError
from app.core.responses import ResponseMeta
from app.features.areas.service import resolve_area
from app.features.stats.repository import (
    fetch_anomalies,
    fetch_bbox_harmonized_monthly,
    fetch_bbox_monthly_frp,
    fetch_yearly_stats,
)
from app.features.stats.schemas import (
    AnomaliesEnvelope,
    AnomalyItem,
    YearlyStatRow,
    YearlyStatsEnvelope,
)

_MAX_CACHE_ENTRIES = 256
_STATS_CACHE: OrderedDict[tuple[object, ...], object] = OrderedDict()
_VALID_CLASSES = {"normal", "elevated", "extreme"}


def clear_stats_cache() -> None:
    """Clear in-process cache for stats and anomalies."""
    _STATS_CACHE.clear()


def _compute_bbox_yearly_stats(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    bbox: tuple[float, float, float, float],
    area_id: str,
) -> YearlyStatsEnvelope:
    """Compute on-the-fly annual burn statistics for a custom bounding box."""
    df = fetch_bbox_harmonized_monthly(cursor, bbox)
    if df.empty:
        raise NotFoundAPIError(f"No active fire data found within bounding box '{area_id}'")

    yearly_df = compute_yearly(df)
    if yearly_df.empty:
        raise NotFoundAPIError(
            f"No complete years of fire data found within bounding box '{area_id}'"
        )

    frp_map = fetch_bbox_monthly_frp(cursor, bbox)
    frp_by_year: dict[int, float] = {}
    for (y, _), frp_val in frp_map.items():
        frp_by_year[y] = frp_by_year.get(y, 0.0) + frp_val

    rows: list[YearlyStatRow] = []
    for _, row in yearly_df.iterrows():
        y = int(row["year"])
        frp_val = frp_by_year.get(y, float(row["frp_sum"]))
        harm_tot = round(float(row["harmonized_total"]), 4)
        frp_tot = round(frp_val, 4)
        rows.append(
            YearlyStatRow(
                year=y,
                harmonized_total=harm_tot,
                frp_sum=frp_tot,
                rank=int(row["rank"]),
                vs_mean_pct=round(float(row["vs_mean_pct"]), 4),
                peak_month=int(row["peak_month"]),
                total_events=round(harm_tot),
                total_frp_mw=frp_tot,
            )
        )

    return YearlyStatsEnvelope(
        data=rows,
        meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
    )


def _compute_bbox_anomalies(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    bbox: tuple[float, float, float, float],
    area_id: str,
    year: int | None = None,
    class_filter: str | None = None,
) -> AnomaliesEnvelope:
    """Compute on-the-fly monthly anomalies for a custom bounding box."""
    df = fetch_bbox_harmonized_monthly(cursor, bbox)
    if df.empty:
        raise NotFoundAPIError(f"No active fire data found within bounding box '{area_id}'")

    anom_df = compute_anomalies(df)
    rows: list[AnomalyItem] = []
    for _, row in anom_df.iterrows():
        y = int(row["year"])
        m = int(row["month"])
        cls_val = str(row["class"])
        if cls_val not in _VALID_CLASSES:
            cls_val = "normal"
        if year is not None and y != year:
            continue
        if class_filter is not None and cls_val != class_filter:
            continue
        pr = float(row["percentile_rank"])
        if math.isnan(pr):
            pr = 0.5
        rows.append(
            AnomalyItem(
                year=y,
                month=m,
                value=round(float(row["value"]), 4),
                percentile_rank=round(pr, 4),
                class_=cls_val,  # type: ignore[arg-type]
            )
        )

    return AnomaliesEnvelope(
        data=rows,
        meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
    )


def get_yearly_stats_envelope(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
) -> YearlyStatsEnvelope:
    """Return yearly aggregated burning stats envelope."""
    cleaned_id = area_id.strip()
    if not cleaned_id:
        raise ValidationAPIError("area_id must not be empty")

    resolved = resolve_area(cursor, cleaned_id)

    cache_key = ("yearly", dataset.data_version, resolved.area_id)
    if cache_key in _STATS_CACHE:
        _STATS_CACHE.move_to_end(cache_key)
        return _STATS_CACHE[cache_key]  # type: ignore[return-value]

    if resolved.kind == "bbox" and resolved.bbox is not None:
        envelope = _compute_bbox_yearly_stats(dataset, cursor, resolved.bbox, cleaned_id)
    else:
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

    if resolved.kind == "bbox" and resolved.bbox is not None:
        envelope = _compute_bbox_anomalies(
            dataset, cursor, resolved.bbox, cleaned_id, year=year, class_filter=class_filter
        )
    else:
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
