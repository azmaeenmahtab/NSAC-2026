"""FastAPI router for `/api/heatmap`."""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.dataset import LoadedDataset
from app.core.db import get_dataset, get_db_cursor
from app.core.errors import ValidationAPIError
from app.features.areas import resolve_area
from app.features.heatmap.schemas import HeatmapEnvelope
from app.features.heatmap.service import get_heatmap_envelope

router = APIRouter(prefix="/api", tags=["Heatmap"])

DatasetDep = Annotated[LoadedDataset, Depends(get_dataset)]
CursorDep = Annotated[duckdb.DuckDBPyConnection, Depends(get_db_cursor)]


@router.get("/heatmap", operation_id="getHeatmap", response_model=HeatmapEnvelope)
async def get_heatmap(
    dataset: DatasetDep,
    cursor: CursorDep,
    bbox: Annotated[
        str | None,
        Query(description="Bounding box 'west,south,east,north'"),
    ] = None,
    area: Annotated[
        str | None,
        Query(description="Area ID or preset ID (e.g. 'PRESET-CHT', 'BGD')"),
    ] = None,
    area_id: Annotated[
        str | None,
        Query(description="Alias for area"),
    ] = None,
    from_param: Annotated[
        str | None,
        Query(alias="from", description="Start year-month YYYY-MM"),
    ] = None,
    to_param: Annotated[
        str | None,
        Query(alias="to", description="End year-month YYYY-MM"),
    ] = None,
    metric: Annotated[
        str,
        Query(description="Metric: harmonized | raw_modis | raw_viirs"),
    ] = "harmonized",
    res: Annotated[
        int | None,
        Query(description="H3 resolution: 5, 6, or 7"),
    ] = None,
) -> HeatmapEnvelope:
    """Retrieve H3 hexagonal cells with fire density within a bounding box or area."""
    effective_bbox = bbox
    if not effective_bbox:
        target_area = area or area_id
        if target_area:
            resolved = resolve_area(cursor, target_area)
            effective_bbox = (
                f"{resolved.bbox[0]},{resolved.bbox[1]},{resolved.bbox[2]},{resolved.bbox[3]}"
            )
        else:
            raise ValidationAPIError("Query parameter 'bbox' or 'area' (or 'area_id') is required")

    return get_heatmap_envelope(
        dataset=dataset,
        cursor=cursor,
        bbox_str=effective_bbox,
        from_str=from_param,
        to_str=to_param,
        metric=metric,
        res=res,
    )
