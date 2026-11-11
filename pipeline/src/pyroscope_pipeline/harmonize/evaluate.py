"""Leave-one-year-out cross-validation and model selection for harmonization."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from pyroscope_pipeline.harmonize.pooling import select_pooled_pair
from pyroscope_pipeline.harmonize.quantile_map import apply_qm, fit_qm
from pyroscope_pipeline.harmonize.ratio import apply_ratio, fit_ratio
from pyroscope_pipeline.harmonize.types import CvMetrics, HarmonizeMethod


def _average_ranks(values: NDArray[np.float64]) -> NDArray[np.float64]:
    """Compute 1-based tie-averaged ranks using pure NumPy."""
    n = values.size
    if n == 0:
        return np.empty(0, dtype=np.float64)
    order = np.argsort(values, kind="mergesort")
    sorted_vals = values[order]

    # Identify starts of unique runs in sorted_vals
    is_new = np.empty(n, dtype=np.bool_)
    is_new[0] = True
    is_new[1:] = sorted_vals[1:] != sorted_vals[:-1]
    group_starts = np.flatnonzero(is_new)
    group_ends = np.empty_like(group_starts)
    group_ends[:-1] = group_starts[1:] - 1
    group_ends[-1] = n - 1

    # Average 1-based rank for a tied group [start, end] is (start + end) / 2 + 1
    avg_group_ranks = 0.5 * (group_starts + group_ends).astype(np.float64) + 1.0
    group_ids = np.cumsum(is_new) - 1
    ranks_sorted = avg_group_ranks[group_ids]

    ranks = np.empty(n, dtype=np.float64)
    ranks[order] = ranks_sorted
    return ranks


def spearman_correlation(x: ArrayLike, y: ArrayLike) -> float:
    """Compute deterministic Spearman rank correlation ``rho`` using pure NumPy.

    Returns ``0.0`` when either series has zero variance (all constant values)
    unless both series are identical constants, in which case returns ``1.0``.
    """
    x_arr = np.asarray(x, dtype=np.float64).ravel()
    y_arr = np.asarray(y, dtype=np.float64).ravel()
    if x_arr.size < 2:
        return 0.0

    rx = _average_ranks(x_arr)
    ry = _average_ranks(y_arr)
    dx = rx - float(np.mean(rx))
    dy = ry - float(np.mean(ry))

    denom = float(np.sqrt(np.sum(dx * dx) * np.sum(dy * dy)))
    if denom <= 1e-15:
        return 1.0 if np.allclose(x_arr, y_arr) else 0.0
    return float(np.clip(np.sum(dx * dy) / denom, -1.0, 1.0))


def _annual_total_rel_error(
    modis: NDArray[np.float64],
    preds: NDArray[np.float64],
    years: NDArray[np.int64],
) -> float:
    """Compute mean absolute relative error of annual totals across overlap years.

    For years where actual MODIS annual total > 0, relative error is
    ``|sum(pred_y) - sum(modis_y)| / sum(modis_y)``. If all annual MODIS totals are 0,
    returns ``0.0`` if all predictions are 0, else ``float(np.mean(np.abs(preds)))``.
    """
    unique_years = np.unique(years)
    rel_errors: list[float] = []
    for y in unique_years:
        mask = years == y
        actual_sum = float(np.sum(modis[mask]))
        pred_sum = float(np.sum(preds[mask]))
        if actual_sum > 0.0:
            rel_errors.append(abs(pred_sum - actual_sum) / actual_sum)
        elif abs(pred_sum) > 1e-12:
            rel_errors.append(abs(pred_sum))
        else:
            rel_errors.append(0.0)
    return float(np.mean(rel_errors)) if rel_errors else 0.0


def cv_by_year(
    modis: ArrayLike,
    viirs: ArrayLike,
    year: ArrayLike,
    month: ArrayLike,
    method: HarmonizeMethod,
    pool_width: int = 1,
) -> CvMetrics:
    """Evaluate ``method`` via leave-one-year-out cross-validation over overlap months.

    Specification:
        - Inputs ``modis``, ``viirs``, ``year``, ``month`` are 1D arrays of equal length
          representing paired monthly fire event counts in the overlap window.
        - For each unique overlap year ``y``, hold out all rows from year ``y``, fit one
          transfer function per target calendar month ``m`` on the remaining years using
          circular calendar-month pooling (``m - pool_width .. m + pool_width``), and
          predict MODIS for year ``y`` from VIIRS.
        - Computes RMSE, MAE, bias (``mean(pred - modis)``), Spearman ``rho`` of monthly
          values, and relative error of annual totals.
    """
    m_arr = np.asarray(modis, dtype=np.float64).ravel()
    v_arr = np.asarray(viirs, dtype=np.float64).ravel()
    y_arr = np.asarray(year, dtype=np.int64).ravel()
    mo_arr = np.asarray(month, dtype=np.int64).ravel()

    n = m_arr.size
    if not (v_arr.size == n and y_arr.size == n and mo_arr.size == n):
        raise ValueError("modis, viirs, year, and month must all have the same length")
    if n == 0:
        raise ValueError("Cannot run cross-validation on empty arrays")
    if method not in ("quantile_map", "ratio"):
        raise ValueError(f"Unsupported harmonization method: {method!r}")

    unique_years = np.unique(y_arr)
    if unique_years.size < 2:
        raise ValueError("cv_by_year requires at least 2 distinct overlap years")

    preds = np.empty(n, dtype=np.float64)

    for held_out_year in unique_years:
        test_mask = y_arr == held_out_year
        train_mask = ~test_mask

        v_train = v_arr[train_mask]
        m_train = m_arr[train_mask]
        mo_train = mo_arr[train_mask]

        test_indices = np.flatnonzero(test_mask)
        test_months = np.unique(mo_arr[test_indices])

        for target_m in test_months:
            v_pool, m_pool = select_pooled_pair(
                v_train,
                m_train,
                mo_train,
                target_month=int(target_m),
                pool_width=pool_width,
            )
            idx_m = test_indices[mo_arr[test_indices] == target_m]
            if method == "quantile_map":
                knots = fit_qm(v_pool, m_pool)
                preds[idx_m] = apply_qm(knots, v_arr[idx_m])
            else:
                r = fit_ratio(v_pool, m_pool)
                preds[idx_m] = apply_ratio(r, v_arr[idx_m])

    diff = preds - m_arr
    rmse = float(np.sqrt(np.mean(diff * diff)))
    mae = float(np.mean(np.abs(diff)))
    bias = float(np.mean(diff))
    rho = spearman_correlation(m_arr, preds)
    annual_rel_err = _annual_total_rel_error(m_arr, preds, y_arr)

    return CvMetrics(
        method=method,
        rmse=rmse,
        mae=mae,
        bias=bias,
        spearman_rho=rho,
        annual_total_rel_error=annual_rel_err,
        n_months=int(n),
        n_years=int(unique_years.size),
        predictions=preds,
    )


def choose_method(cv_qm: CvMetrics, cv_ratio: CvMetrics) -> HarmonizeMethod:
    """Choose between quantile mapping and ratio based on leave-one-year-out CV RMSE.

    The lower RMSE wins; ties (within ``1e-12`` floating-point tolerance or exact tie)
    go to ``"ratio"`` (simpler model).
    """
    if cv_qm.rmse < cv_ratio.rmse - 1e-12:
        return "quantile_map"
    return "ratio"
