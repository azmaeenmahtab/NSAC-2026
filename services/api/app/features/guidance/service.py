"""Service layer for `/api/guidance`."""

from __future__ import annotations

from datetime import UTC, datetime

import duckdb

from app.core.dataset import LoadedDataset
from app.core.errors import ValidationAPIError
from app.features.areas.service import resolve_area
from app.features.calendar.service import get_calendar_envelope
from app.features.guidance.repository import filter_guidance_items, get_all_guidance_items
from app.features.guidance.rules import stage_for
from app.features.guidance.schemas import (
    GuidanceEnvelope,
    GuidanceItem,
    GuidanceMeta,
    GuidanceStage,
)

_VALID_STAGES = {"pre_season", "in_season", "post_season", "extreme", "off_season"}


def get_guidance(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
    area_id: str,
    month: int | None = None,
    stage_override: str | None = None,
    audience: str | None = None,
) -> GuidanceEnvelope:
    """Build guidance checklist envelope for an area and month."""
    cleaned_id = area_id.strip()
    if not cleaned_id:
        raise ValidationAPIError("area_id must not be empty")

    # Validate month if supplied, else default to current UTC month
    target_month = month if month is not None else datetime.now(UTC).month
    if not (1 <= target_month <= 12):
        raise ValidationAPIError(f"month must be between 1 and 12, got {target_month}")

    # Resolve area
    resolved = resolve_area(cursor, cleaned_id)

    # Determine stage: explicit stage override or computed via calendar rules
    if stage_override:
        clean_stage = stage_override.strip().lower()
        if clean_stage not in _VALID_STAGES:
            raise ValidationAPIError(
                f"stage must be one of {sorted(_VALID_STAGES)}, got '{stage_override}'"
            )
        resolved_stage: GuidanceStage = clean_stage  # type: ignore[assignment]
    else:
        calendar_env = get_calendar_envelope(dataset, cursor, resolved.area_id)
        season = calendar_env.data.season

        latest_class = "normal"
        if calendar_env.data.grid:
            overall_latest = calendar_env.data.grid[-1]
            matching_cells = [c for c in calendar_env.data.grid if c.month == target_month]
            month_latest = matching_cells[-1] if matching_cells else None

            if (overall_latest and overall_latest.class_ == "extreme") or (
                month_latest and month_latest.class_ == "extreme"
            ):
                latest_class = "extreme"
            elif month_latest:
                latest_class = month_latest.class_

        resolved_stage = stage_for(target_month, season, latest_class=latest_class)

    # Fetch and filter items
    all_items = get_all_guidance_items()
    filtered_items: list[GuidanceItem] = filter_guidance_items(
        all_items,
        stage=resolved_stage,
        audience=audience,
    )

    return GuidanceEnvelope(
        data=filtered_items,
        meta=GuidanceMeta(
            dataVersion=dataset.data_version,
            asOf=dataset.as_of,
            stage=resolved_stage,
            disclaimer="Alerts, fire season stages, and action guidance are advisory, not an official warning system; follow local authorities.",
        ),
    )
