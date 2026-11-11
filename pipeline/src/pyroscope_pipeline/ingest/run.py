"""Stage runner: Ingest and normalize raw FIRMS CSVs into interim detections.parquet."""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pyroscope_pipeline.common.config import PipelineConfig, load_config
from pyroscope_pipeline.common.logging import get_logger
from pyroscope_pipeline.common.paths import RAW_DIR
from pyroscope_pipeline.ingest.confidence import filter_modis, filter_viirs
from pyroscope_pipeline.ingest.normalize import normalize_detection_records
from pyroscope_pipeline.ingest.readers import (
    clip_bounding_box,
    detect_sensor_family,
    read_firms_chunks,
)

logger = get_logger("ingest")


def run_ingest(
    raw_dir: Path | str | None = None,
    interim_dir: Path | str | None = None,
    config: PipelineConfig | None = None,
) -> dict[str, Any]:
    """Execute ingestion pipeline from raw CSVs to detections.parquet."""
    cfg = config or load_config()

    r_dir = Path(raw_dir) if raw_dir else RAW_DIR
    i_dir = Path(interim_dir) if interim_dir else (r_dir.parent / "interim")
    i_dir.mkdir(parents=True, exist_ok=True)
    out_parquet = i_dir / "detections.parquet"

    csv_files = sorted(r_dir.glob("*.csv"))
    if not csv_files:
        logger.warning(f"No CSV files found in raw directory: {r_dir}")
        return {"rows_ingested": 0, "dropped": {}}

    logger.info(f"Starting ingestion of {len(csv_files)} CSV files from {r_dir}")

    total_stats = {
        "raw_rows_read": 0,
        "low_confidence_dropped": 0,
        "non_vegetation_dropped": 0,
        "outside_bbox_dropped": 0,
        "invalid_timestamp_dropped": 0,
        "duplicate_dropped": 0,
        "detections_kept": 0,
    }

    normalized_chunks = []
    bbox = cfg.spatial.bbox_bangladesh

    for csv_file in csv_files:
        sensor_family = detect_sensor_family(csv_file)
        logger.info(f"Processing {csv_file.name} as {sensor_family}")

        file_rows = 0
        for chunk in read_firms_chunks(csv_file, chunksize=100_000):
            total_stats["raw_rows_read"] += len(chunk)
            file_rows += len(chunk)

            # 1. Confidence & Type filter
            if sensor_family == "MODIS":
                filtered, drop_reasons = filter_modis(
                    chunk,
                    min_confidence=cfg.sources.modis.min_confidence,
                    require_type_zero=cfg.sources.modis.require_type_zero,
                )
            else:
                filtered, drop_reasons = filter_viirs(
                    chunk,
                    allowed_confidence=tuple(cfg.sources.viirs.allowed_confidence),
                    require_type_zero=True,
                )

            total_stats["low_confidence_dropped"] += drop_reasons["low_confidence"]
            total_stats["non_vegetation_dropped"] += drop_reasons["non_vegetation_type"]

            if filtered.empty:
                continue

            # 2. Normalize schema & timestamps
            norm = normalize_detection_records(
                filtered,
                sensor_family=sensor_family,
                source_file=csv_file.name,
            )

            # Drop invalid timestamps if any
            valid_ts_mask = norm["acq_ts"].notna()
            ts_dropped = int((~valid_ts_mask).sum())
            total_stats["invalid_timestamp_dropped"] += ts_dropped
            norm = norm.loc[valid_ts_mask].copy()

            # 3. Spatial clip
            clipped, bbox_dropped = clip_bounding_box(norm, bbox)
            total_stats["outside_bbox_dropped"] += bbox_dropped

            if not clipped.empty:
                normalized_chunks.append(clipped)

        logger.info(f"Completed reading {csv_file.name} ({file_rows:,} rows)")

    if not normalized_chunks:
        logger.warning("No records survived filtering.")
        return total_stats

    # Combine all normalized chunks
    combined = pd.concat(normalized_chunks, ignore_index=True)
    initial_count = len(combined)

    # 4. Deduplicate on (sensor, lat, lon, acq_ts)
    dedup_cols = ["sensor", "lat", "lon", "acq_ts"]
    deduped = combined.drop_duplicates(subset=dedup_cols).copy()
    duplicates_count = initial_count - len(deduped)
    total_stats["duplicate_dropped"] = duplicates_count
    logger.info(f"Deduplication removed {duplicates_count:,} duplicate records")

    # 5. Deterministic sort by (acq_ts, lat, lon)
    logger.info("Sorting records deterministically by acq_ts, lat, lon...")
    deduped = deduped.sort_values(["acq_ts", "lat", "lon"]).reset_index(drop=True)

    # 6. Assign sequential INT64 detection_id
    deduped.insert(0, "detection_id", np.arange(1, len(deduped) + 1, dtype=np.int64))

    # Convert datatypes strictly according to DB_SCHEMA.md
    schema = pa.schema(
        [
            ("detection_id", pa.int64()),
            ("sensor", pa.string()),
            ("sensor_family", pa.string()),
            ("lat", pa.float64()),
            ("lon", pa.float64()),
            ("acq_ts", pa.timestamp("us", tz="UTC")),
            ("daynight", pa.string()),
            ("confidence_raw", pa.string()),
            ("confidence_class", pa.string()),
            ("frp_mw", pa.float64()),
            ("scan", pa.float64()),
            ("track", pa.float64()),
            ("version", pa.string()),
            ("source_file", pa.string()),
        ]
    )

    table = pa.Table.from_pandas(deduped, schema=schema, preserve_index=False)
    pq.write_table(table, out_parquet, compression="ZSTD", version="2.6")

    total_stats["detections_kept"] = len(deduped)
    logger.info(
        f"Successfully wrote {len(deduped):,} detections to {out_parquet} "
        f"({out_parquet.stat().st_size / (1024 * 1024):.2f} MB)"
    )

    return total_stats


if __name__ == "__main__":
    stats = run_ingest()
    print("Ingestion Summary:", stats)
