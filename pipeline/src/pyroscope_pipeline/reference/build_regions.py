"""Build Bangladesh reference region catalog and H3 resolution-7 cell lookup (Chunk P03).

Reads full-resolution geoBoundaries ADM0/ADM1/ADM2 GeoJSON files from `data/raw/boundaries/`
(downloading them from the canonical geoBoundaries v6.0.0 release if not cached locally) and writes:
- `data/reference/regions.geojson` (simplified polygons < 3 MB, with all 74 regions)
- `data/reference/regions.parquet` (tabular catalog without geometry, ZSTD Parquet)
- `data/reference/region_cells.parquet` (`region_id`, `h3_r7` UINT64 for all 64 districts)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geopandas as gpd  # type: ignore[import-untyped]
import h3
import httpx
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import shapely  # type: ignore[import-untyped]
from shapely.geometry import Polygon, mapping  # type: ignore[import-untyped]
from shapely.ops import unary_union  # type: ignore[import-untyped]

from pyroscope_pipeline.common.paths import RAW_DIR, REFERENCE_DIR
from pyroscope_pipeline.reference.catalog_specs import (
    CHT_DISTRICTS,
     DISTRICT_OVERRIDES,
    DIVISION_SPECS,
    GEOBOUNDARIES_URLS,
)


def ensure_raw_boundaries(raw_boundaries_dir: Path | None = None) -> dict[str, Path]:
    """Ensure full-resolution geoBoundaries ADM0/ADM1/ADM2 files exist in `data/raw/boundaries/`."""
    bdir = raw_boundaries_dir or (RAW_DIR / "boundaries")
    bdir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for level, url in GEOBOUNDARIES_URLS.items():
        dest = bdir / f"geoBoundaries-BGD-{level}.geojson"
        if not dest.exists():
            resp = httpx.get(url, follow_redirects=True, timeout=60.0)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
        paths[level] = dest
    return paths


def _bbox_list(geom: Any) -> list[float]:
    minx, miny, maxx, maxy = geom.bounds
    return [round(float(minx), 5), round(float(miny), 5), round(float(maxx), 5), round(float(maxy), 5)]


def _simplify_geom(geom: Any, tolerance: float = 0.002) -> Any:
    simplified = geom.simplify(tolerance, preserve_topology=True)
    return shapely.set_precision(simplified, grid_size=1e-5)


def _assign_district_cells(adm2_rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Assign every Bangladesh H3 r7 cell uniquely to one ADM2 district."""
    cell_to_region: dict[str, str] = {}
    for item in adm2_rows:
        rid = item["region_id"]
        geom = item["full_geometry"]
        for c in h3.geo_to_cells(geom.__geo_interface__, 7):
            cell_to_region[c] = rid

    overlap_candidates: dict[str, list[tuple[str, Any]]] = {}
    for item in adm2_rows:
        rid = item["region_id"]
        geom = item["full_geometry"]
        shape = h3.geo_to_h3shape(geom.__geo_interface__)
        for c in h3.h3shape_to_cells_experimental(shape, 7, contain="overlap"):
            if c not in cell_to_region:
                overlap_candidates.setdefault(c, []).append((rid, geom))

    for c, cands in overlap_candidates.items():
        if len(cands) == 1:
            cell_to_region[c] = cands[0][0]
        else:
            poly = Polygon([(lon, lat) for lat, lon in h3.cell_to_boundary(c)])
            best_rid = max(cands, key=lambda pair: float(pair[1].intersection(poly).area))[0]
            cell_to_region[c] = best_rid

    rows = [
        {"region_id": rid, "h3_r7": np.uint64(int(cell_hex, 16))}
        for cell_hex, rid in cell_to_region.items()
    ]
    return pd.DataFrame(rows).sort_values(["region_id", "h3_r7"]).reset_index(drop=True)


