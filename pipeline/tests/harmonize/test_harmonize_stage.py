"""Tests for D06 Harmonization run, downscaling, aggregate-up, and jump metrics."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from pyroscope_pipeline.harmonize.build import build_harmonization
from pyroscope_pipeline.harmonize.downscale import downscale_to_cells
from pyroscope_pipeline.harmonize.jump_metrics import compute_jump_metrics
from pyroscope_pipeline.harmonize.run import (
    CALIBRATION_REPORT_ARROW_SCHEMA,
    HARMONIZED_CELL_ARROW_SCHEMA,
    HARMONIZED_REGION_ARROW_SCHEMA,
    run_harmonization,
)
from pyroscope_pipeline.harmonize.units import (
    assign_calibration_units,
)


@pytest.fixture
def s01_fixtures() -> tuple[pd.DataFrame, pd.DataFrame, list[str], dict[str, str], list[str]]:
    """Load the deterministic S01 fixtures where VIIRS = 3 x MODIS."""
    from pyroscope_pipeline.common.paths import FIXTURES_DIR

    reg_df = pd.read_parquet(FIXTURES_DIR / "monthly_region.parquet")
    # Filter to district level only (remove country BGD if present in fixture)
    dist_reg_df = reg_df[reg_df["region_id"].str.startswith("BGD-ADM2-")].copy()

    # Create synthetic cell table consistent with districts
    cell_rows = []
    for _, row in dist_reg_df.iterrows():
        rid = str(row["region_id"])
        c_base = 609056049470636031 if rid == "BGD-ADM2-alpha" else 609056049940398079
        cell_rows.append({
            "h3_r7": np.uint64(c_base),
            "h3_r6": np.uint64(599056049470636031),
            "h3_r5": np.uint64(589056049470636031),
            "district_id": rid,
            "sensor_family": str(row["sensor_family"]),
            "year": np.int16(row["year"]),
            "month": np.int8(row["month"]),
            "event_count": np.int32(row["event_count"]),
            "frp_sum": float(row["frp_sum"]),
        })
    cell_df = pd.DataFrame(cell_rows)

    districts = ["BGD-ADM2-alpha", "BGD-ADM2-beta"]
    divisions = ["BGD-ADM1-central"]
    dist_to_div = {
        "BGD-ADM2-alpha": "BGD-ADM1-central",
        "BGD-ADM2-beta": "BGD-ADM1-central",
    }
    return dist_reg_df, cell_df, districts, dist_to_div, divisions


def test_s01_fixture_exact_recovery(s01_fixtures: tuple[pd.DataFrame, pd.DataFrame, list[str], dict[str, str], list[str]]) -> None:
    """S01 fixture (VIIRS = 3 x MODIS): CV RMSE is 0 within 1e-9 and harmonized == MODIS."""
    dist_reg_df, cell_df, districts, dist_to_div, divisions = s01_fixtures

    harm_reg, cal_rep, _harm_cell, _diag = build_harmonization(
        monthly_region_df=dist_reg_df,
        monthly_cell_df=cell_df,
        district_ids=districts,
        district_to_division=dist_to_div,
        divisions=divisions,
        min_mean_monthly_modis=3.0,
        month_pool_width=1,
        overlap_start=(2012, 2),
    )

    # 1. Calibration report asserts
    assert len(cal_rep) > 0
    for _, row in cal_rep.iterrows():
        # Either QM or ratio achieves near-zero error
        min_rmse = min(float(row["cv_rmse_qm"]), float(row["cv_rmse_ratio"]))
        assert min_rmse < 1e-8, f"Unit {row['calibration_unit_id']} failed to recover 3x scaling"

    # 2. Overlap period: harmonized == raw_modis everywhere
    overlap_districts = harm_reg[harm_reg["in_overlap"] & harm_reg["region_id"].isin(districts)]
    diff = np.abs(overlap_districts["harmonized"] - overlap_districts["raw_modis"])
    assert np.max(diff) < 1e-6, "Harmonized series deviated from raw MODIS during overlap"


def test_aggregate_up_conservation(s01_fixtures: tuple[pd.DataFrame, pd.DataFrame, list[str], dict[str, str], list[str]]) -> None:
    """Bottom-up aggregation: country BGD equals the exact sum of districts."""
    dist_reg_df, cell_df, districts, dist_to_div, divisions = s01_fixtures

    harm_reg, _, _, _ = build_harmonization(
        monthly_region_df=dist_reg_df,
        monthly_cell_df=cell_df,
        district_ids=districts,
        district_to_division=dist_to_div,
        divisions=divisions,
    )

    # For every (year, month), sum of districts must equal country BGD
    for (y, m), grp in harm_reg.groupby(["year", "month"]):
        dist_grp = grp[grp["region_id"].isin(districts)]
        bgd_row = grp[grp["region_id"] == "BGD"].iloc[0]

        assert bgd_row["raw_modis"] == pytest.approx(dist_grp["raw_modis"].sum(), abs=1e-6)
        assert bgd_row["harmonized"] == pytest.approx(dist_grp["harmonized"].sum(), abs=1e-6)

        if bgd_row["in_overlap"]:
            assert bgd_row["raw_viirs"] == pytest.approx(dist_grp["raw_viirs"].sum(), abs=1e-6)


def test_downscale_conservation_and_unallocated() -> None:
    """Downscale conservation: cell sum matches district total; unallocated tracked."""
    dist_df = pd.DataFrame([
        # District A: VIIRS > 0
        {"region_id": "DIST-A", "year": 2020, "month": 5, "raw_modis": 10.0, "raw_viirs": 30.0, "harmonized": 10.0, "source_used": "viirs_calibrated", "method": "ratio", "calibration_unit_id": "DIST-A", "in_overlap": True},
        # District B: VIIRS == 0, but harmonized > 0 (transfer function positive offset)
        {"region_id": "DIST-B", "year": 2020, "month": 5, "raw_modis": 0.0, "raw_viirs": 0.0, "harmonized": 2.5, "source_used": "viirs_calibrated", "method": "quantile_map", "calibration_unit_id": "DIST-B", "in_overlap": True},
    ])

    cell_df = pd.DataFrame([
        {"h3_r7": 1, "h3_r6": 1, "h3_r5": 1, "district_id": "DIST-A", "sensor_family": "VIIRS", "year": 2020, "month": 5, "event_count": 10, "frp_sum": 20.0},
        {"h3_r7": 2, "h3_r6": 1, "h3_r5": 1, "district_id": "DIST-A", "sensor_family": "VIIRS", "year": 2020, "month": 5, "event_count": 20, "frp_sum": 40.0},
    ])

    harm_cells, unallocated = downscale_to_cells(cell_df, dist_df)

    # District A cells conserve total: 10/30 * 10 + 10/30 * 20 = 10.0
    sum_a = harm_cells[harm_cells["district_id"] == "DIST-A"]["harmonized"].sum()
    assert sum_a == pytest.approx(10.0, abs=1e-6)

    # District B has 0 VIIRS cells, so 2.5 is tracked as unallocated
    assert unallocated == pytest.approx(2.5, abs=1e-6)


def test_sparse_district_fallback_to_parent() -> None:
    """Sparse district (mean MODIS < 3) falls back to parent division."""
    districts = ["DIST-ACTIVE", "DIST-SPARSE"]
    dist_to_div = {"DIST-ACTIVE": "DIV-1", "DIST-SPARSE": "DIV-1"}
    means = {"DIST-ACTIVE": 15.0, "DIST-SPARSE": 0.5}

    assignments = assign_calibration_units(
        district_ids=districts,
        district_to_division=dist_to_div,
        district_mean_modis=means,
        min_mean_monthly_modis=3.0,
    )

    assert assignments["DIST-ACTIVE"] == ("DIST-ACTIVE", False)
    assert assignments["DIST-SPARSE"] == ("DIV-1", True)


def test_jump_metrics_synthetic() -> None:
    """Jump metrics on a 3x synthetic step jump show naive_ratio ~3 and harmonized_ratio ~1."""
    rows = []
    # 2007-2011: MODIS 100/yr
    for y in range(2007, 2012):
        for m in range(1, 13):
            rows.append({
                "region_id": "BGD", "year": y, "month": m,
                "raw_modis": 10.0, "raw_viirs": np.nan, "harmonized": 10.0,
                "source_used": "modis_raw", "method": "none",
                "calibration_unit_id": "BGD", "in_overlap": False,
            })
    # 2012-2016: raw VIIRS jumps by 3x (30/month = 360/yr), but harmonized recovers 10/month (120/yr)
    for y in range(2012, 2017):
        for m in range(1, 13):
            rows.append({
                "region_id": "BGD", "year": y, "month": m,
                "raw_modis": 10.0, "raw_viirs": 30.0, "harmonized": 10.0,
                "source_used": "viirs_calibrated", "method": "ratio",
                "calibration_unit_id": "BGD", "in_overlap": True,
            })

    df = pd.DataFrame(rows)
    metrics = compute_jump_metrics(df)

    # Naive ratio: 360 / 120 = 3.0
    assert metrics["naive_ratio"] == pytest.approx(3.0, abs=0.05)
    # Harmonized ratio: 120 / 120 = 1.0
    assert metrics["harmonized_ratio"] == pytest.approx(1.0, abs=0.05)


def test_determinism_and_runner(tmp_path: Path) -> None:
    """Ensure run_harmonization produces identical output bytes on reruns."""
    from pyroscope_pipeline.aggregate.run import run_aggregation
    from pyroscope_pipeline.fixtures.make_fixtures import generate_fixtures

    fixture_dir = tmp_path / "fixtures"
    generate_fixtures(fixture_dir)

    # Run aggregation stage
    interim_dir = tmp_path / "interim"
    interim_dir.mkdir(parents=True, exist_ok=True)

    # Prepare events for aggregation
    events_mock = pd.DataFrame([
        {"event_id": 1, "sensor_family": "MODIS", "year": 2015, "month": 5, "h3_r7": np.uint64(609056049470636031), "h3_r6": np.uint64(599056049470636031), "h3_r5": np.uint64(589056049470636031), "district_id": "BGD-ADM2-alpha", "frp_sum": 10.0, "start_ts": "2015-05-02T10:00:00Z"},
        {"event_id": 2, "sensor_family": "VIIRS", "year": 2015, "month": 5, "h3_r7": np.uint64(609056049470636031), "h3_r6": np.uint64(599056049470636031), "h3_r5": np.uint64(589056049470636031), "district_id": "BGD-ADM2-alpha", "frp_sum": 5.0, "start_ts": "2015-05-02T10:00:00Z"},
    ])
    events_mock["start_ts"] = pd.to_datetime(events_mock["start_ts"], utc=True)
    events_mock.to_parquet(interim_dir / "events.parquet", compression="ZSTD")

    # Run aggregation
    run_aggregation(
        interim_dir=interim_dir,
        reference_dir=fixture_dir,
        explicit_end_ym=(2020, 12),
        explicit_viirs_start_ym=(2012, 2),
        explicit_modis_start_ym=(2000, 11),
    )

    # Run harmonization twice
    diag1 = run_harmonization(
        interim_dir=interim_dir,
        reference_dir=fixture_dir,
        overlap_start=(2012, 2),
        overlap_end=(2020, 12),
    )

    harm_reg_path = interim_dir / "harmonized_region.parquet"
    hash1 = hashlib.sha256(harm_reg_path.read_bytes()).hexdigest()

    diag2 = run_harmonization(
        interim_dir=interim_dir,
        reference_dir=fixture_dir,
        overlap_start=(2012, 2),
        overlap_end=(2020, 12),
    )
    hash2 = hashlib.sha256(harm_reg_path.read_bytes()).hexdigest()

    assert hash1 == hash2, "Harmonization must be strictly deterministic across repeated runs"
    assert diag1["naive_ratio"] == diag2["naive_ratio"]

    # Validate Arrow schemas
    reg_table = pq.read_table(harm_reg_path)
    assert reg_table.schema.names == HARMONIZED_REGION_ARROW_SCHEMA.names

    cal_table = pq.read_table(interim_dir / "calibration_report.parquet")
    assert cal_table.schema.names == CALIBRATION_REPORT_ARROW_SCHEMA.names

    cell_table = pq.read_table(interim_dir / "harmonized_cell.parquet")
    assert cell_table.schema.names == HARMONIZED_CELL_ARROW_SCHEMA.names
