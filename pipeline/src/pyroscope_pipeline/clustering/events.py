"""Fire event clustering pure engine.

Clusters normalized satellite detections per sensor family using ST-DBSCAN,
aggregates clustered pixels into physical fire events with geographic centroids,
temporal bounds, FRP metrics, H3 spatial hierarchy, and district assignments.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from pyroscope_pipeline.clustering.h3_index import attach_h3_indices
from pyroscope_pipeline.clustering.regions import assign_districts
from pyroscope_pipeline.clustering.st_dbscan import st_dbscan

EVENTS_SCHEMA_COLUMNS = [
    "event_id",
    "sensor_family",
    "n_pixels",
    "start_ts",
    "end_ts",
    "lat",
    "lon",
    "frp_sum",
    "frp_max",
    "h3_r5",
    "h3_r6",
    "h3_r7",
    "year",
    "month",
    "district_id",
]


def cluster_sensor_family(
    family_df: pd.DataFrame,
    family_name: str,
    eps_s_m: float = 2700.0,
    eps_t_hours: float = 24.0,
    min_pts: int = 2,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Cluster detections for a single sensor family into fire events.

    Args:
        family_df: Detections for one sensor family with lat, lon, acq_ts, frp_mw.
        family_name: 'MODIS' or 'VIIRS'.
        eps_s_m: Spatial neighborhood threshold in meters.
        eps_t_hours: Temporal neighborhood threshold in hours.
        min_pts: Minimum points to form a cluster.

    Returns:
        Tuple of (events_dataframe, stats_dict).
    """
    n_in = len(family_df)
    if n_in == 0:
        empty_events = pd.DataFrame(columns=[
            "sensor_family", "n_pixels", "start_ts", "end_ts",
            "lat", "lon", "frp_sum", "frp_max", "year", "month",
        ])
        return empty_events, {"pixels_in": 0, "events_out": 0, "noise_points": 0}

    # Ensure acq_ts is UTC datetime
    acq_ts = pd.to_datetime(family_df["acq_ts"], utc=True)
    t_min = acq_ts.min()
    t_hours = (acq_ts - t_min).dt.total_seconds() / 3600.0

    lats = family_df["lat"].to_numpy(dtype=np.float64)
    lons = family_df["lon"].to_numpy(dtype=np.float64)
    t_arr = t_hours.to_numpy(dtype=np.float64)

    labels = st_dbscan(
        lat=lats,
        lon=lons,
        t_hours=t_arr,
        eps_s_m=eps_s_m,
        eps_t_hours=eps_t_hours,
        min_pts=min_pts,
    )

    noise_count = int(np.sum(labels == -1))
    valid_mask = labels >= 0

    if not np.any(valid_mask):
        empty_events = pd.DataFrame(columns=[
            "sensor_family", "n_pixels", "start_ts", "end_ts",
            "lat", "lon", "frp_sum", "frp_max", "year", "month",
        ])
        return empty_events, {"pixels_in": n_in, "events_out": 0, "noise_points": noise_count}

    sub_df = pd.DataFrame({
        "cluster_id": labels[valid_mask],
        "lat": lats[valid_mask],
        "lon": lons[valid_mask],
        "acq_ts": acq_ts.iloc[valid_mask].reset_index(drop=True),
        "frp_mw": family_df["frp_mw"].iloc[valid_mask].fillna(0.0).to_numpy(dtype=np.float64),
    })

    # Group by cluster_id and calculate cluster statistics
    grouped = sub_df.groupby("cluster_id", sort=False)
    agg_df = grouped.agg(
        n_pixels=("lat", "count"),
        lat=("lat", "mean"),
        lon=("lon", "mean"),
        start_ts=("acq_ts", "min"),
        end_ts=("acq_ts", "max"),
        frp_sum=("frp_mw", "sum"),
        frp_max=("frp_mw", "max"),
    ).reset_index(drop=True)

    agg_df["sensor_family"] = family_name
    agg_df["start_ts"] = pd.to_datetime(agg_df["start_ts"], utc=True)
    agg_df["end_ts"] = pd.to_datetime(agg_df["end_ts"], utc=True)
    agg_df["year"] = agg_df["start_ts"].dt.year.to_numpy(dtype=np.int16)
    agg_df["month"] = agg_df["start_ts"].dt.month.to_numpy(dtype=np.int8)
    agg_df["n_pixels"] = agg_df["n_pixels"].to_numpy(dtype=np.int32)
    agg_df["frp_sum"] = agg_df["frp_sum"].round(4)
    agg_df["frp_max"] = agg_df["frp_max"].round(4)

    stats = {
        "pixels_in": n_in,
        "events_out": len(agg_df),
        "noise_points": noise_count,
    }
    return agg_df, stats


def build_events(
    detections_df: pd.DataFrame,
    eps_s_m: float = 2700.0,
    eps_t_hours: float = 24.0,
    min_pts: int = 2,
    families: Sequence[str] = ("MODIS", "VIIRS"),
    cell_map: dict[int, str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build unified fire events from raw normalized detections per sensor family."""
    if detections_df.empty:
        empty = pd.DataFrame(columns=EVENTS_SCHEMA_COLUMNS)
        return empty, {"total_pixels": 0, "total_events": 0, "families": {}}

    family_events: list[pd.DataFrame] = []
    family_stats: dict[str, dict[str, int]] = {}

    for fam in families:
        f_mask = detections_df["sensor_family"] == fam
        f_df = detections_df.loc[f_mask]
        ev_df, stats = cluster_sensor_family(
            f_df,
            family_name=fam,
            eps_s_m=eps_s_m,
            eps_t_hours=eps_t_hours,
            min_pts=min_pts,
        )
        family_events.append(ev_df)
        family_stats[fam] = stats

    combined = pd.concat(family_events, ignore_index=True)
    if combined.empty:
        empty = pd.DataFrame(columns=EVENTS_SCHEMA_COLUMNS)
        return empty, {"total_pixels": len(detections_df), "total_events": 0, "families": family_stats}

    # Deterministic sort by (start_ts, lat, lon)
    combined = combined.sort_values(["start_ts", "lat", "lon"]).reset_index(drop=True)
    combined["event_id"] = np.arange(1, len(combined) + 1, dtype=np.int64)

    # Attach H3 spatial index hierarchy (r5, r6, r7 as UINT64)
    with_h3 = attach_h3_indices(combined, lat_col="lat", lon_col="lon")

    # Assign district_id from reference region cells
    final_df = assign_districts(with_h3, cell_col="h3_r7", cell_map=cell_map)

    # Reorder columns strictly per EVENTS_SCHEMA_COLUMNS
    final_df = final_df[EVENTS_SCHEMA_COLUMNS].copy()

    # Calculate outside-ROI counts per family
    for fam in families:
        fam_mask = final_df["sensor_family"] == fam
        outside_count = int(final_df.loc[fam_mask, "district_id"].isna().sum())
        family_stats[fam]["events_outside_roi"] = outside_count

    summary = {
        "total_pixels": len(detections_df),
        "total_events": len(final_df),
        "families": family_stats,
    }
    return final_df, summary

