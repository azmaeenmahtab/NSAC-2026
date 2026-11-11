"""Service logic, validation, and LRU caching for `/api/heatmap`."""

from __future__ import annotations

import re
from collections import OrderedDict
from typing import cast

import duckdb
import numpy as np

from app.core.dataset import LoadedDataset
from app.core.errors import ValidationAPIError
from app.core.responses import ResponseMeta
from app.features.areas.service import parse_bbox_string
from app.features.heatmap.repository import fetch_latest_year_month, query_heatmap_cells
from app.features.heatmap.schemas import (
    HeatmapCell,
    HeatmapData,
    HeatmapEnvelope,
    HeatmapMetric,
    HeatmapStats,
)

MAX_HEATMAP_CELLS = 40_000
_MAX_CACHE_ENTRIES = 256
_YM_RE = re.compile(r"^(\d{4})-(\d{2})$")
_ALLOWED_METRICS = {"harmonized", "raw_modis", "raw_viirs"}
_ALLOWED_RES = {5, 6, 7}

_HEATMAP_CACHE: OrderedDict[tuple[object, ...], HeatmapEnvelope] = OrderedDict()


def clear_heatmap_cache() -> None:
    """Clear the in-process heatmap LRU cache."""
    _HEATMAP_CACHE.clear()


def parse_year_month(raw: str, param_name: str = "from") -> tuple[int, int, int, str]:
    """Parse a `YYYY-MM` string into `(year, month, year*100+month, canonical_str)`.

    Raises:
        ValidationAPIError: (HTTP 400) if malformed or out of calendar range.
    """
    m = _YM_RE.match(raw.strip())
    if not m:
        raise ValidationAPIError(f"Invalid '{param_name}' parameter '{raw}': expected YYYY-MM")
    year = int(m.group(1))
    month = int(m.group(2))
    if not (1990 <= year <= 2100) or not (1 <= month <= 12):
        raise ValidationAPIError(
            f"Invalid '{param_name}' parameter '{raw}': year must be 1990..2100 and month 01..12"
        )
    return (year, month, year * 100 + month, f"{year:04d}-{month:02d}")


def _default_date_window(cursor: duckdb.DuckDBPyConnection) -> tuple[str, str]:
    """Compute the default 12-month window ending at the dataset's latest month."""
    end_y, end_m = fetch_latest_year_month(cursor)
    total_months = end_y * 12 + (end_m - 1) - 11
    start_y = total_months // 12
    start_m = (total_months % 12) + 1
    return (f"{start_y:04d}-{start_m:02d}", f"{end_y:04d}-{end_m:02d}")


def _default_resolution(bbox: tuple[float, float, float, float]) -> int:
    """Choose default H3 resolution based on bbox area span."""
    west, south, east, north = bbox
    area_deg2 = (east - west) * (north - south)
    if area_deg2 > 25.0:
        return 6
    return 7


def get_heatmap_envelope(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    bbox_str: str,
    from_str: str | None = None,
    to_str: str | None = None,
    metric: str = "harmonized",
    res: int | None = None,
    max_cells: int = MAX_HEATMAP_CELLS,
) -> HeatmapEnvelope:
    """Validate parameters, query DuckDB (or LRU cache), and build `HeatmapEnvelope`."""
    bbox = parse_bbox_string(bbox_str)

    cleaned_metric = metric.strip().lower()
    if cleaned_metric not in _ALLOWED_METRICS:
        raise ValidationAPIError(
            f"Invalid metric '{metric}'. Allowed values: harmonized, raw_modis, raw_viirs"
        )
    typed_metric = cast(HeatmapMetric, cleaned_metric)

    chosen_res = _default_resolution(bbox) if res is None else int(res)
    if chosen_res not in _ALLOWED_RES:
        raise ValidationAPIError(f"Invalid H3 resolution '{res}'. Allowed values: 5, 6, 7")

    if from_str is None or to_str is None:
        def_from, def_to = _default_date_window(cursor)
        from_str = from_str or def_from
        to_str = to_str or def_to

    _, _, ym_from, canonical_from = parse_year_month(from_str, param_name="from")
    _, _, ym_to, canonical_to = parse_year_month(to_str, param_name="to")
    if ym_from > ym_to:
        raise ValidationAPIError(
            f"Invalid date range: 'from' ({canonical_from}) must not be after 'to' ({canonical_to})"
        )

    cache_key = (
        dataset.data_version,
        bbox,
        ym_from,
        ym_to,
        typed_metric,
        chosen_res,
        max_cells,
    )
    if cache_key in _HEATMAP_CACHE:
        _HEATMAP_CACHE.move_to_end(cache_key)
        return _HEATMAP_CACHE[cache_key]

    raw_rows = query_heatmap_cells(
        cursor=cursor,
        registered_views=dataset.registered_views,
        bbox=bbox,
        ym_from=ym_from,
        ym_to=ym_to,
        metric=typed_metric,
        res=chosen_res,
    )

    if len(raw_rows) > max_cells:
        raise ValidationAPIError(
            f"Query returned {len(raw_rows)} cells, exceeding maximum {max_cells}. "
            "Use a coarser resolution (res=5 or res=6) or a smaller bounding box."
        )

    cells = [
        HeatmapCell(h3=format(int(cell_int), "x"), value=round(float(val), 6))
        for cell_int, val in raw_rows
    ]

    if cells:
        vals_arr = np.array([c.value for c in cells], dtype=np.float64)
        stats = HeatmapStats(
            min=round(float(np.min(vals_arr)), 6),
            p50=round(float(np.percentile(vals_arr, 50)), 6),
            p95=round(float(np.percentile(vals_arr, 95)), 6),
            max=round(float(np.max(vals_arr)), 6),
            sum=round(float(np.sum(vals_arr)), 6),
            count=len(cells),
        )
    else:
        stats = HeatmapStats(min=0.0, p50=0.0, p95=0.0, max=0.0, sum=0.0, count=0)

    envelope = HeatmapEnvelope(
        data=HeatmapData(
            res=chosen_res,
            metric=typed_metric,
            from_month=canonical_from,
            to_month=canonical_to,
            cells=cells,
            stats=stats,
        ),
        meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
    )

    _HEATMAP_CACHE[cache_key] = envelope
    if len(_HEATMAP_CACHE) > _MAX_CACHE_ENTRIES:
        _HEATMAP_CACHE.popitem(last=False)

    return envelope
