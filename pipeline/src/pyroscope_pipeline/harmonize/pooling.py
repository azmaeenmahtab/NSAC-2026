"""Circular calendar-month pooling for seasonal VIIRS-to-MODIS calibration."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def circular_month_group(target_month: int, pool_width: int = 1) -> tuple[int, ...]:
    """Return the circular calendar-month group centered on ``target_month``.

    Args:
        target_month: Calendar month in 1..12.
        pool_width: Half-width of the circular window in months (default 1 gives
            ``(m - 1, m, m + 1)`` wrapping December <-> January; 0 gives ``(m,)``).

    Returns:
        Tuple of unique calendar months (1..12) in window order.

    Raises:
        ValueError: If ``target_month`` is not in 1..12 or ``pool_width`` < 0.
    """
    if not 1 <= target_month <= 12:
        raise ValueError(f"target_month must be in 1..12, got {target_month}")
    if pool_width < 0:
        raise ValueError(f"pool_width must be >= 0, got {pool_width}")

    seen: list[int] = []
    for offset in range(-pool_width, pool_width + 1):
        m = ((target_month - 1 + offset) % 12) + 1
        if m not in seen:
            seen.append(m)
    return tuple(seen)


def pool_month_mask(
    months: ArrayLike,
    target_month: int,
    pool_width: int = 1,
) -> NDArray[np.bool_]:
    """Build a boolean mask selecting rows belonging to ``target_month``'s pooled window.

    Assumes ``months`` contains UTC calendar months (integers 1..12).
    """
    months_arr = np.asarray(months, dtype=np.int64)
    group = circular_month_group(target_month, pool_width=pool_width)
    return np.isin(months_arr, group)


def select_pooled_pair(
    viirs: ArrayLike,
    modis: ArrayLike,
    months: ArrayLike,
    target_month: int,
    pool_width: int = 1,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Extract paired ``(viirs, modis)`` samples for ``target_month``'s circular pool.

    If the circular pool contains no rows (e.g. sparse Synthetic/CV test with only a
    subset of calendar months), falls back to all provided rows so calibration never
    crashes on partial-year fixtures.
    """
    v_arr = np.asarray(viirs, dtype=np.float64)
    m_arr = np.asarray(modis, dtype=np.float64)
    if v_arr.shape != m_arr.shape:
        raise ValueError(f"viirs and modis shapes must match: {v_arr.shape} vs {m_arr.shape}")

    mask = pool_month_mask(months, target_month=target_month, pool_width=pool_width)
    if not np.any(mask):
        return v_arr.copy(), m_arr.copy()
    return v_arr[mask], m_arr[mask]
