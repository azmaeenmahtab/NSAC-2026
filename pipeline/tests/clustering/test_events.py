"""Unit tests for fire event clustering engine (Chunk D03)."""

from __future__ import annotations

import pandas as pd
import pytest

from pyroscope_pipeline.clustering.events import (
    EVENTS_SCHEMA_COLUMNS,
    build_events,
)


def test_hand_built_6_detections_clustering() -> None:
    """Verify hand-built 6-detection input with 2 clusters, noise points, and cross-family separation.

    Specification:
    - Hand-built 6-detection input: two clusters with known centroid (mean), n_pixels,
      start and end, FRP sum, and month.
    - A MODIS and a VIIRS pixel at the same place and time must NOT merge (different families).
    """
    # 6 Detections:
    # 1. MODIS: (23.000, 90.000), 2021-03-01 06:00:00 UTC, FRP=10.0
    # 2. MODIS: (23.010, 90.010), 2021-03-01 07:00:00 UTC, FRP=20.0
    #    -> Forms MODIS Cluster 1: 2 pixels, centroid=(23.005, 90.005), start=06:00, end=07:00, FRP_sum=30.0, month=3
    #
    # 3. VIIRS: (23.000, 90.000), 2021-03-01 06:00:00 UTC, FRP=15.0 (SAME PLACE AND TIME AS MODIS ROW 1)
    # 4. VIIRS: (23.004, 90.004), 2021-03-01 06:30:00 UTC, FRP=25.0
    #    -> Forms VIIRS Cluster 1: 2 pixels, centroid=(23.002, 90.002), start=06:00, end=06:30, FRP_sum=40.0, month=3
    #
    # 5. MODIS: (24.000, 91.000), 2021-04-10 12:00:00 UTC, FRP=50.0 (ISOLATED NOISE POINT)
    # 6. VIIRS: (22.000, 92.000), 2021-05-15 03:00:00 UTC, FRP=30.0 (ISOLATED NOISE POINT)
    detections = pd.DataFrame([
        {
            "sensor_family": "MODIS",
            "lat": 23.000,
            "lon": 90.000,
            "acq_ts": pd.Timestamp("2021-03-01 06:00:00", tz="UTC"),
            "frp_mw": 10.0,
        },
        {
            "sensor_family": "MODIS",
            "lat": 23.010,
            "lon": 90.010,
            "acq_ts": pd.Timestamp("2021-03-01 07:00:00", tz="UTC"),
            "frp_mw": 20.0,
        },
        {
            "sensor_family": "VIIRS",
            "lat": 23.000,
            "lon": 90.000,
            "acq_ts": pd.Timestamp("2021-03-01 06:00:00", tz="UTC"),
            "frp_mw": 15.0,
        },
        {
            "sensor_family": "VIIRS",
            "lat": 23.004,
            "lon": 90.004,
            "acq_ts": pd.Timestamp("2021-03-01 06:30:00", tz="UTC"),
            "frp_mw": 25.0,
        },
        {
            "sensor_family": "MODIS",
            "lat": 24.000,
            "lon": 91.000,
            "acq_ts": pd.Timestamp("2021-04-10 12:00:00", tz="UTC"),
            "frp_mw": 50.0,
        },
        {
            "sensor_family": "VIIRS",
            "lat": 22.000,
            "lon": 92.000,
            "acq_ts": pd.Timestamp("2021-05-15 03:00:00", tz="UTC"),
            "frp_mw": 30.0,
        },
    ])

    events_df, summary = build_events(
        detections_df=detections,
        eps_s_m=2700.0,
        eps_t_hours=24.0,
        min_pts=2,
    )

    # Invariants: Exactly 2 events created (1 MODIS, 1 VIIRS); 2 noise points
    assert len(events_df) == 2, f"Expected 2 events, got {len(events_df)}"
    assert summary["total_pixels"] == 6
    assert summary["total_events"] == 2
    assert summary["families"]["MODIS"]["pixels_in"] == 3
    assert summary["families"]["MODIS"]["events_out"] == 1
    assert summary["families"]["MODIS"]["noise_points"] == 1
    assert summary["families"]["VIIRS"]["pixels_in"] == 3
    assert summary["families"]["VIIRS"]["events_out"] == 1
    assert summary["families"]["VIIRS"]["noise_points"] == 1

    # Check MODIS event
    mod_ev = events_df[events_df["sensor_family"] == "MODIS"].iloc[0]
    assert mod_ev["n_pixels"] == 2
    assert pytest.approx(mod_ev["lat"], 1e-4) == 23.005
    assert pytest.approx(mod_ev["lon"], 1e-4) == 90.005
    assert mod_ev["start_ts"] == pd.Timestamp("2021-03-01 06:00:00", tz="UTC")
    assert mod_ev["end_ts"] == pd.Timestamp("2021-03-01 07:00:00", tz="UTC")
    assert pytest.approx(mod_ev["frp_sum"], 1e-4) == 30.0
    assert pytest.approx(mod_ev["frp_max"], 1e-4) == 20.0
    assert mod_ev["year"] == 2021
    assert mod_ev["month"] == 3

    # Check VIIRS event
    vii_ev = events_df[events_df["sensor_family"] == "VIIRS"].iloc[0]
    assert vii_ev["n_pixels"] == 2
    assert pytest.approx(vii_ev["lat"], 1e-4) == 23.002
    assert pytest.approx(vii_ev["lon"], 1e-4) == 90.002
    assert vii_ev["start_ts"] == pd.Timestamp("2021-03-01 06:00:00", tz="UTC")
    assert vii_ev["end_ts"] == pd.Timestamp("2021-03-01 06:30:00", tz="UTC")
    assert pytest.approx(vii_ev["frp_sum"], 1e-4) == 40.0
    assert pytest.approx(vii_ev["frp_max"], 1e-4) == 25.0
    assert vii_ev["year"] == 2021
    assert vii_ev["month"] == 3

    # Invariant: Different families never merge into the same event
    assert mod_ev["sensor_family"] != vii_ev["sensor_family"]
    assert mod_ev["event_id"] != vii_ev["event_id"]


def test_empty_and_noise_only_detections() -> None:
    """Verify build_events handles empty DataFrame or 100% noise points gracefully."""
    empty_df = pd.DataFrame(columns=["sensor_family", "lat", "lon", "acq_ts", "frp_mw"])
    res_empty, _ = build_events(empty_df)
    assert res_empty.empty
    assert list(res_empty.columns) == EVENTS_SCHEMA_COLUMNS

    noise_df = pd.DataFrame([
        {
            "sensor_family": "MODIS",
            "lat": 23.0,
            "lon": 90.0,
            "acq_ts": pd.Timestamp("2021-01-01 00:00:00", tz="UTC"),
            "frp_mw": 10.0,
        },
        {
            "sensor_family": "MODIS",
            "lat": 25.0,
            "lon": 92.0,
            "acq_ts": pd.Timestamp("2021-06-01 00:00:00", tz="UTC"),
            "frp_mw": 20.0,
        },
    ])
    res_noise, stats_noise = build_events(noise_df, min_pts=2)
    assert res_noise.empty
    assert stats_noise["families"]["MODIS"]["noise_points"] == 2
    assert stats_noise["families"]["MODIS"]["events_out"] == 0

