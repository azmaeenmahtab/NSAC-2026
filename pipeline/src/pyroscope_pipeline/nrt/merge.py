"""Pure NRT incremental merge engine: stored calibration, downscaling, and MTD anomalies.

Pure scientific functions: no disk, network, or clock access.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from pyroscope_pipeline.aggregate.monthly import aggregate_monthly_cell, aggregate_monthly_region
from pyroscope_pipeline.harmonize.aggregate_up import aggregate_up_regions
from pyroscope_pipeline.harmonize.downscale import downscale_to_cells
from pyroscope_pipeline.nrt.calibrate import harmonize_affected_districts, load_stored_models
from pyroscope_pipeline.nrt.cross_sensor import CrossSensorModel
from pyroscope_pipeline.nrt.recluster import normalize_nrt_raw, recluster_with_buffer
from pyroscope_pipeline.stats.anomalies import evaluate_month_anomaly
from pyroscope_pipeline.stats.assemble import augment_harmonized_with_presets
from pyroscope_pipeline.stats.climatology import determine_complete_years

__all__ = [
    "NrtMergeResult",
    "merge_nrt_tables",
    "normalize_nrt_raw",
    "recluster_with_buffer",
]


@dataclass(frozen=True)
class NrtMergeResult:
    """Updated tables and provenance produced by incremental NRT merge."""

    detections: pd.DataFrame
    events: pd.DataFrame
    monthly_cell: pd.DataFrame
    monthly_region: pd.DataFrame
    harmonized_region: pd.DataFrame
    harmonized_cell: pd.DataFrame
    anomalies: pd.DataFrame
    affected_months: tuple[tuple[int, int], ...]
    unallocated_harmonized: float
    mtd_scale_note: str | None


def _replace_months(
    base_df: pd.DataFrame,
    updated_slice: pd.DataFrame,
    affected_months: set[tuple[int, int]],
    sort_cols: list[str],
) -> pd.DataFrame:
    if base_df.empty:
        return (
            updated_slice.sort_values(sort_cols, ignore_index=True)
            if not updated_slice.empty
            else base_df.copy()
        )
    ym_tuples = list(zip(base_df["year"].astype(int), base_df["month"].astype(int), strict=True))
    keep_mask = [ym not in affected_months for ym in ym_tuples]
    kept = base_df.loc[keep_mask]
    merged = (
        pd.concat([kept, updated_slice], ignore_index=True)
        if not updated_slice.empty
        else kept.copy()
    )
    return merged.sort_values(sort_cols, ignore_index=True)


def _update_anomalies_mtd(
    existing_anom: pd.DataFrame,
    augmented_harm: pd.DataFrame,
    affected_months: set[tuple[int, int]],
    as_of_date: date,
    provisional_ym: int,
) -> tuple[pd.DataFrame, str | None]:
    comp_years_map = determine_complete_years(augmented_harm)
    days_in_m = calendar.monthrange(as_of_date.year, as_of_date.month)[1]
    is_partial = as_of_date.day < days_in_m
    mtd_note = (
        f"Month-to-date anomaly approximation for {as_of_date:%Y-%m}: "
        f"climatological baseline scaled by {as_of_date.day}/{days_in_m} elapsed days."
        if is_partial
        else None
    )

    new_rows: list[dict[str, object]] = []
    for rid in sorted(augmented_harm["region_id"].astype(str).unique()):
        reg_sub = augmented_harm[augmented_harm["region_id"] == rid]
        comp_yrs = comp_years_map.get(rid, set())
        for y, m in sorted(affected_months):
            target = reg_sub[(reg_sub["year"] == y) & (reg_sub["month"] == m)]
            if target.empty:
                continue
            val = float(target["harmonized"].iloc[0])
            base_vals = reg_sub.loc[
                (reg_sub["month"] == m)
                & (reg_sub["year"].isin(comp_yrs))
                & (reg_sub["year"] != y),
                "harmonized",
            ].to_numpy(dtype=np.float64)
            scale = (
                (as_of_date.day / days_in_m)
                if (is_partial and y == as_of_date.year and m == as_of_date.month)
                else 1.0
            )
            rank, cls = evaluate_month_anomaly(val, base_vals * scale)
            new_rows.append(
                {
                    "region_id": rid,
                    "year": np.int16(y),
                    "month": np.int8(m),
                    "value": val,
                    "percentile_rank": rank,
                    "class": cls,
                    "provisional": (y * 100 + m) >= provisional_ym,
                }
            )

    base_anom = existing_anom.copy()
    if "provisional" not in base_anom.columns:
        base_anom["provisional"] = (
            base_anom["year"].astype(int) * 100 + base_anom["month"].astype(int)
        ) >= provisional_ym
    return (
        _replace_months(
            base_anom, pd.DataFrame(new_rows), affected_months, ["region_id", "year", "month"]
        ),
        mtd_note,
    )


def merge_nrt_tables(
    existing_detections: pd.DataFrame,
    new_detections: pd.DataFrame,
    existing_events: pd.DataFrame,
    monthly_cell: pd.DataFrame,
    monthly_region: pd.DataFrame,
    harmonized_region: pd.DataFrame,
    harmonized_cell: pd.DataFrame,
    calibration_report: pd.DataFrame,
    anomalies: pd.DataFrame,
    district_ids: list[str],
    district_to_division: dict[str, str],
    divisions: list[str],
    preset_constituents: dict[str, list[str]],
    provisional_from_date: date,
    new_as_of_date: date,
    cell_map: dict[int, str] | None = None,
    cross_sensor_model: CrossSensorModel | None = None,
    planned_months: set[tuple[int, int]] | None = None,
    buffer_days: int = 3,
    eps_s_m: float = 2700.0,
    eps_t_hours: float = 24.0,
    min_pts: int = 2,
) -> NrtMergeResult:
    """Incrementally merge new NRT detections without altering unaffected months."""
    updated_det, updated_ev, affected_months = recluster_with_buffer(
        existing_detections,
        new_detections,
        existing_events,
        cell_map=cell_map,
        buffer_days=buffer_days,
        eps_s_m=eps_s_m,
        eps_t_hours=eps_t_hours,
        min_pts=min_pts,
    )
    if planned_months:
        affected_months = set(affected_months) | set(planned_months)
    provisional_ym = provisional_from_date.year * 100 + provisional_from_date.month
    if not affected_months:
        return NrtMergeResult(
            updated_det,
            updated_ev,
            monthly_cell.copy(),
            monthly_region.copy(),
            harmonized_region.copy(),
            harmonized_cell.copy(),
            anomalies.copy(),
            (),
            0.0,
            None,
        )

    ev_roi = updated_ev.loc[
        updated_ev["district_id"].notna() & (updated_ev["district_id"] != "")
    ].copy()
    ev_ym = list(zip(ev_roi["year"].astype(int), ev_roi["month"].astype(int), strict=True))
    aff_ev = ev_roi.loc[[ym in affected_months for ym in ev_ym]].copy()

    aff_m_cell = aggregate_monthly_cell(aff_ev)
    updated_m_cell = _replace_months(
        monthly_cell,
        aff_m_cell,
        affected_months,
        ["district_id", "sensor_family", "year", "month", "h3_r7"],
    )

    aff_m_reg = pd.concat(
        [
            aggregate_monthly_region(aff_ev, district_ids, {"MODIS": (ym, ym), "VIIRS": (ym, ym)})
            for ym in sorted(affected_months)
        ],
        ignore_index=True,
    )
    updated_m_reg = _replace_months(
        monthly_region, aff_m_reg, affected_months, ["region_id", "sensor_family", "year", "month"]
    )

    dist_unit_rows = harmonized_region[harmonized_region["region_id"].isin(district_ids)].drop_duplicates(
        "region_id"
    )
    dist_to_unit = dict(
        zip(
            dist_unit_rows["region_id"].astype(str),
            dist_unit_rows["calibration_unit_id"].astype(str),
            strict=True,
        )
    )
    stored_models = load_stored_models(calibration_report)

    aff_dist_harm = harmonize_affected_districts(
        aff_m_reg,
        district_ids,
        dist_to_unit,
        stored_models,
        affected_months,
        cross_sensor_model=cross_sensor_model,
    )
    aff_harm_reg = aggregate_up_regions(aff_dist_harm, district_to_division, divisions)
    aff_harm_reg["provisional"] = (
        aff_harm_reg["year"].astype(int) * 100 + aff_harm_reg["month"].astype(int)
    ) >= provisional_ym

    base_hr = harmonized_region.copy()
    if "provisional" not in base_hr.columns:
        base_hr["provisional"] = (
            base_hr["year"].astype(int) * 100 + base_hr["month"].astype(int)
        ) >= provisional_ym
    updated_harm_reg = _replace_months(
        base_hr, aff_harm_reg, affected_months, ["region_id", "year", "month"]
    )

    aff_harm_cell, unallocated = downscale_to_cells(aff_m_cell, aff_dist_harm)
    updated_harm_cell = _replace_months(
        harmonized_cell, aff_harm_cell, affected_months, ["district_id", "year", "month", "h3_r7"]
    )

    aug_harm = augment_harmonized_with_presets(updated_harm_reg, preset_constituents)
    aug_harm["provisional"] = (
        aug_harm["year"].astype(int) * 100 + aug_harm["month"].astype(int)
    ) >= provisional_ym
    updated_anom, mtd_note = _update_anomalies_mtd(
        anomalies, aug_harm, affected_months, new_as_of_date, provisional_ym
    )

    return NrtMergeResult(
        detections=updated_det,
        events=updated_ev,
        monthly_cell=updated_m_cell,
        monthly_region=updated_m_reg,
        harmonized_region=updated_harm_reg,
        harmonized_cell=updated_harm_cell,
        anomalies=updated_anom,
        affected_months=tuple(sorted(affected_months)),
        unallocated_harmonized=unallocated,
        mtd_scale_note=mtd_note,
    )
