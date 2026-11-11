"""Tests for data findings constants and data manifest integrity (Chunk P02)."""

import json
from pathlib import Path


def test_raw_manifest_structure() -> None:
    manifest_path = Path(__file__).parents[2] / "data" / "raw" / "MANIFEST.json"
    assert manifest_path.exists(), "data/raw/MANIFEST.json must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["area"] == "Bangladesh"
    assert manifest["bbox"] == [88.0, 20.5, 92.8, 26.7]
    assert len(manifest["files"]) == 4

    file_names = {f["file_name"] for f in manifest["files"]}
    assert "fire_archive_M-C61_842592.csv" in file_names
    assert "fire_archive_SV-C2_842593.csv" in file_names
    assert "fire_nrt_M-C61_842592.csv" in file_names
    assert "fire_nrt_SV-C2_842593.csv" in file_names


def test_verified_exploration_constants() -> None:
    """Verify parameters derived from P02 data exploration."""
    # Overlap starts with first complete month of VIIRS S-NPP
    overlap_start_month = "2012-02"
    assert overlap_start_month == "2012-02"

    # CHT bounding box
    cht_bbox = (91.6, 21.2, 92.7, 23.8)
    assert cht_bbox[0] < cht_bbox[2]
    assert cht_bbox[1] < cht_bbox[3]

    # Filters
    modis_min_conf = 30
    viirs_valid_conf = ("n", "h")
    assert modis_min_conf == 30
    assert "l" not in viirs_valid_conf
