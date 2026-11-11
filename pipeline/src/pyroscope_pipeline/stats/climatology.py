"""Climatology pure engine: baseline monthly statistics across complete years.

Pure scientific functions: no file, network, or clock access.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

CLIMATOLOGY_COLUMNS = [
    "region_id",
    "month",
    "n_years",
    "mean",
    "p50",
    "p90",
    "p95",
    "baseline_year_min",
    "baseline_year_max",
]


def determine_complete_years(harmonized_df: pd.DataFrame) -> dict[str, set[int]]:
    """Identify complete calendar years (all 12 months present, non-provisional) per region.

    Inputs:
        harmonized_df: DataFrame with columns `region_id`, `year`, `month`, `harmonized`
            and optional boolean `provisional`.
    Outputs:
        Mapping from `region_id` to set of complete integer calendar years.
    """
    if harmonized_df.empty:
        return {}

    all_regions = sorted({str(r) for r in harmonized_df["region_id"].dropna().unique()})
    result: dict[str, set[int]] = {rid: set() for rid in all_regions}

    df = harmonized_df[["region_id", "year", "month", "harmonized"]].copy()
    harm_vals = pd.to_numeric(df["harmonized"], errors="coerce")
    valid_mask = (
        df["region_id"].notna()
        & harm_vals.notna()
        & np.isfinite(harm_vals.to_numpy(dtype=np.float64))
        & df["month"].between(1, 12)
    )
    if "provisional" in harmonized_df.columns:
        is_prov = harmonized_df["provisional"].fillna(False).astype(bool)
        valid_mask = valid_mask & (~is_prov)

    valid_df = df.loc[valid_mask].copy()
    if valid_df.empty:
        return result

    valid_df["region_id"] = valid_df["region_id"].astype(str)
    valid_df["year"] = valid_df["year"].astype(int)
    valid_df["month"] = valid_df["month"].astype(int)

    month_counts = (
        valid_df.groupby(["region_id", "year"], sort=False)["month"]
        .nunique()
        .reset_index(name="n_months")
    )
    complete_rows = month_counts[month_counts["n_months"] == 12]
    for rid, yr in zip(complete_rows["region_id"], complete_rows["year"], strict=True):
        result[str(rid)].add(int(yr))

    return result


def resolve_complete_years_map(
    harmonized_df: pd.DataFrame,
    complete_years: dict[str, set[int]] | set[int] | None,
) -> dict[str, set[int]]:
    """Resolve optional complete_years override into a per-region year-set mapping."""
    if complete_years is None:
        return determine_complete_years(harmonized_df)
    if isinstance(complete_years, set):
        regions = {str(r) for r in harmonized_df["region_id"].dropna().unique()}
        return {rid: set(complete_years) for rid in regions}
    return {str(k): set(v) for k, v in complete_years.items()}


def compute_month_climatology(values: ArrayLike) -> tuple[int, float, float, float, float]:
    """Compute sample count, mean, p50, p90, and p95 using linear percentile interpolation.

    Inputs:
        values: 1D array-like of monthly harmonized event counts (MODIS-equivalent events).
    Outputs:
        Tuple `(n_years, mean, p50, p90, p95)`.
    """
    arr = np.asarray(values, dtype=np.float64).ravel()
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise ValueError("Cannot compute climatology from empty values")

    p50, p90, p95 = np.percentile(arr, [50.0, 90.0, 95.0], method="linear")
    return (
        int(arr.size),
        float(np.mean(arr)),
        float(p50),
        float(p90),
        float(p95),
    )


def compute_climatology(
    harmonized_df: pd.DataFrame,
    complete_years: dict[str, set[int]] | set[int] | None = None,
) -> pd.DataFrame:
    """Compute monthly baseline climatology per region across complete years.

    Inputs:
        harmonized_df: DataFrame with `region_id`, `year`, `month`, `harmonized`.
        complete_years: Optional override of complete baseline years (all regions or per-region).
    Outputs:
        DataFrame matching DB_SCHEMA.md `climatology` schema, sorted by `(region_id, month)`.
    """
    if harmonized_df.empty:
        return _cast_climatology(pd.DataFrame(columns=CLIMATOLOGY_COLUMNS))

    years_map = resolve_complete_years_map(harmonized_df, complete_years)
    rows: list[dict[str, object]] = []

    work_df = harmonized_df[["region_id", "year", "month", "harmonized"]].copy()
    work_df["region_id"] = work_df["region_id"].astype(str)
    work_df["year"] = work_df["year"].astype(int)
    work_df["month"] = work_df["month"].astype(int)
    work_df["harmonized"] = pd.to_numeric(work_df["harmonized"], errors="coerce").astype(np.float64)

    for rid in sorted(years_map):
        comp_yrs = sorted(years_map[rid])
        if not comp_yrs:
            continue
        y_min, y_max = comp_yrs[0], comp_yrs[-1]
        reg_sub = work_df[(work_df["region_id"] == rid) & (work_df["year"].isin(comp_yrs))]
        if reg_sub.empty:
            continue

        for m in range(1, 13):
            vals = reg_sub.loc[reg_sub["month"] == m, "harmonized"].to_numpy(dtype=np.float64)
            vals = vals[np.isfinite(vals)]
            if vals.size == 0:
                continue
            n_years, mean_v, p50, p90, p95 = compute_month_climatology(vals)
            rows.append(
                {
                    "region_id": rid,
                    "month": np.int8(m),
                    "n_years": np.int32(n_years),
                    "mean": mean_v,
                    "p50": p50,
                    "p90": p90,
                    "p95": p95,
                    "baseline_year_min": np.int16(y_min),
                    "baseline_year_max": np.int16(y_max),
                }
            )

    if not rows:
        return _cast_climatology(pd.DataFrame(columns=CLIMATOLOGY_COLUMNS))

    out = pd.DataFrame(rows).sort_values(["region_id", "month"], ignore_index=True)
    return _cast_climatology(out[CLIMATOLOGY_COLUMNS])


def _cast_climatology(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            {
                "region_id": pd.Series(dtype="string"),
                "month": pd.Series(dtype="int8"),
                "n_years": pd.Series(dtype="int32"),
                "mean": pd.Series(dtype="float64"),
                "p50": pd.Series(dtype="float64"),
                "p90": pd.Series(dtype="float64"),
                "p95": pd.Series(dtype="float64"),
                "baseline_year_min": pd.Series(dtype="int16"),
                "baseline_year_max": pd.Series(dtype="int16"),
            }
        )
    out = df.copy()
    out["region_id"] = out["region_id"].astype("string")
    out["month"] = out["month"].astype(np.int8)
    out["n_years"] = out["n_years"].astype(np.int32)
    out["mean"] = out["mean"].astype(np.float64)
    out["p50"] = out["p50"].astype(np.float64)
    out["p90"] = out["p90"].astype(np.float64)
    out["p95"] = out["p95"].astype(np.float64)
    out["baseline_year_min"] = out["baseline_year_min"].astype(np.int16)
    out["baseline_year_max"] = out["baseline_year_max"].astype(np.int16)
    return out
