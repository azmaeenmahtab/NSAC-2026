"""Harmonization pipeline builder: pure end-to-end scientific orchestration.

Pure scientific functions: no file, network, or clock access.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from pyroscope_pipeline.harmonize.aggregate_up import aggregate_up_regions
from pyroscope_pipeline.harmonize.downscale import downscale_to_cells
from pyroscope_pipeline.harmonize.evaluate import choose_method, cv_by_year
from pyroscope_pipeline.harmonize.jump_metrics import (
    compute_country_cv_metrics,
    compute_jump_metrics,
    compute_qq_points,
)
from pyroscope_pipeline.harmonize.pooling import select_pooled_pair
from pyroscope_pipeline.harmonize.quantile_map import apply_qm, fit_qm
from pyroscope_pipeline.harmonize.ratio import apply_ratio, fit_ratio
from pyroscope_pipeline.harmonize.types import HarmonizeMethod, QmKnots
from pyroscope_pipeline.harmonize.units import (
    assign_calibration_units,
    build_unit_calibration_series,
    compute_district_mean_modis,
)


def fit_unit_models(
    unit_series: pd.DataFrame,
    method: HarmonizeMethod,
    pool_width: int = 1,
) -> tuple[dict[int, QmKnots | float], dict[str, Any]]:
    """Fit full models for each calendar month 1..12 on overlap series with circular pooling."""
    v_arr = unit_series["viirs"].to_numpy(dtype=np.float64)
    m_arr = unit_series["modis"].to_numpy(dtype=np.float64)
    mo_arr = unit_series["month"].to_numpy(dtype=np.int64)

    models: dict[int, QmKnots | float] = {}
    knots_json_dict: dict[str, Any] = {}

    for m in range(1, 13):
        v_pool, m_pool = select_pooled_pair(
            v_arr, m_arr, mo_arr, target_month=m, pool_width=pool_width
        )
        if method == "quantile_map":
            knots = fit_qm(v_pool, m_pool)
            models[m] = knots
            knots_json_dict[str(m)] = knots.to_dict()
        else:
            r = fit_ratio(v_pool, m_pool)
            models[m] = r
            knots_json_dict[str(m)] = {"ratio": float(r)}

    return models, knots_json_dict


def build_harmonization(
    monthly_region_df: pd.DataFrame,
    monthly_cell_df: pd.DataFrame,
    district_ids: list[str],
    district_to_division: dict[str, str],
    divisions: list[str],
    min_mean_monthly_modis: float = 3.0,
    month_pool_width: int = 1,
    overlap_start: tuple[int, int] = (2012, 2),
    overlap_end: tuple[int, int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Run pure harmonization end-to-end.

    Returns:
        (harmonized_region_df, calibration_report_df, harmonized_cell_df, diagnostics_dict)
    """
    # 1. District mean monthly MODIS in overlap & unit assignment
    dist_means = compute_district_mean_modis(
        monthly_region_df, overlap_start=overlap_start, overlap_end=overlap_end
    )
    unit_assignments = assign_calibration_units(
        district_ids=district_ids,
        district_to_division=district_to_division,
        district_mean_modis=dist_means,
        min_mean_monthly_modis=min_mean_monthly_modis,
    )

    # 2. Fit models and evaluate CV per unique calibration unit
    unique_units = sorted({unit_id for unit_id, _ in unit_assignments.values()})
    unit_models: dict[str, dict[int, QmKnots | float]] = {}
    unit_methods: dict[str, HarmonizeMethod] = {}
    report_rows: list[dict[str, Any]] = []
    unit_cv_preds: dict[str, pd.DataFrame] = {}

    for unit_id in unique_units:
        series = build_unit_calibration_series(
            monthly_region_df=monthly_region_df,
            calibration_unit_id=unit_id,
            district_to_division=district_to_division,
            overlap_start=overlap_start,
            overlap_end=overlap_end,
        )

        # Leave-one-year-out CV
        cv_qm = cv_by_year(
            modis=series["modis"],
            viirs=series["viirs"],
            year=series["year"],
            month=series["month"],
            method="quantile_map",
            pool_width=month_pool_width,
        )
        cv_rat = cv_by_year(
            modis=series["modis"],
            viirs=series["viirs"],
            year=series["year"],
            month=series["month"],
            method="ratio",
            pool_width=month_pool_width,
        )

        chosen = choose_method(cv_qm, cv_rat)
        unit_methods[unit_id] = chosen

        # Fit full 12-month models on overlap
        models, knots_dict = fit_unit_models(series, chosen, pool_width=month_pool_width)
        unit_models[unit_id] = models

        chosen_preds = cv_qm.predictions if chosen == "quantile_map" else cv_rat.predictions
        pred_df = series[["year", "month"]].copy()
        pred_df["predicted"] = chosen_preds
        unit_cv_preds[unit_id] = pred_df

        # Check if any district using this unit fell back
        is_fallback = any(
            fb for d, (uid, fb) in unit_assignments.items() if uid == unit_id
        )

        report_rows.append({
            "calibration_unit_id": unit_id,
            "method_chosen": chosen,
            "cv_rmse_qm": round(cv_qm.rmse, 4),
            "cv_rmse_ratio": round(cv_rat.rmse, 4),
            "cv_mae_qm": round(cv_qm.mae, 4),
            "cv_mae_ratio": round(cv_rat.mae, 4),
            "cv_bias_qm": round(cv_qm.bias, 4),
            "cv_bias_ratio": round(cv_rat.bias, 4),
            "spearman_qm": round(cv_qm.spearman_rho, 4),
            "n_overlap_months": len(series),
            "fallback_to_parent": is_fallback,
            "knots_json": json.dumps(knots_dict),
        })

    calibration_report_df = pd.DataFrame(report_rows).sort_values("calibration_unit_id", ignore_index=True)

    # 3. Apply harmonization to each district series
    district_rows: list[dict[str, Any]] = []
    district_cv_pred_list: list[pd.DataFrame] = []

    # Pivot monthly_region to wide (district_id, year, month) -> raw_modis, raw_viirs
    pivoted_reg = monthly_region_df.pivot(
        index=["region_id", "year", "month"],
        columns="sensor_family",
        values="event_count",
    ).reset_index()

    pivoted_reg["MODIS"] = pivoted_reg["MODIS"].fillna(0).astype(float)
    if "VIIRS" not in pivoted_reg.columns:
        pivoted_reg["VIIRS"] = np.nan
    else:
        pivoted_reg["VIIRS"] = pivoted_reg["VIIRS"].astype(float)

    start_ym_num = overlap_start[0] * 100 + overlap_start[1]

    for dist in sorted(district_ids):
        unit_id, _ = unit_assignments[dist]
        chosen_method = unit_methods[unit_id]
        models = unit_models[unit_id]

        dist_sub = pivoted_reg[pivoted_reg["region_id"] == dist].copy()
        dist_sub = dist_sub.sort_values(["year", "month"])

        for _, row in dist_sub.iterrows():
            y = int(row["year"])
            m = int(row["month"])
            ym_val = y * 100 + m
            raw_m = float(row["MODIS"])
            raw_v = float(row["VIIRS"]) if not np.isnan(row["VIIRS"]) else np.nan

            in_overlap = ym_val >= start_ym_num
            if overlap_end is not None:
                in_overlap = in_overlap and (ym_val <= overlap_end[0] * 100 + overlap_end[1])

            if ym_val >= start_ym_num and not np.isnan(raw_v):
                # Apply model
                model = models[m]
                if chosen_method == "quantile_map":
                    harm_val = apply_qm(model, raw_v)  # type: ignore[arg-type]
                else:
                    harm_val = apply_ratio(model, raw_v)  # type: ignore[arg-type]
                source_used = "viirs_calibrated"
                applied_method: str = chosen_method
            else:
                harm_val = raw_m
                source_used = "modis_raw"
                applied_method = "none"
                raw_v = np.nan

            district_rows.append({
                "region_id": dist,
                "year": np.int16(y),
                "month": np.int8(m),
                "raw_modis": raw_m,
                "raw_viirs": raw_v,
                "harmonized": float(harm_val),
                "source_used": source_used,
                "method": applied_method,
                "calibration_unit_id": unit_id,
                "in_overlap": in_overlap,
            })

        # District CV prediction tracking
        unit_preds = unit_cv_preds[unit_id]
        dist_preds = unit_preds.copy()
        dist_preds["region_id"] = dist
        district_cv_pred_list.append(dist_preds)

    dist_harm_df = pd.DataFrame(district_rows)

    # 4. Aggregate bottom-up to divisions and country
    harmonized_region_df = aggregate_up_regions(
        district_harmonized_df=dist_harm_df,
        district_to_division=district_to_division,
        divisions=divisions,
    )

    # 5. Downscale to cells
    harmonized_cell_df, unallocated_harm = downscale_to_cells(
        monthly_cell_df=monthly_cell_df,
        district_harmonized_df=dist_harm_df,
    )

    # 6. Jump metrics & validation figures
    jump_metrics = compute_jump_metrics(harmonized_region_df)

    # Country CV metrics
    all_district_preds = pd.concat(district_cv_pred_list, ignore_index=True)
    country_modis_overlap = (
        harmonized_region_df[
            (harmonized_region_df["region_id"] == "BGD") & harmonized_region_df["in_overlap"]
        ][["year", "month", "raw_modis"]]
    )
    country_cv = compute_country_cv_metrics(all_district_preds, country_modis_overlap)

    qq_pts = compute_qq_points(harmonized_region_df)

    diagnostics = {
        "naive_ratio": jump_metrics["naive_ratio"],
        "harmonized_ratio": jump_metrics["harmonized_ratio"],
        "pre_modis_annual_mean": jump_metrics["pre_modis_annual_mean"],
        "post_naive_annual_mean": jump_metrics["post_naive_annual_mean"],
        "post_harmonized_annual_mean": jump_metrics["post_harmonized_annual_mean"],
        "overlap_cv_rmse": country_cv["overlap_cv_rmse"],
        "overlap_cv_mae": country_cv["overlap_cv_mae"],
        "overlap_cv_bias": country_cv["overlap_cv_bias"],
        "unallocated_harmonized": round(unallocated_harm, 4),
        "qq_points": qq_pts,
        "n_units": len(unique_units),
        "n_districts": len(district_ids),
        "units_fallback_count": sum(1 for _, fb in unit_assignments.values() if fb),
        "units_qm_count": sum(1 for m in unit_methods.values() if m == "quantile_map"),
        "units_ratio_count": sum(1 for m in unit_methods.values() if m == "ratio"),
    }

    return (
        harmonized_region_df,
        calibration_report_df,
        harmonized_cell_df,
        diagnostics,
    )
