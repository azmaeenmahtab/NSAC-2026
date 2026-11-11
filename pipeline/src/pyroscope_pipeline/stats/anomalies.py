"""Anomalies pure engine: leave-one-year-out baseline percentile classification.

Pure scientific functions: no file, network, or clock access.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

from pyroscope_pipeline.stats.climatology import resolve_complete_years_map

AnomalyClass = Literal["normal", "elevated", "extreme", "insufficient_data"]

DEFAULT_MIN_BASELINE_YEARS = 8

ANOMALIES_COLUMNS = [
    "region_id",
    "year",
    "month",
    "value",
    "percentile_rank",
    "class",
]


def evaluate_month_anomaly(
    value: float,
    baseline_values: ArrayLike,
    min_baseline_years: int = DEFAULT_MIN_BASELINE_YEARS,
) -> tuple[float, AnomalyClass]:
    """Evaluate a single monthly value against a baseline sample of same-month values.

    Inputs:
        value: Observed or harmonized monthly fire event count.
        baseline_values: Array-like of baseline counts (excluding the evaluated year).
        min_baseline_years: Minimum required baseline sample size (default 8).
    Outputs:
        Tuple `(percentile_rank, class)` where `percentile_rank` is the share of
        baseline values `<= value` (or `nan` when baseline size < `min_baseline_years`),
        and `class` is `extreme` (`> p95`), `elevated` (`> p90`), `normal`, or
        `insufficient_data`.
    """
    base = np.asarray(baseline_values, dtype=np.float64).ravel()
    base = base[np.isfinite(base)]

    val = float(value)
    if not np.isfinite(val) or base.size < min_baseline_years:
        return (float("nan"), "insufficient_data")

    p90, p95 = np.percentile(base, [90.0, 95.0], method="linear")
    rank = float(np.sum(base <= val) / base.size)

    if val > float(p95):
        cls: AnomalyClass = "extreme"
    elif val > float(p90):
        cls = "elevated"
    else:
        cls = "normal"

    return (rank, cls)


def _evaluate_region_anomalies(
    reg_sub: pd.DataFrame,
    region_id: str,
    comp_yrs: set[int],
    min_baseline_years: int,
) -> list[dict[str, object]]:
    """Evaluate all `(year, month)` rows for one region against other complete years."""
    baseline_by_month: dict[int, tuple[NDArray[np.int64], NDArray[np.float64]]] = {}
    base_sub = reg_sub[reg_sub["year"].isin(comp_yrs)]
    for m in range(1, 13):
        m_sub = base_sub[base_sub["month"] == m]
        if not m_sub.empty:
            y_arr = m_sub["year"].to_numpy(dtype=np.int64)
            v_arr = m_sub["harmonized"].to_numpy(dtype=np.float64)
            finite_mask = np.isfinite(v_arr)
            baseline_by_month[m] = (y_arr[finite_mask], v_arr[finite_mask])

    rows: list[dict[str, object]] = []
    years_arr = reg_sub["year"].to_numpy(dtype=np.int64)
    months_arr = reg_sub["month"].to_numpy(dtype=np.int64)
    vals_arr = reg_sub["harmonized"].to_numpy(dtype=np.float64)

    for y, m, val in zip(years_arr, months_arr, vals_arr, strict=True):
        pair = baseline_by_month.get(int(m))
        if pair is not None:
            b_years, b_vals = pair
            base = b_vals[b_years != int(y)]
        else:
            base = np.empty(0, dtype=np.float64)

        rank, cls = evaluate_month_anomaly(
            float(val),
            base,
            min_baseline_years=min_baseline_years,
        )
        rows.append(
            {
                "region_id": region_id,
                "year": np.int16(y),
                "month": np.int8(m),
                "value": float(val),
                "percentile_rank": rank,
                "class": cls,
            }
        )
    return rows


def compute_anomalies(
    harmonized_df: pd.DataFrame,
    complete_years: dict[str, set[int]] | set[int] | None = None,
    min_baseline_years: int = DEFAULT_MIN_BASELINE_YEARS,
) -> pd.DataFrame:
    """Compute monthly anomaly classifications per region using leave-one-year-out baselines.

    Inputs:
        harmonized_df: DataFrame with `region_id`, `year`, `month`, `harmonized`.
        complete_years: Optional override of complete baseline years (all regions or per-region).
        min_baseline_years: Minimum required baseline years (default 8).
    Outputs:
        DataFrame matching DB_SCHEMA.md `anomalies` schema, sorted by `(region_id, year, month)`.
    """
    if harmonized_df.empty:
        return _cast_anomalies(pd.DataFrame(columns=ANOMALIES_COLUMNS))

    years_map = resolve_complete_years_map(harmonized_df, complete_years)

    work_df = harmonized_df[["region_id", "year", "month", "harmonized"]].copy()
    work_df["region_id"] = work_df["region_id"].astype(str)
    work_df["year"] = work_df["year"].astype(int)
    work_df["month"] = work_df["month"].astype(int)
    work_df["harmonized"] = pd.to_numeric(work_df["harmonized"], errors="coerce").astype(np.float64)
    work_df = work_df.sort_values(["region_id", "year", "month"], ignore_index=True)

    all_rows: list[dict[str, object]] = []
    for rid in sorted(work_df["region_id"].unique()):
        reg_sub = work_df[work_df["region_id"] == rid]
        comp_yrs = years_map.get(rid, set())
        all_rows.extend(
            _evaluate_region_anomalies(
                reg_sub=reg_sub,
                region_id=rid,
                comp_yrs=comp_yrs,
                min_baseline_years=min_baseline_years,
            )
        )

    if not all_rows:
        return _cast_anomalies(pd.DataFrame(columns=ANOMALIES_COLUMNS))

    out = pd.DataFrame(all_rows).sort_values(["region_id", "year", "month"], ignore_index=True)
    return _cast_anomalies(out[ANOMALIES_COLUMNS])


def _cast_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            {
                "region_id": pd.Series(dtype="string"),
                "year": pd.Series(dtype="int16"),
                "month": pd.Series(dtype="int8"),
                "value": pd.Series(dtype="float64"),
                "percentile_rank": pd.Series(dtype="float64"),
                "class": pd.Series(dtype="string"),
            }
        )
    out = df.copy()
    out["region_id"] = out["region_id"].astype("string")
    out["year"] = out["year"].astype(np.int16)
    out["month"] = out["month"].astype(np.int8)
    out["value"] = out["value"].astype(np.float64)
    out["percentile_rank"] = out["percentile_rank"].astype(np.float64)
    out["class"] = out["class"].astype("string")
    return out
