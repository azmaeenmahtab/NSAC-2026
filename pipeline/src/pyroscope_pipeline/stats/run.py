"""Stage runner: Compute calendar statistics and assemble processed dataset (D07)."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pyroscope_pipeline.common.config import PipelineConfig, load_config
from pyroscope_pipeline.common.logging import get_logger
from pyroscope_pipeline.common.paths import (
    INTERIM_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    REFERENCE_DIR,
)
from pyroscope_pipeline.stats.anomalies import compute_anomalies
from pyroscope_pipeline.stats.assemble import (
    augment_harmonized_with_presets,
    build_dataset_manifest,
    compute_as_of_date,
    compute_parquet_dir_hash,
    load_region_constituents,
    update_current_pointer,
)
from pyroscope_pipeline.stats.climatology import compute_climatology
from pyroscope_pipeline.stats.seasons import compute_seasons
from pyroscope_pipeline.stats.yearly import compute_yearly

logger = get_logger("stats")

CLIMATOLOGY_ARROW_SCHEMA = pa.schema([
    ("region_id", pa.string()),
    ("month", pa.int8()),
    ("n_years", pa.int32()),
    ("mean", pa.float64()),
    ("p50", pa.float64()),
    ("p90", pa.float64()),
    ("p95", pa.float64()),
    ("baseline_year_min", pa.int16()),
    ("baseline_year_max", pa.int16()),
])

ANOMALIES_ARROW_SCHEMA = pa.schema([
    ("region_id", pa.string()),
    ("year", pa.int16()),
    ("month", pa.int8()),
    ("value", pa.float64()),
    ("percentile_rank", pa.float64()),
    ("class", pa.string()),
])

SEASONS_ARROW_SCHEMA = pa.schema([
    ("region_id", pa.string()),
    ("start_month", pa.int8()),
    ("peak_month", pa.int8()),
    ("end_month", pa.int8()),
    ("share_of_annual", pa.float64()),
    ("window_length", pa.int32()),
])

YEARLY_ARROW_SCHEMA = pa.schema([
    ("region_id", pa.string()),
    ("year", pa.int16()),
    ("harmonized_total", pa.float64()),
    ("frp_sum", pa.float64()),
    ("rank", pa.int32()),
    ("vs_mean_pct", pa.float64()),
    ("peak_month", pa.int8()),
])


def _write_table_zstd(df: pd.DataFrame, schema: pa.Schema, out_path: Path) -> None:
    table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
    pq.write_table(table, out_path, compression="ZSTD", version="2.6")


def _stage_supporting_files(interim_dir: Path, reference_dir: Path, staging_dir: Path) -> None:
    entries = [
        (interim_dir, "harmonized_region.parquet", True),
        (interim_dir, "harmonized_cell.parquet", True),
        (interim_dir, "monthly_region.parquet", True),
        (interim_dir, "monthly_cell.parquet", False),
        (interim_dir, "calibration_report.parquet", False),
        (interim_dir, "events.parquet", False),
        (interim_dir, "diagnostics.json", False),
        (reference_dir, "regions.parquet", True),
        (reference_dir, "region_cells.parquet", False),
    ]
    for src_dir, fname, required in entries:
        src_file = src_dir / fname
        if src_file.is_file():
            shutil.copy2(src_file, staging_dir / fname)
        elif required:
            raise FileNotFoundError(f"Required file missing for assembly: {src_file}")


def run_stats(
    interim_dir: Path | str | None = None,
    processed_dir: Path | str | None = None,
    reference_dir: Path | str | None = None,
    raw_dir: Path | str | None = None,
    config: PipelineConfig | None = None,
) -> dict[str, Any]:
    """Compute climatology, anomalies, seasons, yearly stats, and assemble processed dataset."""
    t0 = time.time()
    cfg = config or load_config()
    i_dir = Path(interim_dir) if interim_dir else INTERIM_DIR
    p_dir = Path(processed_dir) if processed_dir else PROCESSED_DIR
    ref_dir = Path(reference_dir) if reference_dir else REFERENCE_DIR
    r_dir = Path(raw_dir) if raw_dir else RAW_DIR

    harm_reg_path = i_dir / "harmonized_region.parquet"
    harm_cell_path = i_dir / "harmonized_cell.parquet"
    monthly_reg_path = i_dir / "monthly_region.parquet"
    for req_path in (harm_reg_path, harm_cell_path, monthly_reg_path):
        if not req_path.exists():
            raise FileNotFoundError(f"Required interim table missing: {req_path}")

    harm_reg_df = pd.read_parquet(harm_reg_path)
    monthly_reg_df = pd.read_parquet(monthly_reg_path)
    region_constituents, preset_constituents = load_region_constituents(ref_dir)
    augmented_harm_df = augment_harmonized_with_presets(harm_reg_df, preset_constituents)

    logger.info("Computing climatology, anomalies, seasons, and yearly stats...")
    climatology_df = compute_climatology(augmented_harm_df)
    anomalies_df = compute_anomalies(augmented_harm_df)
    seasons_df = compute_seasons(
        climatology_df,
        share_threshold=cfg.harmonization.season_share_threshold,
    )
    yearly_df = compute_yearly(
        augmented_harm_df,
        monthly_region_df=monthly_reg_df,
        region_constituents=region_constituents,
    )

    p_dir.mkdir(parents=True, exist_ok=True)
    staging_dir = p_dir / ".staging_d07"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    _write_table_zstd(climatology_df, CLIMATOLOGY_ARROW_SCHEMA, staging_dir / "climatology.parquet")
    _write_table_zstd(anomalies_df, ANOMALIES_ARROW_SCHEMA, staging_dir / "anomalies.parquet")
    _write_table_zstd(seasons_df, SEASONS_ARROW_SCHEMA, staging_dir / "seasons.parquet")
    _write_table_zstd(yearly_df, YEARLY_ARROW_SCHEMA, staging_dir / "yearly.parquet")
    _stage_supporting_files(i_dir, ref_dir, staging_dir)

    as_of_date = compute_as_of_date(harm_reg_df)
    short_hash = compute_parquet_dir_hash(staging_dir)
    data_version = f"v{as_of_date}-{short_hash}"

    manifest = build_dataset_manifest(
        raw_dir=r_dir,
        interim_dir=i_dir,
        as_of_date=as_of_date,
        data_version=data_version,
        cfg=cfg,
    )
    manifest.write_json(staging_dir / "manifest.json")

    version_dir = p_dir / data_version
    if version_dir.exists():
        shutil.rmtree(version_dir)
    staging_dir.rename(version_dir)

    current_path = update_current_pointer(p_dir, data_version)
    elapsed_s = round(time.time() - t0, 2)
    logger.info(
        f"Stats assembly complete in {elapsed_s}s: {data_version} "
        f"(climatology={len(climatology_df):,}, anomalies={len(anomalies_df):,}, "
        f"seasons={len(seasons_df):,}, yearly={len(yearly_df):,}) -> {current_path}"
    )

    return {
        "data_version": data_version,
        "as_of_date": as_of_date,
        "version_dir": str(version_dir),
        "current_path": str(current_path),
        "climatology_rows": len(climatology_df),
        "anomalies_rows": len(anomalies_df),
        "seasons_rows": len(seasons_df),
        "yearly_rows": len(yearly_df),
        "elapsed_seconds": elapsed_s,
    }


if __name__ == "__main__":
    summary = run_stats()
    print("Stats Assembly Summary:")
    print(json.dumps(summary, indent=2))
