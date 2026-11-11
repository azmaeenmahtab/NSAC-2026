"""Service logic for listing areas and resolving `area_id` or `bbox:<w>,<s>,<e>,<n>`."""

from __future__ import annotations

import math

import duckdb

from app.core.dataset import LoadedDataset
from app.core.errors import NotFoundAPIError, ValidationAPIError
from app.core.responses import ResponseMeta
from app.features.areas.repository import (
    fetch_area_by_id,
    fetch_areas,
    fetch_child_region_ids,
)
from app.features.areas.schemas import AreasEnvelope, ResolvedArea

_ALLOWED_LEVEL_FILTERS = {"country", "adm1", "adm2", "division", "district", "preset"}

_PRESET_DISTRICTS: dict[str, tuple[str, ...]] = {
    "PRESET-CHT": (
        "BGD-ADM2-bandarban",
        "BGD-ADM2-khagrachari",
        "BGD-ADM2-rangamati",
    ),
}


def parse_bbox_string(
    raw_bbox: str,
    max_span_deg: float = 20.0,
) -> tuple[float, float, float, float]:
    """Parse and validate a `w,s,e,n` or `bbox:w,s,e,n` bounding box string.

    Raises:
        ValidationAPIError: (HTTP 400) if format, numeric conversion, ordering, or range fails.
    """
    text = raw_bbox.strip()
    if text.lower().startswith("bbox:"):
        text = text[5:].strip()

    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 4:
        raise ValidationAPIError(
            f"Invalid bbox '{raw_bbox}': expected 4 comma-separated numbers 'west,south,east,north'"
        )

    try:
        west, south, east, north = (float(p) for p in parts)
    except ValueError as exc:
        raise ValidationAPIError(
            f"Invalid bbox '{raw_bbox}': coordinates must be finite numbers"
        ) from exc

    if not all(math.isfinite(val) for val in (west, south, east, north)):
        raise ValidationAPIError(f"Invalid bbox '{raw_bbox}': coordinates must be finite numbers")

    if not (-180.0 <= west <= 180.0 and -180.0 <= east <= 180.0):
        raise ValidationAPIError(
            f"Invalid bbox '{raw_bbox}': longitude must be within [-180, 180]"
        )
    if not (-90.0 <= south <= 90.0 and -90.0 <= north <= 90.0):
        raise ValidationAPIError(
            f"Invalid bbox '{raw_bbox}': latitude must be within [-90, 90]"
        )
    if west >= east:
        raise ValidationAPIError(
            f"Invalid bbox '{raw_bbox}': west ({west}) must be strictly less than east ({east})"
        )
    if south >= north:
        raise ValidationAPIError(
            f"Invalid bbox '{raw_bbox}': south ({south}) must be strictly less than north ({north})"
        )
    if (east - west) > max_span_deg or (north - south) > max_span_deg:
        raise ValidationAPIError(
            f"Invalid bbox '{raw_bbox}': span exceeds maximum allowed {max_span_deg} degrees"
        )

    return (west, south, east, north)


def validate_level_filter(level: str | None) -> str | None:
    """Validate optional `?level=` query filter."""
    if level is None:
        return None
    cleaned = level.strip().lower()
    if cleaned not in _ALLOWED_LEVEL_FILTERS:
        allowed_str = ", ".join(sorted(_ALLOWED_LEVEL_FILTERS))
        raise ValidationAPIError(
            f"Invalid area level '{level}'. Allowed values: {allowed_str}"
        )
    return cleaned


def list_areas_envelope(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    level: str | None = None,
) -> AreasEnvelope:
    """Return the `/api/areas` envelope filtered by `level`."""
    validated_level = validate_level_filter(level)
    items = fetch_areas(cursor, level=validated_level)
    return AreasEnvelope(
        data=items,
        meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
    )


def resolve_area(
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
) -> ResolvedArea:
    """Resolve `area_id` (region ID, preset ID, or `bbox:<w>,<s>,<e>,<n>`) for downstream queries.

    Raises:
        ValidationAPIError: (400) if `area_id` is empty or has a malformed `bbox:` string.
        NotFoundAPIError: (404) if a named region/preset ID does not exist in `regions`.
    """
    cleaned = area_id.strip()
    if not cleaned:
        raise ValidationAPIError("area_id must not be empty")

    if cleaned.lower().startswith("bbox:"):
        w, s, e, n = parse_bbox_string(cleaned)
        canonical = f"bbox:{w},{s},{e},{n}"
        return ResolvedArea(
            area_id=canonical,
            kind="bbox",
            level="bbox",
            name=f"Custom BBox ({w:.3f}, {s:.3f}, {e:.3f}, {n:.3f})",
            region_ids=(),
            bbox=(w, s, e, n),
        )

    item = fetch_area_by_id(cursor, cleaned)
    if item is None:
        raise NotFoundAPIError(f"Unknown area_id '{cleaned}'")

    bbox_tuple: tuple[float, float, float, float] = (
        float(item.bbox[0]),
        float(item.bbox[1]),
        float(item.bbox[2]),
        float(item.bbox[3]),
    )

    if item.level == "preset":
        preset_ids = _PRESET_DISTRICTS.get(item.id, (item.id,))
        return ResolvedArea(
            area_id=item.id,
            kind="preset",
            level=item.level,
            name=item.name,
            region_ids=preset_ids,
            bbox=bbox_tuple,
        )

    if item.level in ("adm1", "division"):
        children = fetch_child_region_ids(cursor, item.id)
        region_ids = tuple(children) if children else (item.id,)
    else:
        region_ids = (item.id,)

    return ResolvedArea(
        area_id=item.id,
        kind="region",
        level=item.level,
        name=item.name,
        region_ids=region_ids,
        bbox=bbox_tuple,
    )
