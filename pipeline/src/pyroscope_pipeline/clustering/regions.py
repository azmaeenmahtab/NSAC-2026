"""District spatial assignment helpers for fire events.

Assigns fire events to Bangladesh ADM2 districts based on the reference H3 r7
cell mapping (`data/reference/region_cells.parquet`) derived from official
geoBoundaries ADM2 polygons. Events outside Bangladesh are assigned None / pd.NA.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from shapely.geometry import Point, shape  # type: ignore[import-untyped]

from pyroscope_pipeline.clustering.h3_index import latlng_to_h3_u64
from pyroscope_pipeline.common.paths import REFERENCE_DIR

_CACHED_CELL_MAP: dict[int, str] | None = None


def load_district_cells_map(reference_path: Path | str | None = None) -> dict[int, str]:
    """Load H3 resolution-7 to district_id dictionary from region_cells.parquet."""
    global _CACHED_CELL_MAP
    if _CACHED_CELL_MAP is not None and reference_path is None:
        return _CACHED_CELL_MAP

    p = Path(reference_path) if reference_path else (REFERENCE_DIR / "region_cells.parquet")
    if not p.exists():
        raise FileNotFoundError(f"Reference region cells not found at: {p}")

    df_cells = pd.read_parquet(p)
    # Ensure mapping from int(h3_r7) -> region_id
    res = {int(row[1]): str(row[0]) for row in zip(df_cells["region_id"], df_cells["h3_r7"])}
    if reference_path is None:
        _CACHED_CELL_MAP = res
    return res


def assign_districts(
    events_df: pd.DataFrame,
    cell_col: str = "h3_r7",
    cell_map: dict[int, str] | None = None,
) -> pd.DataFrame:
    """Assign district_id to events DataFrame based on H3 r7 cell index.

    Events falling outside Bangladesh reference cells will have district_id = None.
    """
    if events_df.empty:
        out = events_df.copy()
        out["district_id"] = pd.Series(dtype="string")
        return out

    mapping = cell_map if cell_map is not None else load_district_cells_map()
    r7_series = events_df[cell_col]

    # Map each cell integer to district string or None
    districts: list[str | None] = [mapping.get(int(c), None) for c in r7_series]

    out = events_df.copy()
    out["district_id"] = pd.Series(districts, dtype="string")
    return out


def lookup_point_district(
    lat: float,
    lon: float,
    cell_map: dict[int, str] | None = None,
) -> str | None:
    """Lookup district_id for a single (lat, lon) point via H3 r7 cell mapping."""
    mapping = cell_map if cell_map is not None else load_district_cells_map()
    cell_u64 = latlng_to_h3_u64(lat, lon, res=7)
    return mapping.get(cell_u64, None)


def lookup_point_in_polygon(
    lat: float,
    lon: float,
    geojson_path: Path | str | None = None,
) -> str | None:
    """Direct point-in-polygon check against simplified reference regions.geojson."""
    p = Path(geojson_path) if geojson_path else (REFERENCE_DIR / "regions.geojson")
    if not p.exists():
        return None

    with open(p, "r", encoding="utf-8") as f:
        fc = json.load(f)

    pt = Point(lon, lat)
    for feat in fc.get("features", []):
        props = feat.get("properties", {})
        if props.get("level") == "adm2":
            poly = shape(feat["geometry"])
            if poly.contains(pt):
                return str(props["region_id"])
    return None

