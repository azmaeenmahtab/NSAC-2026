"""Tests for P03 reference region catalog and H3 resolution-7 cell mapping (`data/reference/`)."""

from __future__ import annotations

import json

import duckdb
import h3
import pandas as pd

from pyroscope_pipeline.common.paths import REFERENCE_DIR


def test_reference_files_exist_and_size_bound() -> None:
    """Verify SOURCES.md, regions.geojson (< 3 MB), regions.parquet, and region_cells.parquet exist."""
    sources_md = REFERENCE_DIR / "SOURCES.md"
    geojson_path = REFERENCE_DIR / "regions.geojson"
    regions_pq = REFERENCE_DIR / "regions.parquet"
    cells_pq = REFERENCE_DIR / "region_cells.parquet"

    assert sources_md.exists(), "data/reference/SOURCES.md must exist"
    assert geojson_path.exists(), "data/reference/regions.geojson must exist"
    assert regions_pq.exists(), "data/reference/regions.parquet must exist"
    assert cells_pq.exists(), "data/reference/region_cells.parquet must exist"

    # Must be under 3 MB for web delivery
    assert geojson_path.stat().st_size < 3 * 1024 * 1024


def test_regions_catalog_hierarchy_and_aliases() -> None:
    """Verify 1 country, 8 divisions, 64 districts, and 1 CHT preset with required fields and aliases."""
    df = pd.read_parquet(REFERENCE_DIR / "regions.parquet")
    expected_cols = ["region_id", "name", "level", "parent_id", "bbox", "aliases"]
    assert list(df.columns) == expected_cols
    assert len(df) == 74
    assert df["region_id"].is_unique

    counts = df["level"].value_counts().to_dict()
    assert counts == {"adm2": 64, "adm1": 8, "country": 1, "preset": 1}

    by_id = df.set_index("region_id").to_dict(orient="index")
    assert "BGD" in by_id
    assert pd.isna(by_id["BGD"]["parent_id"])

    adm1_ids = set(df[df["level"] == "adm1"]["region_id"])
    assert "BGD-ADM1-chattogram" in adm1_ids
    for rid in adm1_ids:
        assert by_id[rid]["parent_id"] == "BGD"

    for rid in df[df["level"] == "adm2"]["region_id"]:
        assert by_id[rid]["parent_id"] in adm1_ids

    # Check CHT preset and its 3 hill districts
    assert "PRESET-CHT" in by_id
    cht = by_id["PRESET-CHT"]
    assert cht["level"] == "preset"
    assert cht["parent_id"] == "BGD-ADM1-chattogram"
    cht_aliases = list(cht["aliases"])
    assert "Chittagong Hill Tracts" in cht_aliases
    assert "CHT" in cht_aliases
    assert "Hill Tracts" in cht_aliases

    for d_id in ("BGD-ADM2-rangamati", "BGD-ADM2-bandarban", "BGD-ADM2-khagrachari"):
        assert d_id in by_id
        assert by_id[d_id]["parent_id"] == "BGD-ADM1-chattogram"

    assert "Khagrachhari" in list(by_id["BGD-ADM2-khagrachari"]["aliases"])
    assert "Chittagong" in list(by_id["BGD-ADM1-chattogram"]["aliases"])

    # Verify regions.geojson feature count matches regions.parquet
    gj = json.loads((REFERENCE_DIR / "regions.geojson").read_text(encoding="utf-8"))
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) == 74


def test_region_cells_invariants() -> None:
    """Verify region_cells.parquet has unique UINT64 H3 r7 cells across all 64 districts."""
    cells_pq = REFERENCE_DIR / "region_cells.parquet"
    con = duckdb.connect(":memory:")
    desc_rows = con.execute(
        f"DESCRIBE SELECT region_id, h3_r7 FROM read_parquet('{cells_pq.as_posix()}')"
    ).fetchall()
    col_types = {r[0]: r[1] for r in desc_rows}
    con.close()
    assert col_types["h3_r7"] == "UBIGINT"

    df_cells = pd.read_parquet(cells_pq)
    assert list(df_cells.columns) == ["region_id", "h3_r7"]
    assert df_cells["h3_r7"].is_unique, "No H3 r7 cell may appear in two districts"
    assert df_cells["region_id"].nunique() == 64
    assert 25_000 <= len(df_cells) <= 30_000

    # Spot-check H3 validity and resolution
    for u64_val in df_cells["h3_r7"].head(50):
        cell_hex = format(int(u64_val), "x")
        assert len(cell_hex) == 15
        assert h3.is_valid_cell(cell_hex)
        assert h3.get_resolution(cell_hex) == 7
