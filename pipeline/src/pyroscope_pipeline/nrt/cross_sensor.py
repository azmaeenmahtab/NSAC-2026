"""Pure cross-sensor calibration factor when VIIRS S-NPP is unavailable."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from pyroscope_pipeline.harmonize.evaluate import cv_by_year
from pyroscope_pipeline.harmonize.pooling import select_pooled_pair
from pyroscope_pipeline.harmonize.ratio import fit_ratio
from pyroscope_pipeline.harmonize.units import (
    assign_calibration_units,
    compute_district_mean_modis,
)

MIN_SHARED_MONTHS_FOR_CROSS_SENSOR = 24


@dataclass(frozen=True)
class CrossSensorModel:
    """Cross-sensor ratio scaling secondary VIIRS (NOAA-20/21) to S-NPP equivalents."""

    source_sensor: str
    unit_month_ratios: dict[tuple[str, int], float]
    cv_rmse: float
    cv_bias: float
    n_shared_months: int
    label: str


def fit_cross_sensor_factor(
    snpp_monthly_df: pd.DataFrame,
    secondary_monthly_df: pd.DataFrame,
    district_ids: list[str],
    district_to_division: dict[str, str],
    source_sensor: str = "VIIRS_NOAA20_NRT",
    min_mean_monthly_snpp: float = 3.0,
    pool_width: int = 1,
    min_shared_months: int = MIN_SHARED_MONTHS_FOR_CROSS_SENSOR,
) -> CrossSensorModel | None:
    """Fit S-NPP / NOAA-20 ratio per calibration unit & month-group with LOYO CV.

    Returns `None` if fewer than `min_shared_months` (default 24) overlapping months exist.
    """
    if snpp_monthly_df.empty or secondary_monthly_df.empty:
        return None

    s_df = snpp_monthly_df[["region_id", "year", "month", "event_count"]].rename(
        columns={"event_count": "snpp"}
    )
    n_df = secondary_monthly_df[["region_id", "year", "month", "event_count"]].rename(
        columns={"event_count": "sec"}
    )
    paired = s_df.merge(n_df, on=["region_id", "year", "month"], how="inner")
    shared_yms = paired[["year", "month"]].drop_duplicates()
    n_shared = len(shared_yms)
    if n_shared < min_shared_months:
        return None

    # Reuse D06 district-or-division unit assignment rule on S-NPP baseline counts
    snpp_for_means = snpp_monthly_df.assign(sensor_family="MODIS")
    means = compute_district_mean_modis(snpp_for_means, overlap_start=(1900, 1))
    assignments = assign_calibration_units(
        district_ids=district_ids,
        district_to_division=district_to_division,
        district_mean_modis=means,
        min_mean_monthly_modis=min_mean_monthly_snpp,
    )

    paired["div_id"] = paired["region_id"].map(district_to_division)
    unique_units = sorted({u for u, _ in assignments.values()})
    unit_month_ratios: dict[tuple[str, int], float] = {}
    all_preds: list[np.ndarray] = []
    all_actuals: list[np.ndarray] = []

    for unit_id in unique_units:
        if unit_id in set(paired["region_id"]):
            u_df = paired[paired["region_id"] == unit_id]
        else:
            u_df = paired[paired["div_id"] == unit_id].groupby(
                ["year", "month"], as_index=False
            )[["snpp", "sec"]].sum()
        if u_df.empty:
            continue

        s_arr = u_df["snpp"].to_numpy(dtype=np.float64)
        v_arr = u_df["sec"].to_numpy(dtype=np.float64)
        y_arr = u_df["year"].to_numpy(dtype=np.int64)
        m_arr = u_df["month"].to_numpy(dtype=np.int64)

        if np.unique(y_arr).size >= 2:
            cv_res = cv_by_year(
                modis=s_arr,
                viirs=v_arr,
                year=y_arr,
                month=m_arr,
                method="ratio",
                pool_width=pool_width,
            )
            all_preds.append(cv_res.predictions)
            all_actuals.append(s_arr)

        for target_m in range(1, 13):
            v_pool, s_pool = select_pooled_pair(v_arr, s_arr, m_arr, target_m, pool_width)
            unit_month_ratios[(unit_id, target_m)] = fit_ratio(v_pool, s_pool)

    if not unit_month_ratios:
        return None

    if all_preds:
        pred_cat = np.concatenate(all_preds)
        act_cat = np.concatenate(all_actuals)
        diff = pred_cat - act_cat
        cv_rmse = round(float(np.sqrt(np.mean(diff * diff))), 4)
        cv_bias = round(float(np.mean(diff)), 4)
    else:
        cv_rmse = 0.0
        cv_bias = 0.0

    return CrossSensorModel(
        source_sensor=source_sensor,
        unit_month_ratios=unit_month_ratios,
        cv_rmse=cv_rmse,
        cv_bias=cv_bias,
        n_shared_months=n_shared,
        label=f"provisional, cross-sensor calibrated {source_sensor}",
    )


def unadjusted_provisional_label(viirs_source_used: str) -> str | None:
    """Return honest provisional label when a non-S-NPP VIIRS feed is used without factor."""
    if viirs_source_used == "VIIRS_NOAA20_NRT":
        return "provisional, unadjusted NOAA-20"
    if viirs_source_used == "VIIRS_NOAA21_NRT":
        return "provisional, unadjusted NOAA-21"
    return None