def build_reference_datasets(
    output_dir: Path | None = None,
    raw_boundaries_dir: Path | None = None,
) -> dict[str, Any]:
    """Generate `regions.geojson`, `regions.parquet`, and `region_cells.parquet`."""
    out_dir = output_dir or REFERENCE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_paths = ensure_raw_boundaries(raw_boundaries_dir)

    adm1_gdf = gpd.read_file(raw_paths["ADM1"])
    adm2_gdf = gpd.read_file(raw_paths["ADM2"])

    adm1_geoms = {row["shapeName"]: row.geometry for _, row in adm1_gdf.iterrows()}
    adm2_records: list[dict[str, Any]] = []
    div_district_geoms: dict[str, list[Any]] = {div_id: [] for div_id, _, _ in DIVISION_SPECS.values()}

    for _, row in adm2_gdf.sort_values("shapeName").iterrows():
        raw_name = str(row["shapeName"])
        geom = row.geometry
        best_adm1_raw = max(adm1_geoms.items(), key=lambda kv: float(geom.intersection(kv[1]).area))[0]
        parent_div_id = DIVISION_SPECS[best_adm1_raw][0]
        div_district_geoms[parent_div_id].append(geom)

        if raw_name in DISTRICT_OVERRIDES:
            slug, clean_name, aliases = DISTRICT_OVERRIDES[raw_name]
        else:
            slug = raw_name.lower().replace(" ", "-")
            clean_name = raw_name
            aliases = [raw_name, f"{raw_name} District", f"{raw_name} Zila"]

        adm2_records.append(
            {
                "region_id": f"BGD-ADM2-{slug}",
                "name": clean_name,
                "level": "adm2",
                "parent_id": parent_div_id,
                "bbox": _bbox_list(geom),
                "aliases": aliases,
                "full_geometry": geom,
                "geometry": _simplify_geom(geom),
            }
        )

    adm2_records.sort(key=lambda r: str(r["region_id"]))

    adm1_records: list[dict[str, Any]] = []
    for _, (div_id, div_name, div_aliases) in sorted(DIVISION_SPECS.items(), key=lambda kv: kv[1][0]):
        div_geom = unary_union(div_district_geoms[div_id])
        adm1_records.append(
            {
                "region_id": div_id,
                "name": div_name,
                "level": "adm1",
                "parent_id": "BGD",
                "bbox": _bbox_list(div_geom),
                "aliases": div_aliases,
                "geometry": _simplify_geom(div_geom),
            }
        )

    cht_geoms = [r["full_geometry"] for r in adm2_records if r["region_id"] in CHT_DISTRICTS]
    cht_full_geom = unary_union(cht_geoms)
    preset_record = {
        "region_id": "PRESET-CHT",
        "name": "Chittagong Hill Tracts",
        "level": "preset",
        "parent_id": "BGD-ADM1-chattogram",
        "bbox": _bbox_list(cht_full_geom),
        "aliases": [
            "Chittagong Hill Tracts",
            "CHT",
            "Hill Tracts",
            "Chattogram Hill Tracts",
            "Parbatya Chattagram",
        ],
        "geometry": _simplify_geom(cht_full_geom),
    }

    bgd_full_geom = unary_union([r["full_geometry"] for r in adm2_records])
    country_record = {
        "region_id": "BGD",
        "name": "Bangladesh",
        "level": "country",
        "parent_id": None,
        "bbox": _bbox_list(bgd_full_geom),
        "aliases": ["Bangladesh", "BD", "BGD", "People's Republic of Bangladesh"],
        "geometry": _simplify_geom(bgd_full_geom),
    }

    all_records = [
        country_record,
        *adm1_records,
        *[{k: v for k, v in r.items() if k != "full_geometry"} for r in adm2_records],
        preset_record,
    ]

    features = [
        {
            "type": "Feature",
            "properties": {
                "region_id": r["region_id"],
                "name": r["name"],
                "level": r["level"],
                "parent_id": r["parent_id"],
                "bbox": r["bbox"],
                "aliases": r["aliases"],
            },
            "geometry": mapping(r["geometry"]),
        }
        for r in all_records
    ]
    geojson_path = out_dir / "regions.geojson"
    geojson_path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")),
        encoding="utf-8",
    )

    df_regions = pd.DataFrame(
        [
            {
                "region_id": r["region_id"],
                "name": r["name"],
                "level": r["level"],
                "parent_id": r["parent_id"],
                "bbox": r["bbox"],
                "aliases": r["aliases"],
            }
            for r in all_records
        ]
    )
    pq.write_table(
        pa.Table.from_pandas(df_regions, preserve_index=False),
        out_dir / "regions.parquet",
        compression="ZSTD",
        version="2.6",
    )

    df_cells = _assign_district_cells(adm2_records)
    pq.write_table(
        pa.Table.from_pandas(df_cells, preserve_index=False),
        out_dir / "region_cells.parquet",
        compression="ZSTD",
        version="2.6",
    )

    return {
        "regions_count": len(df_regions),
        "cells_count": len(df_cells),
        "geojson_kb": round(geojson_path.stat().st_size / 1024, 1),
        "cht_bbox": preset_record["bbox"],
    }
