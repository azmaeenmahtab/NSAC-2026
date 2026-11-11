"""Yearly burn statistics pure engine: totals, FRP, rank, vs-mean %, and peak month.

Pure scientific functions: no file, network, or clock access.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from pyroscope_pipeline.stats.climatology import resolve_complete_years_map

YEARLY_COLUMNS = [
    "region_id",
    "year",
    "harmonized_total",
    "frp_sum",
    "rank",
    "vs_mean_pct",
    "peak_month",
]


def compute_region_yearly_stats(
    years: ArrayLike,
    totals: ArrayLike,
    frp_sums: ArrayLike,
    peak_months: ArrayLike,
) -> pd.DataFrame:
    """Compute annual rank (1 = highest) and vs_mean_pct (against all other years) for one region.

    Inputs:
        years: 1D array-like of integer years.
        totals: 1D array-like of annual harmonized event totals.
        frp_sums: 1D array-like of annual Fire Radiative Power sums (MW).
        peak_months: 1D array-like of annual peak calendar months (1..12).
    Outputs:
        DataFrame with columns `year`, `harmonized_total`, `frp_sum`, `rank`,
        `vs_mean_pct`, `peak_month`.
    """
    y_arr = np.asarray(years, dtype=np.int16).ravel()
    t_arr = np.asarray(totals, dtype=np.float64).ravel()
    f_arr = np.asarray(frp_sums, dtype=np.float64).ravel()
    p_arr = np.asarray(peak_months, dtype=np.int8).ravel()

    n = y_arr.size
    if not (t_arr.size == n and f_arr.size == n and p_arr.size == n):
        raise ValueError("years, totals, frp_sums, and peak_months must have the same length")

    if n == 0:
        return pd.DataFrame(columns=YEARLY_COLUMNS[1:])

    sum_all = float(np.sum(t_arr))
    ranks = np.empty(n, dtype=np.int32)
    vs_means = np.empty(n, dtype=np.float64)

    for i in range(n):
        ti = float(t_arr[i])
        ranks[i] = int(1 + np.sum(t_arr > ti))
        if n > 1:
            other_mean = (sum_all - ti) / float(n - 1)
            vs_means[i] = ((ti - other_mean) / other_mean) * 100.0 if other_mean > 0.0 else 0.0
        else:
            vs_means[i] = 0.0

    return pd.DataFrame(
        {
            "year": y_arr,
            "harmonized_total": t_arr,
            "frp_sum": f_arr,
            "rank": ranks,
            "vs_mean_pct": vs_means,
            "peak_month": p_arr,
        }
    )


def aggregate_region_frp(
    harmonized_df: pd.DataFrame,
    monthly_region_df: pd.DataFrame,
    region_constituents: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    """Attach selected-sensor monthly `frp_sum` to each `(region_id, year, month)`.

    Selects `VIIRS` FRP when `source_used == 'viirs_calibrated'`, else `MODIS` FRP, avoiding
    double-counting overlapping sensors. Composite regions listed in `region_constituents`
    (divisions, country, presets) receive the sum of their constituent districts' selected FRP.
    """
    if harmonized_df.empty or monthly_region_df.empty:
        return pd.DataFrame(columns=["region_id", "year", "month", "frp_sum"])

    mr = monthly_region_df[["region_id", "sensor_family", "year", "month", "frp_sum"]].copy()
    mr["region_id"] = mr["region_id"].astype(str)
    mr["sensor_family"] = mr["sensor_family"].astype(str)
    mr["year"] = mr["year"].astype(int)
    mr["month"] = mr["month"].astype(int)
    mr["frp_sum"] = pd.to_numeric(mr["frp_sum"], errors="coerce").fillna(0.0).astype(np.float64)

    hr = harmonized_df[["region_id", "year", "month", "source_used"]].copy()
    hr["region_id"] = hr["region_id"].astype(str)
    hr["year"] = hr["year"].astype(int)
    hr["month"] = hr["month"].astype(int)
    hr["sensor_family"] = np.where(hr["source_used"] == "viirs_calibrated", "VIIRS", "MODIS")

    direct = hr.merge(
        mr,
        on=["region_id", "sensor_family", "year", "month"],
        how="left",
    )
    direct["frp_sum"] = direct["frp_sum"].fillna(0.0)
    direct_map = direct[["region_id", "year", "month", "frp_sum"]]

    if not region_constituents:
        return direct_map

    # Build child-district FRP lookup for composite regions (divisions, BGD, PRESET-CHT)
    composite_frames: list[pd.DataFrame] = [
        direct_map[~direct_map["region_id"].isin(region_constituents)]
    ]

    for comp_id, members in sorted(region_constituents.items()):
        if not members:
            continue
        member_rows = direct_map[direct_map["region_id"].isin(members)]
        if member_rows.empty:
            # Fallback to direct row if members were not present in harmonized_df
            comp_direct = direct_map[direct_map["region_id"] == comp_id]
            if not comp_direct.empty:
                composite_frames.append(comp_direct)
            continue
        summed = member_rows.groupby(["year", "month"], as_index=False)["frp_sum"].sum()
        summed["region_id"] = comp_id
        composite_frames.append(summed[["region_id", "year", "month", "frp_sum"]])

    combined = pd.concat(composite_frames, ignore_index=True)
    return combined


def compute_yearly(
    harmonized_df: pd.DataFrame,
    monthly_region_df: pd.DataFrame | None = None,
    complete_years: dict[str, set[int]] | set[int] | None = None,
    region_constituents: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    """Compute annual harmonized totals, FRP, rank, vs-mean %, and peak month for complete years.

    Inputs:
        harmonized_df: DataFrame with `region_id`, `year`, `month`, `harmonized`, and `source_used`.
        monthly_region_df: Optional DataFrame with district-level `frp_sum` per sensor family.
        complete_years: Optional override of complete calendar years (all regions or per-region).
        region_constituents: Optional mapping of composite region_id -> constituent district_ids.
    Outputs:
        DataFrame matching DB_SCHEMA.md `yearly` schema, sorted by `(region_id, year)`.
    """
    if harmonized_df.empty:
        return _cast_yearly(pd.DataFrame(columns=YEARLY_COLUMNS))

    years_map = resolve_complete_years_map(harmonized_df, complete_years)

    work_df = harmonized_df.copy()
    work_df["region_id"] = work_df["region_id"].astype(str)
    work_df["year"] = work_df["year"].astype(int)
    work_df["month"] = work_df["month"].astype(int)
    work_df["harmonized"] = pd.to_numeric(work_df["harmonized"], errors="coerce").astype(np.float64)

    if monthly_region_df is not None and not monthly_region_df.empty:
        frp_df = aggregate_region_frp(work_df, monthly_region_df, region_constituents)
        work_df = work_df.merge(frp_df, on=["region_id", "year", "month"], how="left")
        work_df["frp_sum"] = work_df["frp_sum"].fillna(0.0)
    else:
        work_df["frp_sum"] = 0.0

    # Filter strictly to complete calendar years per region
    keep_mask = pd.Series(
        [
            int(y) in years_map.get(str(r), set())
            for r, y in zip(work_df["region_id"], work_df["year"], strict=True)
        ],
        index=work_df.index,
    )
    comp_df = work_df.loc[keep_mask].sort_values(["region_id", "year", "month"], ignore_index=True)
    if comp_df.empty:
        return _cast_yearly(pd.DataFrame(columns=YEARLY_COLUMNS))

    region_frames: list[pd.DataFrame] = []
    for rid in sorted(comp_df["region_id"].unique()):
        reg_sub = comp_df[comp_df["region_id"] == rid]
        grouped = reg_sub.groupby("year", as_index=False, sort=True)
        annual = grouped.agg(
            harmonized_total=("harmonized", "sum"),
            frp_sum=("frp_sum", "sum"),
        )
        # idxmax on month-sorted slice resolves exact ties to earliest month
        peak_idx = reg_sub.groupby("year", sort=True)["harmonized"].idxmax()
        peak_months = reg_sub.loc[peak_idx, "month"].to_numpy(dtype=np.int8)

        stats_df = compute_region_yearly_stats(
            years=annual["year"].to_numpy(dtype=np.int16),
            totals=annual["harmonized_total"].to_numpy(dtype=np.float64),
            frp_sums=annual["frp_sum"].to_numpy(dtype=np.float64),
            peak_months=peak_months,
        )
        stats_df.insert(0, "region_id", rid)
        region_frames.append(stats_df)

    out = pd.concat(region_frames, ignore_index=True).sort_values(
        ["region_id", "year"], ignore_index=True
    )
    return _cast_yearly(out[YEARLY_COLUMNS])


def _cast_yearly(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            {
                "region_id": pd.Series(dtype="string"),
                "year": pd.Series(dtype="int16"),
                "harmonized_total": pd.Series(dtype="float64"),
                "frp_sum": pd.Series(dtype="float64"),
                "rank": pd.Series(dtype="int32"),
                "vs_mean_pct": pd.Series(dtype="float64"),
                "peak_month": pd.Series(dtype="int8"),
            }
        )
    out = df.copy()
    out["region_id"] = out["region_id"].astype("string")
    out["year"] = out["year"].astype(np.int16)
    out["harmonized_total"] = out["harmonized_total"].astype(np.float64)
    out["frp_sum"] = out["frp_sum"].astype(np.float64)
    out["rank"] = out["rank"].astype(np.int32)
    out["vs_mean_pct"] = out["vs_mean_pct"].astype(np.float64)
    out["peak_month"] = out["peak_month"].astype(np.int8)
    return out
