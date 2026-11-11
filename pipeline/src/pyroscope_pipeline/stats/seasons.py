"""Fire seasons pure engine: shortest circular consecutive window capturing threshold share.

Pure scientific functions: no file, network, or clock access.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

SEASONS_COLUMNS = [
    "region_id",
    "start_month",
    "peak_month",
    "end_month",
    "share_of_annual",
    "window_length",
]


def compute_season_from_means(
    monthly_means: ArrayLike,
    share_threshold: float = 0.7,
) -> dict[str, int | float]:
    """Find the shortest circular window of months capturing at least `share_threshold` of total.

    Inputs:
        monthly_means: Length-12 array-like of climatological monthly means ordered Jan (1)..Dec (12).
        share_threshold: Target fraction of the annual sum in (0, 1], default 0.7.
    Outputs:
        Dict with `start_month`, `peak_month`, `end_month` (1..12), `share_of_annual` (0..1),
        and `window_length` (1..12). Ties in window sum go to earliest `start_month`.
    """
    means = np.asarray(monthly_means, dtype=np.float64).ravel()
    if means.size != 12:
        raise ValueError(f"Expected 12 monthly means, got {means.size}")
    if not np.all(np.isfinite(means)) or np.any(means < 0.0):
        raise ValueError("Monthly means must be finite and non-negative")
    if not (0.0 < share_threshold <= 1.0):
        raise ValueError(f"share_threshold must be in (0, 1], got {share_threshold}")

    total = float(np.sum(means))
    if total <= 0.0:
        return {
            "start_month": 1,
            "peak_month": 1,
            "end_month": 1,
            "share_of_annual": 0.0,
            "window_length": 1,
        }

    target_sum = share_threshold * total
    best_indices: list[int] | None = None
    best_sum = -1.0
    best_length = 12

    for length in range(1, 13):
        for start_idx in range(12):
            indices = [(start_idx + offset) % 12 for offset in range(length)]
            win_sum = float(sum(means[i] for i in indices))
            if win_sum + 1e-12 >= target_sum and (
                best_indices is None or win_sum > best_sum + 1e-12
            ):
                best_indices = indices
                best_sum = win_sum
                best_length = length
        if best_indices is not None:
            break

    assert best_indices is not None
    peak_idx = max(best_indices, key=lambda idx: float(means[idx]))
    return {
        "start_month": int(best_indices[0] + 1),
        "peak_month": int(peak_idx + 1),
        "end_month": int(best_indices[-1] + 1),
        "share_of_annual": float(best_sum / total),
        "window_length": int(best_length),
    }


def compute_seasons(
    climatology_df: pd.DataFrame,
    share_threshold: float = 0.7,
) -> pd.DataFrame:
    """Compute circular fire season summary per region from climatology means.

    Inputs:
        climatology_df: DataFrame with `region_id`, `month` (1..12), and `mean`.
        share_threshold: Fraction of annual mean burning defining the season (default 0.7).
    Outputs:
        DataFrame matching DB_SCHEMA.md `seasons` schema, sorted by `region_id`.
    """
    if climatology_df.empty:
        return _cast_seasons(pd.DataFrame(columns=SEASONS_COLUMNS))

    rows: list[dict[str, object]] = []
    work_df = climatology_df[["region_id", "month", "mean"]].copy()
    work_df["region_id"] = work_df["region_id"].astype(str)
    work_df["month"] = work_df["month"].astype(int)
    work_df["mean"] = pd.to_numeric(work_df["mean"], errors="coerce").fillna(0.0).astype(np.float64)

    for rid in sorted(work_df["region_id"].unique()):
        reg_sub = work_df[work_df["region_id"] == rid]
        means_by_month = dict(zip(reg_sub["month"], reg_sub["mean"], strict=True))
        vec = [float(means_by_month.get(m, 0.0)) for m in range(1, 13)]
        season = compute_season_from_means(vec, share_threshold=share_threshold)
        rows.append(
            {
                "region_id": rid,
                "start_month": np.int8(season["start_month"]),
                "peak_month": np.int8(season["peak_month"]),
                "end_month": np.int8(season["end_month"]),
                "share_of_annual": float(season["share_of_annual"]),
                "window_length": np.int32(season["window_length"]),
            }
        )

    if not rows:
        return _cast_seasons(pd.DataFrame(columns=SEASONS_COLUMNS))

    out = pd.DataFrame(rows).sort_values(["region_id"], ignore_index=True)
    return _cast_seasons(out[SEASONS_COLUMNS])


def _cast_seasons(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            {
                "region_id": pd.Series(dtype="string"),
                "start_month": pd.Series(dtype="int8"),
                "peak_month": pd.Series(dtype="int8"),
                "end_month": pd.Series(dtype="int8"),
                "share_of_annual": pd.Series(dtype="float64"),
                "window_length": pd.Series(dtype="int32"),
            }
        )
    out = df.copy()
    out["region_id"] = out["region_id"].astype("string")
    out["start_month"] = out["start_month"].astype(np.int8)
    out["peak_month"] = out["peak_month"].astype(np.int8)
    out["end_month"] = out["end_month"].astype(np.int8)
    out["share_of_annual"] = out["share_of_annual"].astype(np.float64)
    out["window_length"] = out["window_length"].astype(np.int32)
    return out
