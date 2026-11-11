"""Tests for monthly aggregation engine per D04 specification."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from pyroscope_pipeline.aggregate.coverage import (
    determine_last_complete_month,
    family_coverage_start,
    generate_dense_months,
)
from pyroscope_pipeline.aggregate.monthly import (
    aggregate_monthly_cell,
    aggregate_monthly_region,
    filter_events_by_coverage,
    verify_invariants,
)
from pyroscope_pipeline.aggregate.run import (
    MONTHLY_CELL_ARROW_SCHEMA,
    MONTHLY_REGION_ARROW_SCHEMA,
    run_aggregation,
)


def make_ten_event_fixture() -> tuple[pd.DataFrame, list[str]]:
    """Build the hand-calculated 10-event fixture specified in D04."""
    # H3 r7 cells (using realistic uint64 indices)
    cell_1 = np.uint64(609056049470636031)  # in alpha
    cell_2 = np.uint64(609056049487413247)  # in alpha
    cell_3 = np.uint64(609056049940398079)  # in beta
    cell_out = np.uint64(609056049957175295)  # outside ROI

    r6 = np.uint64(599056049470636031)
    r5 = np.uint64(589056049470636031)

    districts = ["BGD-ADM2-alpha", "BGD-ADM2-beta"]

    events = [
        # MODIS, 2020-05
        {"event_id": 1, "sensor_family": "MODIS", "year": 2020, "month": 5, "h3_r7": cell_1, "h3_r6": r6, "h3_r5": r5, "district_id": "BGD-ADM2-alpha", "frp_sum": 10.0, "start_ts": "2020-05-02T10:00:00Z"},
        {"event_id": 2, "sensor_family": "MODIS", "year": 2020, "month": 5, "h3_r7": cell_1, "h3_r6": r6, "h3_r5": r5, "district_id": "BGD-ADM2-alpha", "frp_sum": 15.0, "start_ts": "2020-05-03T10:00:00Z"},
        {"event_id": 3, "sensor_family": "MODIS", "year": 2020, "month": 5, "h3_r7": cell_2, "h3_r6": r6, "h3_r5": r5, "district_id": "BGD-ADM2-alpha", "frp_sum": 20.0, "start_ts": "2020-05-05T10:00:00Z"},
        {"event_id": 4, "sensor_family": "MODIS", "year": 2020, "month": 5, "h3_r7": cell_3, "h3_r6": r6, "h3_r5": r5, "district_id": "BGD-ADM2-beta", "frp_sum": 30.0, "start_ts": "2020-05-10T10:00:00Z"},
        # MODIS, 2020-06
        {"event_id": 5, "sensor_family": "MODIS", "year": 2020, "month": 6, "h3_r7": cell_1, "h3_r6": r6, "h3_r5": r5, "district_id": "BGD-ADM2-alpha", "frp_sum": 12.0, "start_ts": "2020-06-02T10:00:00Z"},
        # VIIRS, 2020-05
        {"event_id": 6, "sensor_family": "VIIRS", "year": 2020, "month": 5, "h3_r7": cell_1, "h3_r6": r6, "h3_r5": r5, "district_id": "BGD-ADM2-alpha", "frp_sum": 5.0, "start_ts": "2020-05-02T10:00:00Z"},
        {"event_id": 7, "sensor_family": "VIIRS", "year": 2020, "month": 5, "h3_r7": cell_2, "h3_r6": r6, "h3_r5": r5, "district_id": "BGD-ADM2-alpha", "frp_sum": 7.0, "start_ts": "2020-05-06T10:00:00Z"},
        # VIIRS, 2020-06
        {"event_id": 8, "sensor_family": "VIIRS", "year": 2020, "month": 6, "h3_r7": cell_3, "h3_r6": r6, "h3_r5": r5, "district_id": "BGD-ADM2-beta", "frp_sum": 8.0, "start_ts": "2020-06-15T10:00:00Z"},
        {"event_id": 9, "sensor_family": "VIIRS", "year": 2020, "month": 6, "h3_r7": cell_3, "h3_r6": r6, "h3_r5": r5, "district_id": "BGD-ADM2-beta", "frp_sum": 9.0, "start_ts": "2020-06-16T10:00:00Z"},
        # Outside ROI (district_id None)
        {"event_id": 10, "sensor_family": "MODIS", "year": 2020, "month": 5, "h3_r7": cell_out, "h3_r6": r6, "h3_r5": r5, "district_id": None, "frp_sum": 50.0, "start_ts": "2020-05-20T10:00:00Z"},
    ]

    df = pd.DataFrame(events)
    df["start_ts"] = pd.to_datetime(df["start_ts"], utc=True)
    return df, districts


def test_ten_event_fixture_hand_calculated() -> None:
    """Validate aggregations, sparsity, zero-fills, and invariants against hand values."""
    events_df, districts = make_ten_event_fixture()

    coverage_ranges = {
        "MODIS": ((2020, 5), (2020, 6)),
        "VIIRS": ((2020, 5), (2020, 6)),
    }

    filtered = filter_events_by_coverage(events_df, coverage_ranges)
    # Event 10 (outside ROI) dropped -> exactly 9 events kept
    assert len(filtered) == 9

    # Monthly cell aggregation
    cell_df = aggregate_monthly_cell(filtered)
    # Exactly 7 distinct cell-month groups
    assert len(cell_df) == 7

    # Hand-calculated assertions on monthly_cell
    c1_m5_mod = cell_df[(cell_df["h3_r7"] == 609056049470636031) & (cell_df["sensor_family"] == "MODIS") & (cell_df["month"] == 5)]
    assert len(c1_m5_mod) == 1
    assert c1_m5_mod.iloc[0]["event_count"] == 2
    assert c1_m5_mod.iloc[0]["frp_sum"] == pytest.approx(25.0)

    c3_m6_vii = cell_df[(cell_df["h3_r7"] == 609056049940398079) & (cell_df["sensor_family"] == "VIIRS") & (cell_df["month"] == 6)]
    assert len(c3_m6_vii) == 1
    assert c3_m6_vii.iloc[0]["event_count"] == 2
    assert c3_m6_vii.iloc[0]["frp_sum"] == pytest.approx(17.0)

    # Sparsity: cell_2 in 2020-06 has 0 events and MUST be absent
    c2_m6 = cell_df[(cell_df["h3_r7"] == 609056049487413247) & (cell_df["month"] == 6)]
    assert len(c2_m6) == 0

    # Monthly region aggregation
    region_df = aggregate_monthly_region(filtered, districts, coverage_ranges)
    # Dense: 2 districts x 2 families x 2 months = 8 rows
    assert len(region_df) == 8

    # Zero-filled district-months present
    beta_m6_mod = region_df[(region_df["region_id"] == "BGD-ADM2-beta") & (region_df["sensor_family"] == "MODIS") & (region_df["month"] == 6)]
    assert len(beta_m6_mod) == 1
    assert beta_m6_mod.iloc[0]["event_count"] == 0
    assert beta_m6_mod.iloc[0]["frp_sum"] == pytest.approx(0.0)

    alpha_m5_mod = region_df[(region_df["region_id"] == "BGD-ADM2-alpha") & (region_df["sensor_family"] == "MODIS") & (region_df["month"] == 5)]
    assert len(alpha_m5_mod) == 1
    assert alpha_m5_mod.iloc[0]["event_count"] == 3  # events 1, 2, 3
    assert alpha_m5_mod.iloc[0]["frp_sum"] == pytest.approx(45.0)

    # Invariants verification
    verify_invariants(cell_df, region_df)


def test_coverage_and_month_boundaries() -> None:
    """Validate MODIS coverage start, VIIRS start inference, and last complete month."""
    # 1. MODIS starts at 2000-11
    dummy_df = pd.DataFrame({"sensor_family": ["MODIS"]})
    assert family_coverage_start(dummy_df, "MODIS") == (2000, 11)

    # 2. VIIRS mid-month start -> first complete is next month
    viirs_events = pd.DataFrame({
        "sensor_family": ["VIIRS", "VIIRS"],
        "start_ts": ["2012-01-20T05:00:00Z", "2012-02-01T05:00:00Z"],
    })
    assert family_coverage_start(viirs_events, "VIIRS") == (2012, 2)

    # 3. Dense month generator
    months = generate_dense_months((2012, 11), (2013, 2))
    assert months == [(2012, 11), (2012, 12), (2013, 1), (2013, 2)]

    # 4. Partial month cut-off (e.g. Nov 1st -> last complete is October)
    events_with_partial = pd.DataFrame({
        "year": [2026, 2026],
        "month": [10, 11],
        "start_ts": ["2026-10-31T23:00:00Z", "2026-11-01T12:00:00Z"],
    })
    assert determine_last_complete_month(events_with_partial) == (2026, 10)


def test_invariant_failures() -> None:
    """Verify that invariants detect corrupt or invalid aggregations."""
    # Negative count
    bad_cell = pd.DataFrame({
        "h3_r7": [1], "h3_r6": [1], "h3_r5": [1],
        "district_id": ["A"], "sensor_family": ["MODIS"],
        "year": [2020], "month": [5],
        "event_count": [-1], "frp_sum": [10.0],
    })
    bad_region = pd.DataFrame({
        "region_id": ["A"], "sensor_family": ["MODIS"],
        "year": [2020], "month": [5],
        "event_count": [0], "frp_sum": [0.0],
    })
    with pytest.raises(ValueError, match="negative event_count"):
        verify_invariants(bad_cell, bad_region)

    # Count mismatch between cell and region
    cell_ok = pd.DataFrame({
        "h3_r7": [1], "h3_r6": [1], "h3_r5": [1],
        "district_id": ["A"], "sensor_family": ["MODIS"],
        "year": [2020], "month": [5],
        "event_count": [5], "frp_sum": [10.0],
    })
    reg_mismatch = pd.DataFrame({
        "region_id": ["A"], "sensor_family": ["MODIS"],
        "year": [2020], "month": [5],
        "event_count": [3], "frp_sum": [10.0],
    })
    with pytest.raises(ValueError, match="event count mismatch"):
        verify_invariants(cell_ok, reg_mismatch)


def test_run_aggregation_stage(tmp_path: Path) -> None:
    """Test run_aggregation IO runner end-to-end with temporary directory."""
    events_df, districts = make_ten_event_fixture()
    # Save mock events.parquet
    events_pq = tmp_path / "events.parquet"
    events_df.to_parquet(events_pq, compression="ZSTD")

    # Save mock reference regions.parquet
    ref_dir = tmp_path / "reference"
    ref_dir.mkdir(parents=True, exist_ok=True)
    ref_pq = ref_dir / "regions.parquet"
    pd.DataFrame({"region_id": districts, "level": ["adm2", "adm2"]}).to_parquet(ref_pq)

    summary = run_aggregation(
        interim_dir=tmp_path,
        reference_dir=ref_dir,
        explicit_end_ym=(2020, 6),
        explicit_viirs_start_ym=(2020, 5),
        explicit_modis_start_ym=(2020, 5),
    )

    assert summary["monthly_cell_rows"] == 7
    assert summary["monthly_region_rows"] == 8

    # Verify Parquet files on disk
    cell_file = tmp_path / "monthly_cell.parquet"
    reg_file = tmp_path / "monthly_region.parquet"
    manifest_file = tmp_path / "aggregate_manifest.json"

    assert cell_file.exists()
    assert reg_file.exists()
    assert manifest_file.exists()

    cell_table = pq.read_table(cell_file)
    reg_table = pq.read_table(reg_file)

    assert cell_table.schema.names == MONTHLY_CELL_ARROW_SCHEMA.names
    assert reg_table.schema.names == MONTHLY_REGION_ARROW_SCHEMA.names

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    assert manifest_data["n_districts"] == 2


def test_real_data_aggregation_invariants() -> None:
    """Validate invariants on real data when interim/events.parquet exists."""
    from pyroscope_pipeline.common.paths import INTERIM_DIR

    events_pq = INTERIM_DIR / "events.parquet"
    if not events_pq.exists():
        pytest.skip("Real data events.parquet not available; running only in local data lane.")

    cell_pq = INTERIM_DIR / "monthly_cell.parquet"
    reg_pq = INTERIM_DIR / "monthly_region.parquet"

    if not cell_pq.exists() or not reg_pq.exists():
        run_aggregation()

    cell_df = pd.read_parquet(cell_pq)
    reg_df = pd.read_parquet(reg_pq)

    # 1. Non-empty
    assert len(cell_df) > 0
    assert len(reg_df) == 31296  # 489 coverage months * 64 districts

    # 2. Strict Invariants
    verify_invariants(cell_df, reg_df)

