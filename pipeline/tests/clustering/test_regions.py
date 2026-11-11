"""Unit tests for district assignment and reference H3 mapping (Chunk D03)."""

from __future__ import annotations

import pandas as pd

from pyroscope_pipeline.clustering.h3_index import latlng_to_h3_u64
from pyroscope_pipeline.clustering.regions import (
    assign_districts,
    load_district_cells_map,
    lookup_point_district,
    lookup_point_in_polygon,
)


def test_load_district_cells_map() -> None:
    """Verify loading reference cell mapping from region_cells.parquet."""
    cell_map = load_district_cells_map()
    assert len(cell_map) > 25000
    unique_districts = set(cell_map.values())
    assert len(unique_districts) == 64
    assert "BGD-ADM2-rangamati" in unique_districts
    assert "BGD-ADM2-bandarban" in unique_districts
    assert "BGD-ADM2-dhaka" in unique_districts


def test_lookup_point_inside_rangamati_and_bay_of_bengal() -> None:
    """Verify point inside Rangamati returns BGD-ADM2-rangamati, and Bay of Bengal returns None."""
    cell_map = load_district_cells_map()

    # Point in Rangamati hill tracts (22.65 N, 92.18 E)
    rangamati_district = lookup_point_district(22.65, 92.18, cell_map=cell_map)
    assert rangamati_district == "BGD-ADM2-rangamati"

    # Deep Bay of Bengal (20.0 N, 90.0 E) -> outside Bangladesh land boundary
    sea_district = lookup_point_district(20.0, 90.0, cell_map=cell_map)
    assert sea_district is None

    # Offshore Indian Ocean / south of St. Martin's (19.5 N, 91.0 E)
    offshore_district = lookup_point_district(19.5, 91.0, cell_map=cell_map)
    assert offshore_district is None


def test_point_in_polygon_agreement() -> None:
    """Verify H3 cell lookup agrees with direct geojson polygon containment for Rangamati."""
    poly_district = lookup_point_in_polygon(22.65, 92.18)
    assert poly_district == "BGD-ADM2-rangamati"

    sea_poly = lookup_point_in_polygon(20.0, 90.0)
    assert sea_poly is None


def test_assign_districts_dataframe() -> None:
    """Verify assign_districts populates district_id column with strings and nulls."""
    cell_map = load_district_cells_map()

    r7_rangamati = latlng_to_h3_u64(22.65, 92.18, 7)
    r7_sea = latlng_to_h3_u64(20.0, 90.0, 7)

    df = pd.DataFrame({
        "event_id": [1, 2],
        "h3_r7": [r7_rangamati, r7_sea],
    })

    assigned = assign_districts(df, cell_col="h3_r7", cell_map=cell_map)
    assert "district_id" in assigned.columns
    assert assigned["district_id"].iloc[0] == "BGD-ADM2-rangamati"
    assert pd.isna(assigned["district_id"].iloc[1])

