import hashlib
from pathlib import Path

import pandas as pd

from pyroscope_pipeline.common.config import load_config
from pyroscope_pipeline.ingest.run import run_ingest


def test_run_ingest_stage(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    interim_dir = tmp_path / "interim"
    raw_dir.mkdir()
    interim_dir.mkdir()

    # Create synthetic MODIS CSV with duplicate, low confidence, and outside bbox
    modis_csv = raw_dir / "fire_archive_M-C61_test.csv"
    modis_data = (
        "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight,type\n"
        # 1. Valid row
        "23.5,90.2,310.5,1.0,1.0,2020-03-15,52,Terra,MODIS,75,6.1,295.0,15.2,D,0\n"
        # 2. Duplicate of row 1 (same sensor, lat, lon, acq_ts)
        "23.5,90.2,312.0,1.0,1.0,2020-03-15,52,Terra,MODIS,80,6.1,295.0,15.2,D,0\n"
        # 3. Low confidence (<30) -> dropped
        "23.6,90.3,300.0,1.0,1.0,2020-03-15,1330,Aqua,MODIS,25,6.1,290.0,10.0,D,0\n"
        # 4. Non-vegetation type (2) -> dropped
        "23.7,90.4,320.0,1.0,1.0,2020-03-15,1330,Aqua,MODIS,85,6.1,290.0,10.0,D,2\n"
        # 5. Outside bbox (lon 95.0 > 92.8) -> dropped
        "23.8,95.0,310.0,1.0,1.0,2020-03-15,1330,Aqua,MODIS,85,6.1,290.0,10.0,D,0\n"
        # 6. Valid Aqua row
        "24.0,91.0,330.0,1.0,1.0,2020-03-16,720,Aqua,MODIS,90,6.1,300.0,25.0,D,0\n"
    )
    modis_csv.write_text(modis_data, encoding="utf-8")

    # Create synthetic VIIRS CSV
    viirs_csv = raw_dir / "fire_archive_SV-C2_test.csv"
    viirs_data = (
        "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight,type\n"
        # 1. Valid nominal row
        "22.5,91.5,325.0,0.4,0.4,2020-04-01,730,N,VIIRS,n,2.0,298.0,8.5,D,0\n"
        # 2. Low confidence 'l' -> dropped
        "22.6,91.6,305.0,0.4,0.4,2020-04-01,730,N,VIIRS,l,2.0,298.0,3.5,D,0\n"
    )
    viirs_csv.write_text(viirs_data, encoding="utf-8")

    cfg = load_config()
    stats1 = run_ingest(raw_dir=raw_dir, interim_dir=interim_dir, config=cfg)

    out_file = interim_dir / "detections.parquet"
    assert out_file.exists()

    df = pd.read_parquet(out_file)
    # Expected kept:
    # MODIS: row 1, row 6 (2 rows)
    # VIIRS: row 1 (1 row)
    # Total = 3 rows
    assert len(df) == 3
    assert stats1["detections_kept"] == 3
    assert stats1["duplicate_dropped"] == 1
    assert stats1["low_confidence_dropped"] == 2  # 1 MODIS + 1 VIIRS
    assert stats1["non_vegetation_dropped"] == 1
    assert stats1["outside_bbox_dropped"] == 1

    # Check columns match DB_SCHEMA.md
    expected_cols = [
        "detection_id",
        "sensor",
        "sensor_family",
        "lat",
        "lon",
        "acq_ts",
        "daynight",
        "confidence_raw",
        "confidence_class",
        "frp_mw",
        "scan",
        "track",
        "version",
        "source_file",
    ]
    assert list(df.columns) == expected_cols
    assert df["detection_id"].iloc[0] == 1
    assert df["detection_id"].iloc[1] == 2
    assert df["detection_id"].iloc[2] == 3

    # Test idempotency (content SHA256 identical on re-run)
    hash1 = hashlib.sha256(out_file.read_bytes()).hexdigest()
    run_ingest(raw_dir=raw_dir, interim_dir=interim_dir, config=cfg)
    hash2 = hashlib.sha256(out_file.read_bytes()).hexdigest()
    assert hash1 == hash2
