"""Stage runner: Cluster normalized detections into interim events.parquet."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pyroscope_pipeline.clustering.events import build_events
from pyroscope_pipeline.common.config import PipelineConfig, load_config
from pyroscope_pipeline.common.logging import get_logger
from pyroscope_pipeline.common.paths import INTERIM_DIR, REFERENCE_DIR

logger = get_logger("clustering")

EVENTS_ARROW_SCHEMA = pa.schema([
    ("event_id", pa.int64()),
    ("sensor_family", pa.string()),
    ("n_pixels", pa.int32()),
    ("start_ts", pa.timestamp("us", tz="UTC")),
    ("end_ts", pa.timestamp("us", tz="UTC")),
    ("lat", pa.float64()),
    ("lon", pa.float64()),
    ("frp_sum", pa.float64()),
    ("frp_max", pa.float64()),
    ("h3_r5", pa.uint64()),
    ("h3_r6", pa.uint64()),
    ("h3_r7", pa.uint64()),
    ("year", pa.int16()),
    ("month", pa.int8()),
    ("district_id", pa.string()),
])


def compute_annual_sensor_ratios(events_df: pd.DataFrame, detections_df: pd.DataFrame) -> dict[int, dict[str, Any]]:
    """Compute annual pixel and event counts and VIIRS/MODIS ratios for overlap years."""
    det_year = pd.to_datetime(detections_df["acq_ts"], utc=True).dt.year
    det_counts = (
        pd.DataFrame({"year": det_year, "family": detections_df["sensor_family"]})
        .groupby(["year", "family"])
        .size()
        .unstack(fill_value=0)
    )

    ev_counts = events_df.groupby(["year", "sensor_family"]).size().unstack(fill_value=0)

    all_years = sorted(set(det_counts.index).union(set(ev_counts.index)))
    ratios: dict[int, dict[str, Any]] = {}

    for yr in all_years:
        mod_px = int(det_counts.loc[yr, "MODIS"]) if yr in det_counts.index and "MODIS" in det_counts.columns else 0
        vii_px = int(det_counts.loc[yr, "VIIRS"]) if yr in det_counts.index and "VIIRS" in det_counts.columns else 0
        mod_ev = int(ev_counts.loc[yr, "MODIS"]) if yr in ev_counts.index and "MODIS" in ev_counts.columns else 0
        vii_ev = int(ev_counts.loc[yr, "VIIRS"]) if yr in ev_counts.index and "VIIRS" in ev_counts.columns else 0

        px_ratio = round(vii_px / mod_px, 2) if mod_px > 0 else None
        ev_ratio = round(vii_ev / mod_ev, 2) if mod_ev > 0 else None

        ratios[int(yr)] = {
            "modis_pixels": mod_px,
            "viirs_pixels": vii_px,
            "pixel_ratio_viirs_modis": px_ratio,
            "modis_events": mod_ev,
            "viirs_events": vii_ev,
            "event_ratio_viirs_modis": ev_ratio,
        }
    return ratios


def run_clustering(
    interim_dir: Path | str | None = None,
    config: PipelineConfig | None = None,
    reference_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Execute clustering stage from detections.parquet to events.parquet."""
    t0 = time.time()
    cfg = config or load_config()
    i_dir = Path(interim_dir) if interim_dir else INTERIM_DIR
    ref_dir = Path(reference_dir) if reference_dir else REFERENCE_DIR

    det_path = i_dir / "detections.parquet"
    if not det_path.exists():
        raise FileNotFoundError(f"Detections file not found: {det_path}. Run ingest first.")

    out_parquet = i_dir / "events.parquet"
    out_manifest = i_dir / "events_manifest.json"

    logger.info(f"Loading detections from {det_path}...")
    detections_df = pd.read_parquet(det_path)
    logger.info(f"Loaded {len(detections_df):,} detections. Starting ST-DBSCAN clustering...")

    # Load district cell mapping
    from pyroscope_pipeline.clustering.regions import load_district_cells_map

    cells_pq = ref_dir / "region_cells.parquet"
    cell_map = load_district_cells_map(cells_pq) if cells_pq.exists() else None

    events_df, summary = build_events(
        detections_df=detections_df,
        eps_s_m=cfg.clustering.eps_spatial_meters,
        eps_t_hours=cfg.clustering.eps_temporal_hours,
        min_pts=cfg.clustering.min_pts,
        cell_map=cell_map,
    )

    elapsed_s = round(time.time() - t0, 2)
    logger.info(f"Clustering complete in {elapsed_s}s: {len(events_df):,} events created.")

    # Write strictly validated Parquet table
    table = pa.Table.from_pandas(events_df, schema=EVENTS_ARROW_SCHEMA, preserve_index=False)
    pq.write_table(table, out_parquet, compression="ZSTD", version="2.6")
    logger.info(f"Saved {out_parquet} ({out_parquet.stat().st_size / (1024 * 1024):.2f} MB)")

    # Annual sensor ratios report
    annual_ratios = compute_annual_sensor_ratios(events_df, detections_df)
    summary["annual_ratios"] = annual_ratios
    summary["elapsed_seconds"] = elapsed_s

    with open(out_manifest, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    summary = run_clustering()
    print("Clustering Summary:")
    print(json.dumps(summary, indent=2))

