"""Integration tests for clustering stage runner and schema invariants (Chunk D03)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from pyroscope_pipeline.clustering.run import run_clustering


@pytest.fixture
def sample_detections_parquet(tmp_path: Path) -> Path:
    """Generate a valid synthetic detections.parquet for stage testing."""
    interim_dir = tmp_path / "interim"
    interim_dir.mkdir(parents=True, exist_ok=True)
    det_file = interim_dir / "detections.parquet"

    # Create detections inside Rangamati (in-country) and in the Bay of Bengal (outside)
    records = [
        # In-country cluster 1 (Rangamati, MODIS)
        {
            "detection_id": 1,
            "sensor": "MODIS_TERRA",
            "sensor_family": "MODIS",
            "lat": 22.650,
            "lon": 92.180,
            "acq_ts": pd.Timestamp("2021-03-10 04:30:00", tz="UTC"),
            "daynight": "D",
            "confidence_raw": "80",
            "confidence_class": "nominal",
            "frp_mw": 25.5,
            "scan": 1.0,
            "track": 1.0,
            "version": "6.1",
            "source_file": "test_modis.csv",
        },
        {
            "detection_id": 2,
            "sensor": "MODIS_AQUA",
            "sensor_family": "MODIS",
            "lat": 22.655,
            "lon": 92.185,
            "acq_ts": pd.Timestamp("2021-03-10 07:15:00", tz="UTC"),
            "daynight": "D",
            "confidence_raw": "95",
            "confidence_class": "high",
            "frp_mw": 34.0,
            "scan": 1.0,
            "track": 1.0,
            "version": "6.1",
            "source_file": "test_modis.csv",
        },
        # In-country cluster 2 (Rangamati, VIIRS)
        {
            "detection_id": 3,
            "sensor": "VIIRS_SNPP",
            "sensor_family": "VIIRS",
            "lat": 22.651,
            "lon": 92.182,
            "acq_ts": pd.Timestamp("2021-03-10 06:00:00", tz="UTC"),
            "daynight": "D",
            "confidence_raw": "n",
            "confidence_class": "nominal",
            "frp_mw": 12.0,
            "scan": 0.4,
            "track": 0.4,
            "version": "2.0",
            "source_file": "test_viirs.csv",
        },
        {
            "detection_id": 4,
            "sensor": "VIIRS_SNPP",
            "sensor_family": "VIIRS",
            "lat": 22.653,
            "lon": 92.184,
            "acq_ts": pd.Timestamp("2021-03-10 06:00:00", tz="UTC"),
            "daynight": "D",
            "confidence_raw": "h",
            "confidence_class": "high",
            "frp_mw": 18.5,
            "scan": 0.4,
            "track": 0.4,
            "version": "2.0",
            "source_file": "test_viirs.csv",
        },
        # Outside Bangladesh cluster (Bay of Bengal, MODIS)
        {
            "detection_id": 5,
            "sensor": "MODIS_TERRA",
            "sensor_family": "MODIS",
            "lat": 20.000,
            "lon": 90.000,
            "acq_ts": pd.Timestamp("2021-04-05 05:00:00", tz="UTC"),
            "daynight": "D",
            "confidence_raw": "85",
            "confidence_class": "nominal",
            "frp_mw": 15.0,
            "scan": 1.0,
            "track": 1.0,
            "version": "6.1",
            "source_file": "test_modis.csv",
        },
        {
            "detection_id": 6,
            "sensor": "MODIS_TERRA",
            "sensor_family": "MODIS",
            "lat": 20.005,
            "lon": 90.005,
            "acq_ts": pd.Timestamp("2021-04-05 06:00:00", tz="UTC"),
            "daynight": "D",
            "confidence_raw": "88",
            "confidence_class": "nominal",
            "frp_mw": 20.0,
            "scan": 1.0,
            "track": 1.0,
            "version": "6.1",
            "source_file": "test_modis.csv",
        },
        # Noise point (MODIS, isolated)
        {
            "detection_id": 7,
            "sensor": "MODIS_TERRA",
            "sensor_family": "MODIS",
            "lat": 25.500,
            "lon": 89.000,
            "acq_ts": pd.Timestamp("2021-08-01 10:00:00", tz="UTC"),
            "daynight": "D",
            "confidence_raw": "70",
            "confidence_class": "nominal",
            "frp_mw": 10.0,
            "scan": 1.0,
            "track": 1.0,
            "version": "6.1",
            "source_file": "test_modis.csv",
        },
    ]

    df = pd.DataFrame(records)
    schema = pa.schema([
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
    ])
    table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
    pq.write_table(table, det_file, compression="ZSTD", version="2.6")
    return interim_dir


def test_clustering_stage_execution_and_schema(sample_detections_parquet: Path) -> None:
    """Verify run_clustering produces valid events.parquet conforming to DB_SCHEMA.md."""
    interim_dir = sample_detections_parquet
    summary = run_clustering(interim_dir=interim_dir)

    out_file = interim_dir / "events.parquet"
    out_manifest = interim_dir / "events_manifest.json"
    assert out_file.exists()
    assert out_manifest.exists()

    assert summary["total_pixels"] == 7
    assert summary["total_events"] == 3  # 2 in-country + 1 outside
    assert summary["families"]["MODIS"]["noise_points"] == 1
    assert summary["families"]["MODIS"]["events_outside_roi"] == 1
    assert summary["families"]["VIIRS"]["events_outside_roi"] == 0

    # Validate DuckDB data types
    con = duckdb.connect(":memory:")
    desc = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{out_file.as_posix()}')").fetchall()
    col_types = {r[0]: r[1] for r in desc}
    con.close()

    expected_types = {
        "event_id": "BIGINT",
        "sensor_family": "VARCHAR",
        "n_pixels": "INTEGER",
        "start_ts": "TIMESTAMP WITH TIME ZONE",
        "end_ts": "TIMESTAMP WITH TIME ZONE",
        "lat": "DOUBLE",
        "lon": "DOUBLE",
        "frp_sum": "DOUBLE",
        "frp_max": "DOUBLE",
        "h3_r5": "UBIGINT",
        "h3_r6": "UBIGINT",
        "h3_r7": "UBIGINT",
        "year": "SMALLINT",
        "month": "TINYINT",
        "district_id": "VARCHAR",
    }
    for col, exp_type in expected_types.items():
        assert col in col_types, f"Missing column {col}"
        assert col_types[col] == exp_type, f"Column {col} has type {col_types[col]}, expected {exp_type}"

    # Verify invariants on data content
    df_events = pd.read_parquet(out_file)
    assert len(df_events) == 3
    assert list(df_events["event_id"]) == [1, 2, 3]

    # Verify district assignment
    in_country = df_events[df_events["lat"] > 21.0]
    assert len(in_country) == 2
    for dist in in_country["district_id"]:
        assert dist == "BGD-ADM2-rangamati"

    outside = df_events[df_events["lat"] < 21.0]
    assert len(outside) == 1
    assert pd.isna(outside["district_id"].iloc[0])


def test_clustering_stage_idempotency_determinism(sample_detections_parquet: Path) -> None:
    """Verify executing run_clustering twice on identical inputs produces identical SHA256 bytes."""
    interim_dir = sample_detections_parquet
    out_file = interim_dir / "events.parquet"

    run_clustering(interim_dir=interim_dir)
    hash1 = hashlib.sha256(out_file.read_bytes()).hexdigest()

    run_clustering(interim_dir=interim_dir)
    hash2 = hashlib.sha256(out_file.read_bytes()).hexdigest()

    assert hash1 == hash2, "Clustering run must be bitwise deterministic across reruns"

