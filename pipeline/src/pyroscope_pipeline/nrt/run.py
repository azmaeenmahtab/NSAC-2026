"""Stage runner: Incremental NRT update, provisional assembly, and current pointer update (D08)."""

from __future__ import annotations

import json
import os
import shutil
import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pyroscope_pipeline.aggregate.run import MONTHLY_CELL_ARROW_SCHEMA, MONTHLY_REGION_ARROW_SCHEMA
from pyroscope_pipeline.clustering.regions import load_district_cells_map
from pyroscope_pipeline.clustering.run import EVENTS_ARROW_SCHEMA
from pyroscope_pipeline.common.config import PipelineConfig, load_config
from pyroscope_pipeline.common.logging import get_logger
from pyroscope_pipeline.common.manifest import DatasetManifest, SourceManifest
from pyroscope_pipeline.common.paths import INTERIM_DIR, PIPELINE_ROOT, PROCESSED_DIR, REFERENCE_DIR
from pyroscope_pipeline.harmonize.run import (
    HARMONIZED_CELL_ARROW_SCHEMA,
    load_hierarchy,
)
from pyroscope_pipeline.nrt.cross_sensor import unadjusted_provisional_label
from pyroscope_pipeline.nrt.fetch import fetch_nrt_detections
from pyroscope_pipeline.nrt.merge import merge_nrt_tables
from pyroscope_pipeline.nrt.plan import parse_iso_date, plan_fetch_windows, plan_missing_days
from pyroscope_pipeline.nrt.recluster import normalize_nrt_raw
from pyroscope_pipeline.stats.assemble import (
    compute_parquet_dir_hash,
    get_git_commit,
    load_region_constituents,
    update_current_pointer,
)

logger = get_logger("nrt")

HARMONIZED_REGION_NRT_SCHEMA = pa.schema([
    ("region_id", pa.string()),
    ("year", pa.int16()),
    ("month", pa.int8()),
    ("raw_modis", pa.float64()),
    ("raw_viirs", pa.float64()),
    ("harmonized", pa.float64()),
    ("source_used", pa.string()),
    ("method", pa.string()),
    ("calibration_unit_id", pa.string()),
    ("in_overlap", pa.bool_()),
    ("provisional", pa.bool_()),
])

ANOMALIES_NRT_SCHEMA = pa.schema([
    ("region_id", pa.string()),
    ("year", pa.int16()),
    ("month", pa.int8()),
    ("value", pa.float64()),
    ("percentile_rank", pa.float64()),
    ("class", pa.string()),
    ("provisional", pa.bool_()),
])


def _resolve_map_key(explicit_key: str | None) -> str:
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()
    env_key = os.environ.get("FIRMS_MAP_KEY", "").strip()
    if env_key:
        return env_key
    env_file = PIPELINE_ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("FIRMS_MAP_KEY="):
                val = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                if val and val != "your_firms_map_key_here":
                    return val
    raise ValueError("FIRMS_MAP_KEY not configured in environment or pipeline/.env")


def _write_zstd(df: pd.DataFrame, schema: pa.Schema, out_path: Path) -> None:
    table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
    pq.write_table(table, out_path, compression="ZSTD", version="2.6")


