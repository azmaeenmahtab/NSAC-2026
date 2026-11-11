"""Stage runner: Run harmonization, downscale to cells, write validation report."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pyroscope_pipeline.common.config import PipelineConfig, load_config
from pyroscope_pipeline.common.logging import get_logger
from pyroscope_pipeline.common.paths import INTERIM_DIR, REFERENCE_DIR
from pyroscope_pipeline.harmonize.build import build_harmonization

logger = get_logger("harmonize")

HARMONIZED_REGION_ARROW_SCHEMA = pa.schema([
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
])

CALIBRATION_REPORT_ARROW_SCHEMA = pa.schema([
    ("calibration_unit_id", pa.string()),
    ("method_chosen", pa.string()),
    ("cv_rmse_qm", pa.float64()),
    ("cv_rmse_ratio", pa.float64()),
    ("cv_mae_qm", pa.float64()),
    ("cv_mae_ratio", pa.float64()),
    ("cv_bias_qm", pa.float64()),
    ("cv_bias_ratio", pa.float64()),
    ("spearman_qm", pa.float64()),
    ("n_overlap_months", pa.int32()),
    ("fallback_to_parent", pa.bool_()),
    ("knots_json", pa.string()),
])

HARMONIZED_CELL_ARROW_SCHEMA = pa.schema([
    ("h3_r7", pa.uint64()),
    ("h3_r6", pa.uint64()),
    ("h3_r5", pa.uint64()),
    ("district_id", pa.string()),
    ("year", pa.int16()),
    ("month", pa.int8()),
    ("harmonized", pa.float64()),
    ("source_used", pa.string()),
])


def load_hierarchy(reference_dir: Path | str | None = None) -> tuple[list[str], list[str], dict[str, str]]:
    """Load district IDs, division IDs, and district -> division mapping."""
    ref_dir = Path(reference_dir) if reference_dir else REFERENCE_DIR
    regions_pq = ref_dir / "regions.parquet"
    if not regions_pq.exists():
        raise FileNotFoundError(f"Regions file not found at: {regions_pq}")

    df = pd.read_parquet(regions_pq)
    districts = sorted(df.loc[df["level"] == "adm2", "region_id"].dropna().tolist())
    divisions = sorted(df.loc[df["level"] == "adm1", "region_id"].dropna().tolist())

    dist_to_div: dict[str, str] = {}
    for _, row in df[df["level"] == "adm2"].iterrows():
        dist_to_div[str(row["region_id"])] = str(row["parent_id"])

    return districts, divisions, dist_to_div


def run_harmonization(
    interim_dir: Path | str | None = None,
    reference_dir: Path | str | None = None,
    config: PipelineConfig | None = None,
    overlap_start: tuple[int, int] = (2012, 2),
    overlap_end: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Execute harmonization stage from monthly interim tables to harmonized products."""
    t0 = time.time()
    cfg = config or load_config()
    i_dir = Path(interim_dir) if interim_dir else INTERIM_DIR
    ref_dir = Path(reference_dir) if reference_dir else REFERENCE_DIR

    reg_file = i_dir / "monthly_region.parquet"
    cell_file = i_dir / "monthly_cell.parquet"
    if not reg_file.exists() or not cell_file.exists():
        raise FileNotFoundError(f"Monthly tables not found in {i_dir}. Run aggregate first.")

    out_harm_reg = i_dir / "harmonized_region.parquet"
    out_cal_rep = i_dir / "calibration_report.parquet"
    out_harm_cell = i_dir / "harmonized_cell.parquet"
    out_diagnostics = i_dir / "diagnostics.json"

    logger.info(f"Loading monthly tables from {i_dir}...")
    monthly_reg_df = pd.read_parquet(reg_file)
    monthly_cell_df = pd.read_parquet(cell_file)
    logger.info(
        f"Loaded {len(monthly_reg_df):,} monthly_region rows and {len(monthly_cell_df):,} monthly_cell rows."
    )

    districts, divisions, dist_to_div = load_hierarchy(ref_dir)
    logger.info(f"Loaded {len(districts)} districts across {len(divisions)} divisions.")

    min_mean_modis = cfg.harmonization.min_mean_monthly_modis
    month_pool_width = cfg.harmonization.month_pool_width

    logger.info(
        f"Running harmonization with min_mean_monthly_modis={min_mean_modis}, "
        f"pool_width={month_pool_width}, overlap={overlap_start}.."
    )

    harm_reg_df, cal_rep_df, harm_cell_df, diagnostics = build_harmonization(
        monthly_region_df=monthly_reg_df,
        monthly_cell_df=monthly_cell_df,
        district_ids=districts,
        district_to_division=dist_to_div,
        divisions=divisions,
        min_mean_monthly_modis=min_mean_modis,
        month_pool_width=month_pool_width,
        overlap_start=overlap_start,
        overlap_end=overlap_end,
    )

    # Write Parquet tables
    reg_table = pa.Table.from_pandas(
        harm_reg_df, schema=HARMONIZED_REGION_ARROW_SCHEMA, preserve_index=False
    )
    pq.write_table(reg_table, out_harm_reg, compression="ZSTD", version="2.6")

    cal_rep_table = pa.Table.from_pandas(
        cal_rep_df, schema=CALIBRATION_REPORT_ARROW_SCHEMA, preserve_index=False
    )
    pq.write_table(cal_rep_table, out_cal_rep, compression="ZSTD", version="2.6")

    cell_table = pa.Table.from_pandas(
        harm_cell_df, schema=HARMONIZED_CELL_ARROW_SCHEMA, preserve_index=False
    )
    pq.write_table(cell_table, out_harm_cell, compression="ZSTD", version="2.6")

    with open(out_diagnostics, "w", encoding="utf-8") as f:
        json.dump(diagnostics, f, indent=2)

    elapsed_s = round(time.time() - t0, 2)
    logger.info(
        f"Harmonization complete in {elapsed_s}s: "
        f"harmonized_region={len(harm_reg_df):,} rows, "
        f"calibration_report={len(cal_rep_df):,} rows, "
        f"harmonized_cell={len(harm_cell_df):,} rows."
    )
    logger.info(
        f"Diagnostics: naive_ratio={diagnostics['naive_ratio']:.2f}x -> "
        f"harmonized_ratio={diagnostics['harmonized_ratio']:.2f}x. "
        f"Overlap CV RMSE={diagnostics['overlap_cv_rmse']:.2f}, "
        f"Bias={diagnostics['overlap_cv_bias']:.2f}."
    )
    logger.info(
        f"Method breakdown: QM chosen for {diagnostics['units_qm_count']} units, "
        f"Ratio chosen for {diagnostics['units_ratio_count']} units. "
        f"Fallback to parent division: {diagnostics['units_fallback_count']} districts."
    )

    diagnostics["elapsed_seconds"] = elapsed_s
    return diagnostics


if __name__ == "__main__":
    res = run_harmonization()
    print("Harmonization diagnostics:")
    print(json.dumps(res, indent=2))
