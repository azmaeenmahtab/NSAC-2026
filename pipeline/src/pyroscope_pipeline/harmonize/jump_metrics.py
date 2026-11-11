"""Descriptive jump metrics and Q-Q distribution diagnostics.

Pure scientific functions: no file, network, or clock access.
NOTE: Jump metrics are descriptive metrics of the data series jump across the
sensor splice in 2012; they do NOT constitute formal statistical trend tests.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_jump_metrics(
    harmonized_region_df: pd.DataFrame,
    pre_window: tuple[int, int] = (2007, 2011),
    post_window: tuple[int, int] = (2012, 2016),
) -> dict[str, float]:
    """Compute naive splice jump ratio vs harmonized ratio for country BGD.

    Specification:
        - naive_splice: MODIS before 2012-02, raw VIIRS in and after 2012-02.
        - naive_ratio: mean annual naive splice (2012-2016) / mean annual MODIS (2007-2011).
        - harmonized_ratio: mean annual harmonized (2012-2016) / mean annual harmonized (2007-2011).
        - Guard against zero denominators.
    """
    bgd_df = harmonized_region_df[harmonized_region_df["region_id"] == "BGD"].copy()
    if bgd_df.empty:
        return {"naive_ratio": 0.0, "harmonized_ratio": 0.0}

    # Construct naive splice monthly series
    # MODIS before 2012-02, VIIRS on or after 2012-02
    ym = bgd_df["year"].astype(int) * 100 + bgd_df["month"].astype(int)
    is_post_splice = ym >= 201202

    bgd_df["naive_val"] = np.where(
        is_post_splice,
        bgd_df["raw_viirs"].fillna(0.0),
        bgd_df["raw_modis"].fillna(0.0),
    )

    # 1. Pre-window annual sums (2007-2011)
    pre_mask = (bgd_df["year"] >= pre_window[0]) & (bgd_df["year"] <= pre_window[1])
    pre_sub = bgd_df.loc[pre_mask]

    pre_modis_annual = pre_sub.groupby("year")["raw_modis"].sum()
    pre_harm_annual = pre_sub.groupby("year")["harmonized"].sum()

    pre_modis_mean = float(pre_modis_annual.mean()) if not pre_modis_annual.empty else 0.0
    pre_harm_mean = float(pre_harm_annual.mean()) if not pre_harm_annual.empty else 0.0

    # 2. Post-window annual sums (2012-2016)
    post_mask = (bgd_df["year"] >= post_window[0]) & (bgd_df["year"] <= post_window[1])
    post_sub = bgd_df.loc[post_mask]

    post_naive_annual = post_sub.groupby("year")["naive_val"].sum()
    post_harm_annual = post_sub.groupby("year")["harmonized"].sum()

    post_naive_mean = float(post_naive_annual.mean()) if not post_naive_annual.empty else 0.0
    post_harm_mean = float(post_harm_annual.mean()) if not post_harm_annual.empty else 0.0

    naive_ratio = round(post_naive_mean / pre_modis_mean, 4) if pre_modis_mean > 0.0 else 0.0
    harmonized_ratio = round(post_harm_mean / pre_harm_mean, 4) if pre_harm_mean > 0.0 else 0.0

    return {
        "naive_ratio": float(naive_ratio),
        "harmonized_ratio": float(harmonized_ratio),
        "pre_modis_annual_mean": float(pre_modis_mean),
        "post_naive_annual_mean": float(post_naive_mean),
        "post_harmonized_annual_mean": float(post_harm_mean),
    }


def compute_country_cv_metrics(
    district_cv_preds: pd.DataFrame,
    country_modis_overlap: pd.DataFrame,
) -> dict[str, float]:
    """Compute national-level cross-validation error metrics from summed district predictions."""
    if district_cv_preds.empty or country_modis_overlap.empty:
        return {"overlap_cv_rmse": 0.0, "overlap_cv_mae": 0.0, "overlap_cv_bias": 0.0}

    # Sum predictions of all districts per (year, month)
    nat_preds = district_cv_preds.groupby(["year", "month"], as_index=False)["predicted"].sum()
    merged = nat_preds.merge(country_modis_overlap, on=["year", "month"])

    pred_arr = merged["predicted"].to_numpy(dtype=np.float64)
    act_arr = merged["raw_modis"].to_numpy(dtype=np.float64)

    diff = pred_arr - act_arr
    rmse = float(np.sqrt(np.mean(diff * diff)))
    mae = float(np.mean(np.abs(diff)))
    bias = float(np.mean(diff))

    return {
        "overlap_cv_rmse": round(rmse, 4),
        "overlap_cv_mae": round(mae, 4),
        "overlap_cv_bias": round(bias, 4),
    }


def compute_qq_points(harmonized_region_df: pd.DataFrame) -> dict[str, list[float]]:
    """Compute sorted Q-Q distribution points for country BGD during the overlap period."""
    bgd_overlap = harmonized_region_df[
        (harmonized_region_df["region_id"] == "BGD") & harmonized_region_df["in_overlap"]
    ]
    if bgd_overlap.empty:
        return {"viirs": [], "modis": [], "harmonized": []}

    v_sorted = np.sort(bgd_overlap["raw_viirs"].dropna().to_numpy(dtype=np.float64))
    m_sorted = np.sort(bgd_overlap["raw_modis"].dropna().to_numpy(dtype=np.float64))
    h_sorted = np.sort(bgd_overlap["harmonized"].dropna().to_numpy(dtype=np.float64))

    return {
        "viirs": [round(float(x), 2) for x in v_sorted],
        "modis": [round(float(x), 2) for x in m_sorted],
        "harmonized": [round(float(x), 2) for x in h_sorted],
    }
