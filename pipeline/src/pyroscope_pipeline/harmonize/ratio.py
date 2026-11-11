"""Proportional ratio baseline for VIIRS-to-MODIS harmonization."""

from __future__ import annotations

from typing import overload

import numpy as np
from numpy.typing import ArrayLike, NDArray


def fit_ratio(viirs: ArrayLike, modis: ArrayLike) -> float:
    """Fit a proportional scaling ratio ``r = sum(modis) / sum(viirs)``.

    Assumptions & units:
        - ``viirs`` and ``modis`` are paired monthly fire event counts over the overlap.
        - Returns ``0.0`` when ``sum(viirs) <= 0`` so zero-fire series never divide by zero.
    """
    v_arr = np.asarray(viirs, dtype=np.float64).ravel()
    m_arr = np.asarray(modis, dtype=np.float64).ravel()

    if v_arr.shape != m_arr.shape:
        raise ValueError(f"viirs and modis must have identical length: {v_arr.shape} vs {m_arr.shape}")
    if v_arr.size == 0:
        raise ValueError("Cannot fit ratio on empty arrays")

    sum_v = float(np.sum(v_arr))
    if sum_v <= 0.0:
        return 0.0
    sum_m = float(np.sum(m_arr))
    return max(0.0, sum_m / sum_v)


@overload
def apply_ratio(ratio: float, x: float) -> float: ...


@overload
def apply_ratio(
    ratio: float,
    x: NDArray[np.floating] | list[float] | list[int],
) -> NDArray[np.float64]: ...


def apply_ratio(
    ratio: float,
    x: ArrayLike,
) -> float | NDArray[np.float64]:
    """Apply a fitted ratio ``r`` to VIIRS count(s) ``x``, clamped to ``>= 0.0``."""
    scalar_input = np.ndim(x) == 0
    x_arr = np.asarray(x, dtype=np.float64)
    out = np.maximum(0.0, float(ratio) * x_arr)
    if scalar_input:
        return float(out.item())
    return out
