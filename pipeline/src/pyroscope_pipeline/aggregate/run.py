"""Stage runner: Aggregate events into monthly_cell and monthly_region tables."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pyroscope_pipeline.aggregate.coverage import (
    determine_last_complete_month,
    family_coverage_start,
)
from pyroscope_pipeline.aggregate.monthly import (
    aggregate_monthly_cell,
    aggregate_monthly_region,
    filter_events_by_coverage,
    verify_invariants,
)
from pyroscope_pipeline.common.logging import get_logger
from pyroscope_pipeline.common.paths import INTERIM_DIR, REFERENCE_DIR

logger = get_logger("aggregate")

MONTHLY_CELL_ARROW_SCHEMA = pa.schema([
    ("h3_r7", pa.uint64()),
    ("h3_r6", pa.uint64()),
    ("h3_r5", pa.uint64()),
    ("district_id", pa.string()),
    ("sensor_family", pa.string()),
    ("year", pa.int16()),
    ("month", pa.int8()),
    ("event_count", pa.int32()),
    ("frp_sum", pa.float64()),
])

MONTHLY_REGION_ARROW_SCHEMA = pa.schema([
    ("region_id", pa.string()),
    ("sensor_family", pa.string()),
    ("year", pa.int16()),
    ("month", pa.int8()),
    ("event_count", pa.int64()),
    ("frp_sum", pa.float64()),
])


def load_district_ids(reference_dir: Path | str | None = None) -> list[str]:
    """Load canonical list of 64 Bangladesh ADM2 district IDs."""
    ref_dir = Path(reference_dir) if reference_dir else REFERENCE_DIR
    regions_pq = ref_dir / "regions.parquet"
    if regions_pq.exists():
        df = pd.read_parquet(regions_pq)
        adm2 = df.loc[df["level"] == "adm2", "region_id"].dropna().tolist()
        if adm2:
            return sorted(set(adm2))

    cells_pq = ref_dir / "region_cells.parquet"
    if cells_pq.exists():
        df = pd.read_parquet(cells_pq)
        return sorted(df["region_id"].unique().tolist())

    raise FileNotFoundError(f"Neither regions.parquet nor region_cells.parquet found in {ref_dir}")


def run_aggregation(
    interim_dir: Path | str | None = None,
    reference_dir: Path | str | None = None,
    explicit_end_ym: tuple[int, int] | None = None,
    explicit_viirs_start_ym: tuple[int, int] | None = None,
    explicit_modis_start_ym: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Execute monthly aggregation stage from events.parquet to interim tables."""
    t0 = time.time()
    i_dir = Path(interim_dir) if interim_dir else INTERIM_DIR
    ref_dir = Path(reference_dir) if reference_dir else REFERENCE_DIR

    events_path = i_dir / "events.parquet"
    if not events_path.exists():
        raise FileNotFoundError(f"Events file not found: {events_path}. Run cluster first.")

    out_cell_pq = i_dir / "monthly_cell.parquet"
    out_region_pq = i_dir / "monthly_region.parquet"
    out_manifest = i_dir / "aggregate_manifest.json"

    logger.info(f"Loading events from {events_path}...")
    events_df = pd.read_parquet(events_path)
    logger.info(f"Loaded {len(events_df):,} events.")

    # 1. District IDs
    districts = load_district_ids(ref_dir)
    logger.info(f"Loaded {len(districts)} reference districts.")

    # 2. Determine coverage windows
    last_complete = determine_last_complete_month(events_df, explicit_end_ym)
    modis_start = family_coverage_start(events_df, "MODIS", explicit_modis_start_ym)
    viirs_start = family_coverage_start(events_df, "VIIRS", explicit_viirs_start_ym)

    logger.info(f"Coverage window: MODIS {modis_start} to {last_complete}")
    logger.info(f"Coverage window: VIIRS {viirs_start} to {last_complete} (VERIFIED from data)")

    coverage_ranges = {
        "MODIS": (modis_start, last_complete),
        "VIIRS": (viirs_start, last_complete),
    }

    # 3. Filter events
    filtered_events = filter_events_by_coverage(events_df, coverage_ranges)
    logger.info(f"Events in covered range and ROI: {len(filtered_events):,} / {len(events_df):,}")

    # 4. Aggregate monthly cell (sparse)
    monthly_cell_df = aggregate_monthly_cell(filtered_events)
    logger.info(f"Aggregated monthly_cell: {len(monthly_cell_df):,} sparse cell-months.")

    # 5. Aggregate monthly region (dense)
    monthly_region_df = aggregate_monthly_region(filtered_events, districts, coverage_ranges)
    logger.info(f"Aggregated monthly_region: {len(monthly_region_df):,} dense district-months.")

    # 6. Verify invariants
    verify_invariants(monthly_cell_df, monthly_region_df)
    logger.info("All aggregation invariants successfully verified.")

    # 7. Write Parquet tables
    cell_table = pa.Table.from_pandas(
        monthly_cell_df,
        schema=MONTHLY_CELL_ARROW_SCHEMA,
        preserve_index=False,
    )
    pq.write_table(cell_table, out_cell_pq, compression="ZSTD", version="2.6")

    region_table = pa.Table.from_pandas(
        monthly_region_df,
        schema=MONTHLY_REGION_ARROW_SCHEMA,
        preserve_index=False,
    )
    pq.write_table(region_table, out_region_pq, compression="ZSTD", version="2.6")

    elapsed_s = round(time.time() - t0, 2)
    summary = {
        "input_events": len(events_df),
        "filtered_events": len(filtered_events),
        "monthly_cell_rows": len(monthly_cell_df),
        "monthly_region_rows": len(monthly_region_df),
        "modis_coverage": [list(modis_start), list(last_complete)],
        "viirs_coverage": [list(viirs_start), list(last_complete)],
        "n_districts": len(districts),
        "elapsed_seconds": elapsed_s,
    }

    with open(out_manifest, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Monthly aggregation complete in {elapsed_s}s: tables written to {i_dir}")
    return summary


if __name__ == "__main__":
    res = run_aggregation()
    print("Aggregation Summary:")
    print(json.dumps(res, indent=2))
