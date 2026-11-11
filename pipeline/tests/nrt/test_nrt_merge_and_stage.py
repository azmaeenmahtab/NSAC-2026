"""Unit and integration tests for D08 merge, boundary re-clustering, climatology, and MTD."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import h3
import httpx
import numpy as np
import pandas as pd

from pyroscope_pipeline.clustering.regions import load_district_cells_map
from pyroscope_pipeline.common.paths import FIXTURES_DIR, REPO_ROOT
from pyroscope_pipeline.harmonize.run import run_harmonization
from pyroscope_pipeline.nrt.merge import merge_nrt_tables, recluster_with_buffer
from pyroscope_pipeline.nrt.run import run_nrt
from pyroscope_pipeline.stats.climatology import compute_climatology
from pyroscope_pipeline.stats.run import run_stats


def _build_fixture_nrt_environment(tmp_path: Path) -> dict[str, Path]:
    """Assemble a complete D07 dataset (2000-11..2025-12) in `tmp_path` for NRT testing."""
    interim_dir = tmp_path / "interim"
    processed_dir = tmp_path / "processed"
    ref_dir = tmp_path / "reference"
    raw_dir = tmp_path / "raw"
    for d in (interim_dir, processed_dir, ref_dir, raw_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Copy synthetic fixture tables and calibration report from D06
    monthly_reg = pd.read_parquet(FIXTURES_DIR / "monthly_region.parquet")
    monthly_reg_dist = monthly_reg[monthly_reg["region_id"].str.startswith("BGD-ADM2-")].copy()
    monthly_reg_dist.to_parquet(interim_dir / "monthly_region.parquet", index=False)

    # Build sparse monthly_cell consistent with monthly_region_dist
    regions_df = pd.read_parquet(FIXTURES_DIR / "regions.parquet")
    regions_df["parent_id"] = regions_df["parent_id"].fillna("BGD")
    div_row = pd.DataFrame([
        {
            "region_id": "BGD-ADM1-central",
            "name": "Central",
            "level": "adm1",
            "parent_id": "BGD",
            "bbox": [89.0, 22.0, 92.0, 23.0],
            "aliases": ["Central"],
        }
    ])
    regions_df.loc[regions_df["level"] == "adm2", "parent_id"] = "BGD-ADM1-central"
    regions_df.loc[regions_df["level"] == "country", "parent_id"] = None
    pd.concat([regions_df, div_row], ignore_index=True).to_parquet(ref_dir / "regions.parquet", index=False)

    c_alpha = np.uint64(int(h3.latlng_to_cell(22.5, 89.5, 7), 16))
    c_beta = np.uint64(int(h3.latlng_to_cell(22.5, 91.5, 7), 16))
    pd.DataFrame([
        {"region_id": "BGD-ADM2-alpha", "h3_r7": c_alpha},
        {"region_id": "BGD-ADM2-beta", "h3_r7": c_beta},
    ]).to_parquet(ref_dir / "region_cells.parquet", index=False)

    cell_rows = []
    for _, r in monthly_reg_dist.iterrows():
        rid = str(r["region_id"])
        r7 = c_alpha if rid == "BGD-ADM2-alpha" else c_beta
        r7_hex = format(int(r7), "x")
        cell_rows.append({
            "h3_r7": r7,
            "h3_r6": np.uint64(int(h3.cell_to_parent(r7_hex, 6), 16)),
            "h3_r5": np.uint64(int(h3.cell_to_parent(r7_hex, 5), 16)),
            "district_id": rid,
            "sensor_family": str(r["sensor_family"]),
            "year": np.int16(r["year"]),
            "month": np.int8(r["month"]),
            "event_count": np.int32(r["event_count"]),
            "frp_sum": float(r["frp_sum"]),
        })
    pd.DataFrame(cell_rows).to_parquet(interim_dir / "monthly_cell.parquet", index=False)

    # Existing detections: place 1 pixel on 2025-12-31 22:00 UTC in alpha (isolated alone)
    existing_det = pd.DataFrame([
        {
            "detection_id": np.int64(1),
            "sensor": "VIIRS_SNPP",
            "sensor_family": "VIIRS",
            "lat": 22.5,
            "lon": 89.5,
            "acq_ts": pd.Timestamp("2025-12-31 22:00:00", tz="UTC"),
            "daynight": "N",
            "confidence_raw": "n",
            "confidence_class": "nominal",
            "frp_mw": 5.0,
            "scan": 0.4,
            "track": 0.4,
            "version": "2.0",
            "source_file": "archive.csv",
        }
    ])
    existing_det.to_parquet(interim_dir / "detections.parquet", index=False)

    # Empty events placeholder for initial state
    pd.DataFrame(columns=[
        "event_id", "sensor_family", "n_pixels", "start_ts", "end_ts",
        "lat", "lon", "frp_sum", "frp_max", "h3_r5", "h3_r6", "h3_r7",
        "year", "month", "district_id",
    ]).to_parquet(interim_dir / "events.parquet", index=False)

    run_harmonization(
        interim_dir=interim_dir,
        reference_dir=ref_dir,
        overlap_start=(2012, 2),
        overlap_end=(2025, 12),
    )
    run_stats(
        interim_dir=interim_dir,
        processed_dir=processed_dir,
        reference_dir=ref_dir,
        raw_dir=raw_dir,
    )
    return {
        "interim": interim_dir,
        "processed": processed_dir,
        "ref": ref_dir,
        "raw": raw_dir,
    }


def test_boundary_spanning_event_reclustered_and_only_affected_months_change(tmp_path: Path) -> None:
    """Appending a day merges a 2-day boundary event and changes only affected months."""
    dirs = _build_fixture_nrt_environment(tmp_path)
    cur = dirs["processed"] / "current"
    cell_map = load_district_cells_map(dirs["ref"] / "region_cells.parquet")

    existing_det = pd.read_parquet(dirs["interim"] / "detections.parquet")
    existing_ev = pd.read_parquet(cur / "events.parquet")
    assert len(existing_ev) == 0  # isolated single pixel on 2025-12-31 was noise

    # New pixel arrives on 2026-01-01 06:00 UTC within 200m & 8h of 2025-12-31 22:00 UTC
    new_det = pd.DataFrame([
        {
            "detection_id": np.int64(1),
            "sensor": "VIIRS_NOAA20",
            "sensor_family": "VIIRS",
            "lat": 22.501,
            "lon": 89.501,
            "acq_ts": pd.Timestamp("2026-01-01 06:00:00", tz="UTC"),
            "daynight": "D",
            "confidence_raw": "h",
            "confidence_class": "high",
            "frp_mw": 7.0,
            "scan": 0.4,
            "track": 0.4,
            "version": "2.0NRT",
            "source_file": "firms_nrt_api",
        }
    ])

    _, updated_ev, affected = recluster_with_buffer(
        existing_detections=existing_det,
        new_detections=new_det,
        existing_events=existing_ev,
        cell_map=cell_map,
        buffer_days=3,
    )
    # The boundary-spanning pixels formed 1 merged event starting in 2025-12!
    assert len(updated_ev) == 1
    assert int(updated_ev.iloc[0]["n_pixels"]) == 2
    assert int(updated_ev.iloc[0]["year"]) == 2025
    assert int(updated_ev.iloc[0]["month"]) == 12
    assert (2025, 12) in affected
    assert (2026, 1) in affected

    # Non-boundary event on 2026-01-10 + 2026-01-10 changes ONLY (2026, 1)
    two_jan_det = pd.DataFrame([
        {
            "detection_id": np.int64(1),
            "sensor": "VIIRS_NOAA20",
            "sensor_family": "VIIRS",
            "lat": 22.5,
            "lon": 89.5,
            "acq_ts": pd.Timestamp("2026-01-10 06:00:00", tz="UTC"),
            "daynight": "D",
            "confidence_raw": "h",
            "confidence_class": "high",
            "frp_mw": 7.0,
            "scan": 0.4,
            "track": 0.4,
            "version": "2.0NRT",
            "source_file": "firms_nrt_api",
        },
        {
            "detection_id": np.int64(2),
            "sensor": "VIIRS_NOAA20",
            "sensor_family": "VIIRS",
            "lat": 22.501,
            "lon": 89.501,
            "acq_ts": pd.Timestamp("2026-01-10 08:00:00", tz="UTC"),
            "daynight": "D",
            "confidence_raw": "h",
            "confidence_class": "high",
            "frp_mw": 8.0,
            "scan": 0.4,
            "track": 0.4,
            "version": "2.0NRT",
            "source_file": "firms_nrt_api",
        },
    ])

    orig_hr = pd.read_parquet(cur / "harmonized_region.parquet")
    merged = merge_nrt_tables(
        existing_detections=existing_det,
        new_detections=two_jan_det,
        existing_events=existing_ev,
        monthly_cell=pd.read_parquet(cur / "monthly_cell.parquet"),
        monthly_region=pd.read_parquet(cur / "monthly_region.parquet"),
        harmonized_region=orig_hr,
        harmonized_cell=pd.read_parquet(cur / "harmonized_cell.parquet"),
        calibration_report=pd.read_parquet(cur / "calibration_report.parquet"),
        anomalies=pd.read_parquet(cur / "anomalies.parquet"),
        district_ids=["BGD-ADM2-alpha", "BGD-ADM2-beta"],
        district_to_division={"BGD-ADM2-alpha": "BGD-ADM1-central", "BGD-ADM2-beta": "BGD-ADM1-central"},
        divisions=["BGD-ADM1-central"],
        preset_constituents={},
        provisional_from_date=date(2026, 1, 1),
        new_as_of_date=date(2026, 1, 10),
        cell_map=cell_map,
    )
    assert merged.affected_months == ((2026, 1),)
    # Historical rows (<= 2025-12) in harmonized_region are identical and provisional=False
    hist_orig = orig_hr.sort_values(["region_id", "year", "month"]).reset_index(drop=True)
    hist_new = merged.harmonized_region[merged.harmonized_region["year"] <= 2025].drop(
        columns=["provisional"]
    ).sort_values(["region_id", "year", "month"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(hist_orig, hist_new)

    # Provisional rows (>= 2026-01) have provisional=True and are excluded from climatology
    jan26 = merged.harmonized_region[merged.harmonized_region["year"] == 2026]
    assert jan26["provisional"].all()
    clim_after = compute_climatology(merged.harmonized_region)
    clim_before = pd.read_parquet(cur / "climatology.parquet")
    clim_before = clim_before[clim_before["region_id"].isin(clim_after["region_id"])].reset_index(drop=True)
    pd.testing.assert_frame_equal(clim_after, clim_before, check_dtype=False)

    # Partial month MTD scaling approximation documented
    assert merged.mtd_scale_note is not None
    assert "10/31" in merged.mtd_scale_note


def test_run_nrt_end_to_end_updates_current_and_api_reads_provisional(tmp_path: Path) -> None:
    """Full run_nrt with mocked FIRMS API publishes new version and API exposes provisional flags."""
    dirs = _build_fixture_nrt_environment(tmp_path)
    api_root = str(REPO_ROOT / "services" / "api")
    if api_root not in sys.path:
        sys.path.insert(0, api_root)

    from app.core.config import Settings  # type: ignore[import-untyped]
    from app.features.calendar.service import clear_calendar_cache  # type: ignore[import-untyped]
    from app.features.series.service import clear_series_cache  # type: ignore[import-untyped]
    from app.main import create_app  # type: ignore[import-untyped]
    from fastapi.testclient import TestClient

    noaa20_csv = (
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
        "22.5,89.5,330.0,0.4,0.4,2026-01-02,0700,N20,VIIRS,h,2.0NRT,290.0,10.0,D\n"
        "22.501,89.501,332.0,0.4,0.4,2026-01-02,0705,N20,VIIRS,h,2.0NRT,291.0,12.0,D\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "VIIRS_NOAA20_NRT" in url:
            return httpx.Response(200, text=noaa20_csv)
        return httpx.Response(200, text="")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res = run_nrt(
        processed_dir=dirs["processed"],
        interim_dir=dirs["interim"],
        reference_dir=dirs["ref"],
        map_key="FAKE_KEY_FOR_TEST",
        today_utc="2026-01-05",
        client=client,
    )
    assert res["status"] == "updated"
    assert res["as_of_date"] == "2026-01-04"
    assert res["provisional_from"] == "2026-01-01"
    assert res["viirs_source_used"] == "VIIRS_NOAA20_NRT"
    assert "provisional, unadjusted NOAA-20" in str(res["provisional_note"])
    assert "4/31" in str(res["provisional_note"])

    # Verify manifest and API endpoints read provisional flags
    manifest = json.loads((dirs["processed"] / "current" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["provisional_from"] == "2026-01-01"
    assert "provisional, unadjusted NOAA-20" in manifest["provisional_note"]

    clear_calendar_cache()
    clear_series_cache()
    cfg = Settings(
        data_dir=str(dirs["processed"] / "current"),
        reference_dir=str(dirs["ref"]),
        web_origin="http://localhost:3000",
        rate_limit_default="120/minute",
    )
    api_client = TestClient(create_app(cfg))
    meta = api_client.get("/api/meta").json()["data"]
    assert meta["provisionalFrom"] == "2026-01-01"

    cal = api_client.get("/api/calendar", params={"area_id": "BGD-ADM2-alpha"}).json()["data"]
    jan26_cell = next(c for c in cal["grid"] if c["year"] == 2026 and c["month"] == 1)
    dec25_cell = next(c for c in cal["grid"] if c["year"] == 2025 and c["month"] == 12)
    assert jan26_cell["provisional"] is True
    assert dec25_cell["provisional"] is False

    series = api_client.get("/api/series", params={"area_id": "BGD-ADM2-alpha"}).json()["data"]
    assert series[-1]["year"] == 2026 and series[-1]["provisional"] is True
    assert series[-2]["year"] == 2025 and series[-2]["provisional"] is False
