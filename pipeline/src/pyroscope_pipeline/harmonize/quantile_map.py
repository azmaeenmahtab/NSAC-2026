"""Empirical equal-n quantile mapping with duplicate-merging and ratio extrapolation."""

from __future__ import annotations

from typing import overload

import numpy as np
from numpy.typing import ArrayLike, NDArray

from pyroscope_pipeline.harmonize.types import QmKnots


def fit_qm(viirs: ArrayLike, modis: ArrayLike) -> QmKnots:
    """Fit a piecewise-linear VIIRS -> MODIS transfer function via equal-n quantile mapping.

    Assumptions & units:
        - ``viirs`` and ``modis`` are paired monthly fire event counts (non-negative)
          of equal length ``n >= 1`` over the overlap period.
        - Both samples are sorted ascending independently (empirical quantile matching
          at ranks ``k / n``).
        - If values repeat in sorted ``viirs``, duplicate knots are merged by averaging
          their paired sorted ``modis`` values (isotonic grouping), guaranteeing
          strictly increasing ``knots_v`` and non-decreasing ``knots_m``.

    Args:
        viirs: 1D array-like of VIIRS monthly event counts.
        modis: 1D array-like of MODIS monthly event counts.

    Returns:
        :class:`QmKnots` containing ``(knots_v, knots_m)``.
    """
    v_arr = np.asarray(viirs, dtype=np.float64).ravel()
    m_arr = np.asarray(modis, dtype=np.float64).ravel()

    if v_arr.shape != m_arr.shape:
        raise ValueError(f"viirs and modis must have identical length: {v_arr.shape} vs {m_arr.shape}")
    if v_arr.size == 0:
        raise ValueError("Cannot fit quantile mapping on empty arrays")

    v_sorted = np.sort(v_arr)
    m_sorted = np.sort(m_arr)

    unique_v, inverse_idx, counts = np.unique(
        v_sorted,
        return_inverse=True,
        return_counts=True,
    )
    summed_m = np.bincount(inverse_idx, weights=m_sorted)
    mean_m = summed_m / counts.astype(np.float64)

    return QmKnots(
        knots_v=unique_v.astype(np.float64),
        knots_m=np.maximum(0.0, mean_m.astype(np.float64)),
    )


@overload
def apply_qm(knots: QmKnots, x: float) -> float: ...


@overload
def apply_qm(knots: QmKnots, x: NDArray[np.floating] | list[float] | list[int]) -> NDArray[np.float64]: ...


def apply_qm(
    knots: QmKnots,
    x: ArrayLike,
) -> float | NDArray[np.float64]:
    """Evaluate a fitted quantile-mapping transfer function at VIIRS count(s) ``x``.

    Transfer rules:
        1. Inside ``[v_0, v_max]``: piecewise-linear interpolation between adjacent knots.
        2. Below ``v_0`` (``x < v_0``): lowest-knot ratio scaling ``x * (m_0 / v_0)`` if
           ``v_0 > 0``, else ``m_0``.
        3. Above ``v_max`` (``x > v_max``): constant-ratio extrapolation
           ``x * (m_max / v_max)`` if ``v_max > 0``, else ``m_max``.
        4. Non-negativity: output is clamped to ``>= 0.0``.
    """
    scalar_input = np.ndim(x) == 0
    x_arr = np.atleast_1d(np.asarray(x, dtype=np.float64))

    kv = knots.knots_v
    km = knots.knots_m
    if kv.size == 0 or km.size == 0:
        raise ValueError("QmKnots must contain at least one knot")

    v0 = float(kv[0])
    m0 = float(km[0])
    vmax = float(kv[-1])
    mmax = float(km[-1])

    if kv.size == 1:
        out = np.empty_like(x_arr, dtype=np.float64)
        if v0 > 0.0:
            out[...] = x_arr * (m0 / v0)
        else:
            out[...] = m0
    else:
        out = np.asarray(np.interp(x_arr, kv, km), dtype=np.float64)

        below_mask = x_arr < v0
        if np.any(below_mask):
            if v0 > 0.0:
                out[below_mask] = x_arr[below_mask] * (m0 / v0)
            else:
                out[below_mask] = m0

        above_mask = x_arr > vmax
        if np.any(above_mask):
            if vmax > 0.0:
                out[above_mask] = x_arr[above_mask] * (mmax / vmax)
            else:
                out[above_mask] = mmax

    out = np.maximum(0.0, out)
    if scalar_input:
        return float(out.item())
    return out
