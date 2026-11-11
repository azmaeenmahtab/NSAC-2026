"""Calibration unit selection and hierarchy mapping for harmonization.

Pure functions: no network, file, or clock access.
"""

from __future__ import annotations

import pandas as pd


def compute_district_mean_modis(
    monthly_region_df: pd.DataFrame,
    overlap_start: tuple[int, int] = (2012, 2),
    overlap_end: tuple[int, int] | None = None,
) -> dict[str, float]:
    """Compute mean monthly MODIS fire events per district over the overlap period.

    Args:
        monthly_region_df: Dense monthly region DataFrame with 'region_id',
            'sensor_family', 'year', 'month', 'event_count'.
        overlap_start: Start of the overlap window, default (2012, 2).
        overlap_end: Optional end of overlap window.

    Returns:
        Mapping of district_id to mean monthly MODIS event count.
    """
    mod_mask = monthly_region_df["sensor_family"] == "MODIS"
    ym = monthly_region_df["year"].astype(int) * 100 + monthly_region_df["month"].astype(int)
    min_ym = overlap_start[0] * 100 + overlap_start[1]
    overlap_mask = mod_mask & (ym >= min_ym)
    if overlap_end is not None:
        max_ym = overlap_end[0] * 100 + overlap_end[1]
        overlap_mask &= (ym <= max_ym)

    sub = monthly_region_df.loc[overlap_mask]
    if sub.empty:
        return {}

    means = sub.groupby("region_id")["event_count"].mean().to_dict()
    return {str(k): float(v) for k, v in means.items()}


def assign_calibration_units(
    district_ids: list[str],
    district_to_division: dict[str, str],
    district_mean_modis: dict[str, float],
    min_mean_monthly_modis: float = 3.0,
) -> dict[str, tuple[str, bool]]:
    """Determine calibration unit and fallback flag for each district.

    Specification:
        - If district mean monthly MODIS >= min_mean_monthly_modis:
          unit is the district itself; fallback_to_parent = False.
        - Otherwise:
          unit is parent division; fallback_to_parent = True.

    Returns:
        Dict mapping district_id -> (calibration_unit_id, fallback_to_parent).
    """
    assignments: dict[str, tuple[str, bool]] = {}
    for dist in sorted(district_ids):
        mean_val = district_mean_modis.get(dist, 0.0)
        parent_div = district_to_division.get(dist)
        if mean_val >= min_mean_monthly_modis or not parent_div:
            assignments[dist] = (dist, False)
        else:
            assignments[dist] = (parent_div, True)
    return assignments


def build_unit_calibration_series(
    monthly_region_df: pd.DataFrame,
    calibration_unit_id: str,
    district_to_division: dict[str, str],
    overlap_start: tuple[int, int] = (2012, 2),
    overlap_end: tuple[int, int] | None = None,
) -> pd.DataFrame:
    """Extract the paired (MODIS, VIIRS) overlap series for a calibration unit.

    If calibration_unit_id is a division, sums the event counts of all
    districts belonging to that division.
    """
    ym = monthly_region_df["year"].astype(int) * 100 + monthly_region_df["month"].astype(int)
    min_ym = overlap_start[0] * 100 + overlap_start[1]
    mask = ym >= min_ym
    if overlap_end is not None:
        max_ym = overlap_end[0] * 100 + overlap_end[1]
        mask &= (ym <= max_ym)

    sub = monthly_region_df.loc[mask].copy()

    # Identify matching districts
    if calibration_unit_id.startswith("BGD-ADM1-") or calibration_unit_id == "BGD":
        target_districts = {
            dist for dist, div in district_to_division.items()
            if div == calibration_unit_id or calibration_unit_id == "BGD"
        }
        sub = sub[sub["region_id"].isin(target_districts)]
    else:
        sub = sub[sub["region_id"] == calibration_unit_id]

    if sub.empty:
        return pd.DataFrame(columns=["year", "month", "modis", "viirs"])

    # Pivot sensor families to columns: modis, viirs
    grouped = (
        sub.groupby(["year", "month", "sensor_family"], as_index=False)["event_count"]
        .sum()
    )
    pivoted = grouped.pivot(
        index=["year", "month"],
        columns="sensor_family",
        values="event_count",
    ).reset_index()

    pivoted.columns.name = None
    if "MODIS" not in pivoted.columns:
        pivoted["MODIS"] = 0
    if "VIIRS" not in pivoted.columns:
        pivoted["VIIRS"] = 0

    pivoted = pivoted.rename(columns={"MODIS": "modis", "VIIRS": "viirs"})
    pivoted["modis"] = pivoted["modis"].fillna(0).astype(float)
    pivoted["viirs"] = pivoted["viirs"].fillna(0).astype(float)
    return pivoted.sort_values(["year", "month"], ignore_index=True)