def run_nrt(
    processed_dir: Path | str | None = None,
    interim_dir: Path | str | None = None,
    reference_dir: Path | str | None = None,
    config: PipelineConfig | None = None,
    map_key: str | None = None,
    today_utc: str | date | None = None,
    max_lookback_days: int = 30,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Fetch missing NRT FIRMS detections, merge with 3-day buffer, and publish versioned dataset."""
    t0 = time.time()
    cfg = config or load_config()
    p_dir = Path(processed_dir) if processed_dir else PROCESSED_DIR
    i_dir = Path(interim_dir) if interim_dir else INTERIM_DIR
    ref_dir = Path(reference_dir) if reference_dir else REFERENCE_DIR

    current_dir = (p_dir / "current").resolve()
    manifest_path = current_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Active dataset manifest not found at {manifest_path}")

    manifest = DatasetManifest.read_json(manifest_path)
    today_val = parse_iso_date(today_utc) if today_utc is not None else datetime.now(UTC).date()
    missing_days = plan_missing_days(
        as_of_date=manifest.as_of_date,
        today_utc=today_val,
        max_lookback_days=max_lookback_days,
    )
    windows = plan_fetch_windows(
        as_of_date=manifest.as_of_date,
        today_utc=today_val,
        max_days_per_call=5,
        max_lookback_days=max_lookback_days,
    )
    if not windows:
        logger.info(f"Dataset {manifest.data_version} already up to date (as_of={manifest.as_of_date}).")
        return {"status": "up_to_date", "data_version": manifest.data_version, "as_of_date": manifest.as_of_date}

    resolved_key = _resolve_map_key(map_key)
    logger.info(f"Fetching NRT detections across {len(windows)} windows ({missing_days[0]}..{missing_days[-1]})...")
    fetch_res = fetch_nrt_detections(
        windows=windows,
        bbox=cfg.spatial.bbox_bangladesh,
        map_key=resolved_key,
        client=client,
    )
    new_det, ingest_stats = normalize_nrt_raw(
        fetch_res.modis_raw,
        fetch_res.viirs_raw,
        bbox=cfg.spatial.bbox_bangladesh,
        min_modis_conf=cfg.sources.modis.min_confidence,
        require_type_zero=cfg.sources.modis.require_type_zero,
        allowed_viirs_conf=tuple(cfg.sources.viirs.allowed_confidence),
    )

    det_path = i_dir / "detections.parquet"
    existing_det = pd.read_parquet(det_path) if det_path.is_file() else pd.DataFrame()
    ev_path = current_dir / "events.parquet"
    if not ev_path.is_file():
        ev_path = i_dir / "events.parquet"
    existing_ev = pd.read_parquet(ev_path)

    districts, divisions, dist_to_div = load_hierarchy(ref_dir)
    _, preset_constituents = load_region_constituents(ref_dir)
    cells_pq = ref_dir / "region_cells.parquet"
    cell_map = load_district_cells_map(cells_pq) if cells_pq.is_file() else None

    provisional_from = parse_iso_date(manifest.provisional_from) if manifest.provisional_from else missing_days[0]
    new_as_of = missing_days[-1]
    planned_months = {(d.year, d.month) for d in missing_days}

    merged = merge_nrt_tables(
        existing_detections=existing_det,
        new_detections=new_det,
        existing_events=existing_ev,
        monthly_cell=pd.read_parquet(current_dir / "monthly_cell.parquet"),
        monthly_region=pd.read_parquet(current_dir / "monthly_region.parquet"),
        harmonized_region=pd.read_parquet(current_dir / "harmonized_region.parquet"),
        harmonized_cell=pd.read_parquet(current_dir / "harmonized_cell.parquet"),
        calibration_report=pd.read_parquet(current_dir / "calibration_report.parquet"),
        anomalies=pd.read_parquet(current_dir / "anomalies.parquet"),
        district_ids=districts,
        district_to_division=dist_to_div,
        divisions=divisions,
        preset_constituents=preset_constituents,
        provisional_from_date=provisional_from,
        new_as_of_date=new_as_of,
        cell_map=cell_map,
        planned_months=planned_months,
        eps_s_m=cfg.clustering.eps_spatial_meters,
        eps_t_hours=cfg.clustering.eps_temporal_hours,
        min_pts=cfg.clustering.min_pts,
    )

    staging_dir = p_dir / ".staging_d08"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    for static_name in ("climatology.parquet", "seasons.parquet", "yearly.parquet", "calibration_report.parquet", "regions.parquet", "region_cells.parquet", "diagnostics.json"):
        src_p = current_dir / static_name
        if src_p.is_file():
            shutil.copy2(src_p, staging_dir / static_name)

    _write_zstd(merged.events, EVENTS_ARROW_SCHEMA, staging_dir / "events.parquet")
    _write_zstd(merged.monthly_cell, MONTHLY_CELL_ARROW_SCHEMA, staging_dir / "monthly_cell.parquet")
    _write_zstd(merged.monthly_region, MONTHLY_REGION_ARROW_SCHEMA, staging_dir / "monthly_region.parquet")
    _write_zstd(merged.harmonized_region, HARMONIZED_REGION_NRT_SCHEMA, staging_dir / "harmonized_region.parquet")
    _write_zstd(merged.harmonized_cell, HARMONIZED_CELL_ARROW_SCHEMA, staging_dir / "harmonized_cell.parquet")
    _write_zstd(merged.anomalies, ANOMALIES_NRT_SCHEMA, staging_dir / "anomalies.parquet")

    data_version = f"v{new_as_of.isoformat()}-{compute_parquet_dir_hash(staging_dir)}"
    sensor_note = unadjusted_provisional_label(fetch_res.viirs_source_used)
    note_parts = [p for p in (sensor_note, merged.mtd_scale_note) if p]

    new_sources = list(manifest.sources)
    new_sources.append(
        SourceManifest(
            file_name=f"firms_nrt_{missing_days[0]}_{new_as_of}",
            sensor=f"MODIS_NRT+{fetch_res.viirs_source_used}",
            row_count=ingest_stats["raw_rows"],
            sha256="live-firms-nrt-api",
            date_range=[missing_days[0].isoformat(), new_as_of.isoformat()],
        )
    )
    updated_manifest = DatasetManifest(
        data_version=data_version,
        git_commit=get_git_commit(),
        as_of_date=new_as_of.isoformat(),
        provisional_from=provisional_from.isoformat(),
        provisional_note="; ".join(note_parts) if note_parts else None,
        parameters=manifest.parameters,
        sources=new_sources,
        counts=manifest.counts.model_copy(
            update={
                "detections_raw": manifest.counts.detections_raw + ingest_stats["raw_rows"],
                "detections_kept": manifest.counts.detections_kept + ingest_stats["kept"],
                "detections_dropped_confidence": manifest.counts.detections_dropped_confidence + ingest_stats["low_confidence"],
                "events_created": len(merged.events),
            }
        ),
        unallocated_harmonized=round(manifest.unallocated_harmonized + merged.unallocated_harmonized, 4),
    )
    updated_manifest.write_json(staging_dir / "manifest.json")

    version_dir = p_dir / data_version
    if version_dir.exists():
        shutil.rmtree(version_dir)
    staging_dir.rename(version_dir)
    current_path = update_current_pointer(p_dir, data_version)

    if i_dir.exists():
        _write_zstd(merged.events, EVENTS_ARROW_SCHEMA, i_dir / "events.parquet")
        if not merged.detections.empty:
            merged.detections.to_parquet(det_path, compression="ZSTD", index=False)

    elapsed_s = round(time.time() - t0, 2)
    return {
        "status": "updated",
        "data_version": data_version,
        "as_of_date": new_as_of.isoformat(),
        "provisional_from": provisional_from.isoformat(),
        "provisional_note": updated_manifest.provisional_note,
        "viirs_source_used": fetch_res.viirs_source_used,
        "nrt_raw_rows": ingest_stats["raw_rows"],
        "nrt_kept_rows": ingest_stats["kept"],
        "affected_months": [f"{y:04d}-{m:02d}" for y, m in merged.affected_months],
        "current_path": str(current_path),
        "elapsed_seconds": elapsed_s,
    }


if __name__ == "__main__":
    print(json.dumps(run_nrt(), indent=2))
