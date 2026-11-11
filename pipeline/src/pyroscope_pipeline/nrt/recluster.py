"""Pure NRT normalization and 3-day boundary-buffer ST-DBSCAN re-clustering.

Pure scientific functions: no disk, network, or clock access.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pyroscope_pipeline.clustering.events import EVENTS_SCHEMA_COLUMNS, build_events
from pyroscope_pipeline.ingest.confidence import filter_modis, filter_viirs
from pyroscope_pipeline.ingest.normalize import normalize_detection_records
from pyroscope_pipeline.ingest.readers import clip_bounding_box


def normalize_nrt_raw(
    modis_raw_df: pd.DataFrame,
    viirs_raw_df: pd.DataFrame,
    bbox: list[float],
    min_modis_conf: int = 30,
    require_type_zero: bool = True,
    allowed_viirs_conf: tuple[str, ...] = ("n", "h"),
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Filter, normalize, and bbox-clip raw NRT MODIS and VIIRS CSV DataFrames."""
    stats = {"raw_rows": 0, "low_confidence": 0, "non_vegetation": 0, "outside_bbox": 0, "kept": 0}
    parts: list[pd.DataFrame] = []

    for family, raw_df in (("MODIS", modis_raw_df), ("VIIRS", viirs_raw_df)):
        if raw_df.empty:
            continue
        stats["raw_rows"] += len(raw_df)
        if family == "MODIS":
            filtered, drops = filter_modis(
                raw_df,
                min_confidence=min_modis_conf,
                require_type_zero=require_type_zero,
            )
        else:
            filtered, drops = filter_viirs(
                raw_df,
                allowed_confidence=allowed_viirs_conf,
                require_type_zero=require_type_zero,
            )
        stats["low_confidence"] += int(drops["low_confidence"])
        stats["non_vegetation"] += int(drops["non_vegetation_type"])
        if filtered.empty:
            continue

        norm = normalize_detection_records(filtered, sensor_family=family, source_file="firms_nrt_api")
        if family == "VIIRS" and "satellite" in filtered.columns:
            sats = filtered["satellite"].astype(str).str.strip().str.upper()
            norm.loc[sats.str.contains("JPSS-1", na=False), "sensor"] = "VIIRS_NOAA20"
            norm.loc[sats.str.contains("JPSS-2", na=False), "sensor"] = "VIIRS_NOAA21"

        norm = norm.loc[norm["acq_ts"].notna()].copy()
        clipped, out_bbox = clip_bounding_box(norm, bbox)
        stats["outside_bbox"] += out_bbox
        if not clipped.empty:
            parts.append(clipped)

    if not parts:
        return pd.DataFrame(), stats

    combined = pd.concat(parts, ignore_index=True).drop_duplicates(
        subset=["sensor", "lat", "lon", "acq_ts"]
    )
    combined = combined.sort_values(["acq_ts", "lat", "lon"], ignore_index=True)
    combined.insert(0, "detection_id", np.arange(1, len(combined) + 1, dtype=np.int64))
    stats["kept"] = len(combined)
    return combined, stats


def _diff_event_months(old_events: pd.DataFrame, new_events: pd.DataFrame) -> set[tuple[int, int]]:
    def _month_sigs(df: pd.DataFrame) -> dict[tuple[int, int], tuple[int, float]]:
        if df.empty:
            return {}
        grp = df.groupby(["year", "month"], as_index=False).agg(
            cnt=("event_id", "count"),
            frp=("frp_sum", "sum"),
        )
        return {
            (int(r["year"]), int(r["month"])): (int(r["cnt"]), round(float(r["frp"]), 4))
            for _, r in grp.iterrows()
        }

    old_s, new_s = _month_sigs(old_events), _month_sigs(new_events)
    return {ym for ym in set(old_s) | set(new_s) if old_s.get(ym) != new_s.get(ym)}


def recluster_with_buffer(
    existing_detections: pd.DataFrame,
    new_detections: pd.DataFrame,
    existing_events: pd.DataFrame,
    cell_map: dict[int, str] | None = None,
    buffer_days: int = 3,
    eps_s_m: float = 2700.0,
    eps_t_hours: float = 24.0,
    min_pts: int = 2,
) -> tuple[pd.DataFrame, pd.DataFrame, set[tuple[int, int]]]:
    """Append `new_detections`, re-cluster trailing `buffer_days`, and return affected `(y, m)`."""
    if new_detections.empty:
        return existing_detections.copy(), existing_events.copy(), set()

    new_ts = pd.to_datetime(new_detections["acq_ts"], utc=True)
    new_months = {(int(ts.year), int(ts.month)) for ts in new_ts}
    buffer_start = new_ts.min().normalize() - pd.Timedelta(days=buffer_days)

    if existing_detections.empty:
        combined_det = new_detections.copy()
    else:
        combined_det = pd.concat([existing_detections, new_detections], ignore_index=True)

    combined_det["acq_ts"] = pd.to_datetime(combined_det["acq_ts"], utc=True)
    combined_det = combined_det.drop_duplicates(
        subset=["sensor", "lat", "lon", "acq_ts"]
    ).sort_values(["acq_ts", "lat", "lon"], ignore_index=True)
    combined_det["detection_id"] = np.arange(1, len(combined_det) + 1, dtype=np.int64)

    recluster_start = buffer_start
    if not existing_events.empty:
        ev_end = pd.to_datetime(existing_events["end_ts"], utc=True)
        ev_start = pd.to_datetime(existing_events["start_ts"], utc=True)
        straddling = existing_events.loc[ev_end >= buffer_start]
        if not straddling.empty:
            recluster_start = min(recluster_start, ev_start.loc[straddling.index].min())
        frozen_events = existing_events.loc[ev_end < recluster_start].copy()
    else:
        frozen_events = pd.DataFrame(columns=EVENTS_SCHEMA_COLUMNS)

    tail_det = combined_det.loc[combined_det["acq_ts"] >= recluster_start].copy()
    reclustered_events, _ = build_events(
        detections_df=tail_det,
        eps_s_m=eps_s_m,
        eps_t_hours=eps_t_hours,
        min_pts=min_pts,
        cell_map=cell_map,
    )

    updated_events = pd.concat([frozen_events, reclustered_events], ignore_index=True)
    if not updated_events.empty:
        updated_events = updated_events.sort_values(["start_ts", "lat", "lon"], ignore_index=True)
        updated_events["event_id"] = np.arange(1, len(updated_events) + 1, dtype=np.int64)

    affected = set(new_months) | _diff_event_months(existing_events, updated_events)
    return combined_det, updated_events, affected
