"""Assembly helpers for presets, manifest metadata, and versioned directory pointer."""

from __future__ import annotations

import calendar
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from pyroscope_pipeline.common.config import PipelineConfig
from pyroscope_pipeline.common.manifest import DatasetManifest, PipelineCounts, SourceManifest
from pyroscope_pipeline.common.paths import REPO_ROOT
from pyroscope_pipeline.ingest.confidence import filter_modis, filter_viirs
from pyroscope_pipeline.ingest.readers import detect_sensor_family, read_firms_chunks
from pyroscope_pipeline.reference.catalog_specs import CHT_DISTRICTS


def load_region_constituents(
    reference_dir: Path,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Load composite-region -> district_id mappings from `regions.parquet`."""
    regions_pq = reference_dir / "regions.parquet"
    if not regions_pq.exists():
        return {}, {}

    df = pd.read_parquet(regions_pq)
    adm2_df = df[df["level"] == "adm2"]
    all_districts = sorted(adm2_df["region_id"].astype(str).tolist())

    constituents: dict[str, list[str]] = {}
    for div_id in sorted(df.loc[df["level"] == "adm1", "region_id"].astype(str).unique()):
        members = sorted(
            adm2_df.loc[adm2_df["parent_id"].astype(str) == div_id, "region_id"]
            .astype(str)
            .tolist()
        )
        if members:
            constituents[div_id] = members

    if all_districts:
        constituents["BGD"] = all_districts

    presets: dict[str, list[str]] = {}
    if "PRESET-CHT" in set(df["region_id"].astype(str)):
        cht_members = sorted(d for d in CHT_DISTRICTS if d in set(all_districts))
        if cht_members:
            constituents["PRESET-CHT"] = cht_members
            presets["PRESET-CHT"] = cht_members

    return constituents, presets


def augment_harmonized_with_presets(
    harmonized_df: pd.DataFrame,
    preset_constituents: dict[str, list[str]],
) -> pd.DataFrame:
    """Append synthetic preset rows (e.g. PRESET-CHT) by summing constituent districts."""
    if harmonized_df.empty or not preset_constituents:
        return harmonized_df

    existing = set(harmonized_df["region_id"].astype(str).unique())
    extra_frames: list[pd.DataFrame] = []

    for preset_id, members in sorted(preset_constituents.items()):
        if preset_id in existing or not members:
            continue
        sub = harmonized_df[harmonized_df["region_id"].isin(members)]
        if sub.empty:
            continue
        rows: list[dict[str, object]] = []
        for (y, m), grp in sub.groupby(["year", "month"], sort=True):
            first = grp.iloc[0]
            in_ov = bool(first["in_overlap"])
            src = str(first["source_used"])
            viirs_val = (
                float(grp["raw_viirs"].sum())
                if (in_ov or src == "viirs_calibrated")
                else np.nan
            )
            rows.append({
                "region_id": preset_id,
                "year": np.int16(y),
                "month": np.int8(m),
                "raw_modis": float(grp["raw_modis"].sum()),
                "raw_viirs": viirs_val,
                "harmonized": float(grp["harmonized"].sum()),
                "source_used": src,
                "method": "none",
                "calibration_unit_id": preset_id,
                "in_overlap": in_ov,
            })
        if rows:
            extra_frames.append(pd.DataFrame(rows))

    if not extra_frames:
        return harmonized_df
    return pd.concat([harmonized_df, *extra_frames], ignore_index=True).sort_values(
        ["region_id", "year", "month"], ignore_index=True
    )


def compute_as_of_date(harmonized_df: pd.DataFrame) -> str:
    """Compute the final YYYY-MM-DD calendar date covered by `harmonized_df`."""
    if harmonized_df.empty:
        raise ValueError("Cannot derive as_of_date from empty harmonized_region table")
    ym_series = harmonized_df["year"].astype(int) * 100 + harmonized_df["month"].astype(int)
    max_y, max_m = divmod(int(ym_series.max()), 100)
    last_day = calendar.monthrange(max_y, max_m)[1]
    return f"{max_y:04d}-{max_m:02d}-{last_day:02d}"


def compute_parquet_dir_hash(directory: Path) -> str:
    """Compute a deterministic 8-character content hash over all Parquet files in `directory`."""
    hasher = hashlib.sha256()
    for parquet_path in sorted(directory.glob("*.parquet")):
        hasher.update(parquet_path.name.encode("utf-8"))
        hasher.update(parquet_path.read_bytes())
    return hasher.hexdigest()[:8]


def get_git_commit() -> str:
    """Return short git HEAD commit SHA or `'unknown'` if unavailable."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or "unknown"
    except (subprocess.SubprocessError, OSError):
        return "unknown"


def flatten_parameters(cfg: PipelineConfig) -> dict[str, Any]:
    """Flatten public pipeline configuration parameters for manifest display."""
    return {
        "eps_spatial_meters": cfg.clustering.eps_spatial_meters,
        "eps_temporal_hours": cfg.clustering.eps_temporal_hours,
        "min_pts": cfg.clustering.min_pts,
        "min_mean_monthly_modis": cfg.harmonization.min_mean_monthly_modis,
        "month_pool_width": cfg.harmonization.month_pool_width,
        "cv_method": cfg.harmonization.cv_method,
        "methods": list(cfg.harmonization.methods),
        "percentiles": list(cfg.harmonization.percentiles),
        "season_share_threshold": cfg.harmonization.season_share_threshold,
        "h3_resolutions": list(cfg.spatial.h3_resolutions),
        "bbox_bangladesh": list(cfg.spatial.bbox_bangladesh),
        "modis_min_confidence": cfg.sources.modis.min_confidence,
        "viirs_allowed_confidence": list(cfg.sources.viirs.allowed_confidence),
    }


def _count_drops_from_raw(
    raw_dir: Path,
    cfg: PipelineConfig,
    detections_kept: int,
) -> tuple[int, int] | None:
    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        return None
    west, south, east, north = cfg.spatial.bbox_bangladesh
    raw_total = 0
    low_conf = 0
    non_veg = 0
    outside_bbox = 0
    for csv_file in csv_files:
        family = detect_sensor_family(csv_file)
        for chunk in read_firms_chunks(csv_file, chunksize=100_000):
            raw_total += len(chunk)
            if family == "MODIS":
                kept, drops = filter_modis(
                    chunk,
                    min_confidence=cfg.sources.modis.min_confidence,
                    require_type_zero=cfg.sources.modis.require_type_zero,
                )
            else:
                kept, drops = filter_viirs(
                    chunk,
                    allowed_confidence=tuple(cfg.sources.viirs.allowed_confidence),
                    require_type_zero=True,
                )
            low_conf += int(drops["low_confidence"])
            non_veg += int(drops["non_vegetation_type"])
            if not kept.empty:
                in_box = (
                    (kept["latitude"] >= south)
                    & (kept["latitude"] <= north)
                    & (kept["longitude"] >= west)
                    & (kept["longitude"] <= east)
                )
                outside_bbox += int((~in_box).sum())

    dup = max(0, raw_total - low_conf - non_veg - outside_bbox - detections_kept) if detections_kept > 0 else 0
    return low_conf, dup


def build_dataset_manifest(
    raw_dir: Path,
    interim_dir: Path,
    as_of_date: str,
    data_version: str,
    cfg: PipelineConfig,
) -> DatasetManifest:
    """Collect sources, counts, parameters, and unallocated total into a DatasetManifest."""
    sources: list[SourceManifest] = []
    detections_raw = 0
    raw_manifest = raw_dir / "MANIFEST.json"
    if raw_manifest.is_file():
        raw_meta = json.loads(raw_manifest.read_text(encoding="utf-8"))
        for entry in raw_meta.get("files", []):
            rows_n = int(entry.get("row_count", 0))
            detections_raw += rows_n
            sources.append(
                SourceManifest(
                    file_name=str(entry["file_name"]),
                    sensor=str(entry["sensor"]),
                    row_count=rows_n,
                    sha256=str(entry.get("sha256", "")),
                    date_range=[str(entry.get("date_min", "")), str(entry.get("date_max", ""))],
                )
            )

    detections_kept = 0
    events_created = 0
    noise_points = 0
    events_outside_roi = 0
    events_manifest = interim_dir / "events_manifest.json"
    if events_manifest.is_file():
        ev_meta = json.loads(events_manifest.read_text(encoding="utf-8"))
        detections_kept = int(ev_meta.get("total_pixels", 0))
        events_created = int(ev_meta.get("total_events", 0))
        for fam_stats in ev_meta.get("families", {}).values():
            noise_points += int(fam_stats.get("noise_points", 0))
            events_outside_roi += int(fam_stats.get("events_outside_roi", 0))

    dropped_conf = 0
    dropped_dup = 0
    ingest_manifest = interim_dir / "ingest_manifest.json"
    if ingest_manifest.is_file():
        ing_meta = json.loads(ingest_manifest.read_text(encoding="utf-8"))
        detections_raw = int(ing_meta.get("raw_rows_read", detections_raw))
        detections_kept = int(ing_meta.get("detections_kept", detections_kept))
        dropped_conf = int(ing_meta.get("low_confidence_dropped", 0))
        dropped_dup = int(ing_meta.get("duplicate_dropped", 0))
    else:
        raw_drops = _count_drops_from_raw(raw_dir, cfg, detections_kept)
        if raw_drops is not None:
            dropped_conf, dropped_dup = raw_drops

    unallocated = 0.0
    diag_path = interim_dir / "diagnostics.json"
    if diag_path.is_file():
        diag_raw = json.loads(diag_path.read_text(encoding="utf-8"))
        unallocated = float(diag_raw.get("unallocated_harmonized", 0.0))

    return DatasetManifest(
        data_version=data_version,
        git_commit=get_git_commit(),
        as_of_date=as_of_date,
        provisional_from=None,
        parameters=flatten_parameters(cfg),
        sources=sources,
        counts=PipelineCounts(
            detections_raw=detections_raw,
            detections_kept=detections_kept,
            detections_dropped_confidence=dropped_conf,
            detections_dropped_duplicate=dropped_dup,
            events_created=events_created,
            noise_points=noise_points,
            events_outside_roi=events_outside_roi,
        ),
        unallocated_harmonized=unallocated,
    )


def update_current_pointer(processed_dir: Path, version_name: str) -> Path:
    """Point `processed_dir/current` at `version_name` via symlink (copy fallback)."""
    current_path = processed_dir / "current"
    if current_path.is_symlink() or current_path.is_file():
        current_path.unlink()
    elif current_path.is_dir():
        shutil.rmtree(current_path)

    try:
        current_path.symlink_to(version_name, target_is_directory=True)
    except OSError:
        shutil.copytree(processed_dir / version_name, current_path)
    return current_path
