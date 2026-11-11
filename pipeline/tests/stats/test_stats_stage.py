"""Stage runner and API integration tests for D07 processed dataset assembly."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from pyroscope_pipeline.common.config import load_config
from pyroscope_pipeline.common.manifest import DatasetManifest
from pyroscope_pipeline.common.paths import FIXTURES_DIR, REFERENCE_DIR, REPO_ROOT
from pyroscope_pipeline.stats.run import (
    ANOMALIES_ARROW_SCHEMA,
    CLIMATOLOGY_ARROW_SCHEMA,
    SEASONS_ARROW_SCHEMA,
    YEARLY_ARROW_SCHEMA,
    run_stats,
)


def _prepare_interim_from_fixtures(interim_dir: Path, ref_dir: Path) -> None:
    """Stage an interim directory with PRESET-CHT-compatible regions and harmonized tables."""
    interim_dir.mkdir(parents=True, exist_ok=True)
    ref_dir.mkdir(parents=True, exist_ok=True)

    # Copy synthetic harmonized tables from fixtures
    harm_reg = pd.read_parquet(FIXTURES_DIR / "harmonized_region.parquet")
    harm_cell = pd.read_parquet(FIXTURES_DIR / "harmonized_cell.parquet")
    monthly_reg = pd.read_parquet(FIXTURES_DIR / "monthly_region.parquet")
    regions_df = pd.read_parquet(FIXTURES_DIR / "regions.parquet")

    # Add a synthetic PRESET-CHT row referencing alpha + beta so preset augmentation is exercised
    preset_row = pd.DataFrame([
        {
            "region_id": "PRESET-CHT",
            "name": "Chittagong Hill Tracts",
            "level": "preset",
            "parent_id": "BGD",
            "bbox": [89.0, 22.0, 92.0, 23.0],
            "aliases": ["CHT", "Chittagong Hill Tracts"],
        }
    ])
    pd.concat([regions_df, preset_row], ignore_index=True).to_parquet(
        ref_dir / "regions.parquet", index=False
    )

    # Remap alpha/beta to CHT district ids so preset augmentation matches catalog_specs.CHT_DISTRICTS
    remap = {
        "BGD-ADM2-alpha": "BGD-ADM2-rangamati",
        "BGD-ADM2-beta": "BGD-ADM2-bandarban",
    }
    regions_full = pd.read_parquet(ref_dir / "regions.parquet")
    regions_full["region_id"] = regions_full["region_id"].replace(remap)
    regions_full.to_parquet(ref_dir / "regions.parquet", index=False)

    harm_reg["region_id"] = harm_reg["region_id"].replace(remap)
    harm_reg.to_parquet(interim_dir / "harmonized_region.parquet", index=False)

    harm_cell["district_id"] = harm_cell["district_id"].replace(remap)
    harm_cell.to_parquet(interim_dir / "harmonized_cell.parquet", index=False)

    monthly_reg["region_id"] = monthly_reg["region_id"].replace(remap)
    monthly_reg.to_parquet(interim_dir / "monthly_region.parquet", index=False)

    (interim_dir / "diagnostics.json").write_text(
        json.dumps({"unallocated_harmonized": 0.0}), encoding="utf-8"
    )
    (interim_dir / "events_manifest.json").write_text(
        json.dumps(
            {
                "total_pixels": 500,
                "total_events": 100,
                "families": {
                    "MODIS": {"noise_points": 5, "events_outside_roi": 1},
                    "VIIRS": {"noise_points": 7, "events_outside_roi": 2},
                },
            }
        ),
        encoding="utf-8",
    )


def test_run_stats_assembly_determinism_and_schemas(tmp_path: Path) -> None:
    """Verify run_stats creates deterministic versioned dir, manifest.json, and current pointer."""
    interim_dir = tmp_path / "interim"
    processed_dir = tmp_path / "processed"
    ref_dir = tmp_path / "reference"
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    _prepare_interim_from_fixtures(interim_dir, ref_dir)

    cfg = load_config()
    summary1 = run_stats(
        interim_dir=interim_dir,
        processed_dir=processed_dir,
        reference_dir=ref_dir,
        raw_dir=raw_dir,
        config=cfg,
    )

    version_dir = Path(summary1["version_dir"])
    current_path = Path(summary1["current_path"])
    assert version_dir.is_dir()
    assert current_path.resolve() == version_dir.resolve()
    assert summary1["data_version"].startswith("v2025-12-31-")
    assert len(summary1["data_version"].split("-")[-1]) == 8

    # Check Arrow schemas
    assert pq.read_schema(version_dir / "climatology.parquet").names == CLIMATOLOGY_ARROW_SCHEMA.names
    assert pq.read_schema(version_dir / "anomalies.parquet").names == ANOMALIES_ARROW_SCHEMA.names
    assert pq.read_schema(version_dir / "seasons.parquet").names == SEASONS_ARROW_SCHEMA.names
    assert pq.read_schema(version_dir / "yearly.parquet").names == YEARLY_ARROW_SCHEMA.names

    # Verify PRESET-CHT is present in all four stats tables
    for fname in ("climatology.parquet", "anomalies.parquet", "seasons.parquet", "yearly.parquet"):
        df = pd.read_parquet(version_dir / fname)
        assert "PRESET-CHT" in set(df["region_id"])

    # Verify manifest.json
    manifest = DatasetManifest.read_json(version_dir / "manifest.json")
    assert manifest.data_version == summary1["data_version"]
    assert manifest.as_of_date == "2025-12-31"
    assert manifest.provisional_from is None
    assert manifest.counts.events_created == 100
    assert manifest.counts.noise_points == 12
    assert manifest.counts.events_outside_roi == 3
    assert "eps_spatial_meters" in manifest.parameters

    # Hash output Parquet files before second run
    hashes1 = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(version_dir.glob("*.parquet"))
    }

    summary2 = run_stats(
        interim_dir=interim_dir,
        processed_dir=processed_dir,
        reference_dir=ref_dir,
        raw_dir=raw_dir,
        config=cfg,
    )
    assert summary2["data_version"] == summary1["data_version"]
    hashes2 = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(Path(summary2["version_dir"]).glob("*.parquet"))
    }
    assert hashes1 == hashes2


def test_assembled_dataset_loads_with_a01_api_loader(tmp_path: Path) -> None:
    """Verify the assembled `current` directory loads cleanly in the FastAPI A01 loader and endpoints."""
    api_root = str(REPO_ROOT / "services" / "api")
    if api_root not in sys.path:
        sys.path.insert(0, api_root)

    from app.core.config import Settings  # type: ignore[import-untyped]
    from app.core.dataset import load_dataset  # type: ignore[import-untyped]
    from app.features.calendar.service import clear_calendar_cache  # type: ignore[import-untyped]
    from app.features.methodology.service import clear_methodology_cache  # type: ignore[import-untyped]
    from app.features.stats.service import clear_stats_cache  # type: ignore[import-untyped]
    from app.main import create_app  # type: ignore[import-untyped]
    from fastapi.testclient import TestClient

    interim_dir = tmp_path / "interim"
    processed_dir = tmp_path / "processed"
    ref_dir = tmp_path / "reference"
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    _prepare_interim_from_fixtures(interim_dir, ref_dir)

    summary = run_stats(
        interim_dir=interim_dir,
        processed_dir=processed_dir,
        reference_dir=ref_dir,
        raw_dir=raw_dir,
    )

    loaded = load_dataset(summary["current_path"], reference_dir=REFERENCE_DIR)
    try:
        assert loaded.data_version == summary["data_version"]
        assert loaded.as_of == "2025-12-31"
        for view in ("climatology", "anomalies", "seasons", "yearly", "harmonized_region"):
            assert view in loaded.registered_views
    finally:
        loaded.connection.close()

    clear_calendar_cache()
    clear_stats_cache()
    clear_methodology_cache()
    cfg = Settings(
        data_dir=str(summary["current_path"]),
        reference_dir=str(ref_dir),
        web_origin="http://localhost:3000",
        rate_limit_default="120/minute",
    )
    client = TestClient(create_app(cfg))

    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["dataVersion"] == summary["data_version"]

    res_cal = client.get("/api/calendar", params={"area_id": "PRESET-CHT"})
    assert res_cal.status_code == 200
    cal_data = res_cal.json()["data"]
    assert cal_data["season"]["start_month"] == 4
    assert cal_data["season"]["peak_month"] == 5
    assert cal_data["season"]["end_month"] == 6
    assert np.isclose(cal_data["season"]["share_of_annual"], 244.0 / 344.0, atol=1e-3)

    res_yearly = client.get("/api/stats/yearly", params={"area_id": "PRESET-CHT"})
    assert res_yearly.status_code == 200
    assert len(res_yearly.json()["data"]) == 25

    res_anom = client.get(
        "/api/anomalies",
        params={"area_id": "PRESET-CHT", "year": 2020, "class": "extreme"},
    )
    assert res_anom.status_code == 200
    assert len(res_anom.json()["data"]) == 1
    assert res_anom.json()["data"][0]["month"] == 5
