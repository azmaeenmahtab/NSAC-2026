"""Monthly aggregation engine for H3 cells and administrative districts.

Pure scientific functions: no disk, network, or clock access.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pyroscope_pipeline.aggregate.coverage import generate_dense_months

MONTHLY_CELL_COLUMNS = [
    "h3_r7",
    "h3_r6",
    "h3_r5",
    "district_id",
    "sensor_family",
    "year",
    "month",
    "event_count",
    "frp_sum",
]

MONTHLY_REGION_COLUMNS = [
    "region_id",
    "sensor_family",
    "year",
    "month",
    "event_count",
    "frp_sum",
]


def filter_events_by_coverage(
    events_df: pd.DataFrame,
    coverage_ranges: dict[str, tuple[tuple[int, int], tuple[int, int]]],
) -> pd.DataFrame:
    """Filter fire events to valid districts and sensor coverage windows.

    Drops events with null district_id (outside ROI) and events occurring
    outside each sensor family's [start_ym, end_ym] coverage range.
    """
    if events_df.empty:
        return events_df.copy()

    # Drop outside ROI
    has_district = events_df["district_id"].notna() & (events_df["district_id"] != "")
    valid_df = events_df.loc[has_district].copy()
    if valid_df.empty:
        return valid_df

    kept_frames: list[pd.DataFrame] = []
    for fam, (start_ym, end_ym) in coverage_ranges.items():
        fam_mask = valid_df["sensor_family"] == fam
        sub = valid_df.loc[fam_mask]
        if sub.empty:
            continue
        ym = sub["year"].astype(int) * 100 + sub["month"].astype(int)
        min_val = start_ym[0] * 100 + start_ym[1]
        max_val = end_ym[0] * 100 + end_ym[1]
        in_range = (ym >= min_val) & (ym <= max_val)
        kept_frames.append(sub.loc[in_range])

    if not kept_frames:
        return pd.DataFrame(columns=events_df.columns)

    return pd.concat(kept_frames, ignore_index=True)


def aggregate_monthly_cell(events_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate fire events to monthly counts and FRP per H3 r7 cell.

    Sparse representation: only cells with at least one event are present.
    """
    if events_df.empty:
        df = pd.DataFrame(columns=MONTHLY_CELL_COLUMNS)
        return _cast_monthly_cell(df)

    group_cols = [
        "h3_r7",
        "h3_r6",
        "h3_r5",
        "district_id",
        "sensor_family",
        "year",
        "month",
    ]

    agg_df = (
        events_df.groupby(group_cols, as_index=False, sort=False)
        .agg(
            event_count=("event_id", "count"),
            frp_sum=("frp_sum", "sum"),
        )
    )

    agg_df["frp_sum"] = agg_df["frp_sum"].round(4)
    agg_df = agg_df.sort_values(
        ["district_id", "sensor_family", "year", "month", "h3_r7"],
        ignore_index=True,
    )
    return _cast_monthly_cell(agg_df[MONTHLY_CELL_COLUMNS])


def aggregate_monthly_region(
    events_df: pd.DataFrame,
    district_ids: list[str],
    coverage_ranges: dict[str, tuple[tuple[int, int], tuple[int, int]]],
) -> pd.DataFrame:
    """Aggregate fire events to dense monthly counts per district.

    Dense representation: every district has a row for every covered month,
    with event_count = 0 and frp_sum = 0.0 when no events occurred.
    """
    # 1. Build dense grid of all (district, family, year, month)
    grid_rows: list[dict[str, object]] = []
    sorted_districts = sorted(set(district_ids))

    for fam, (start_ym, end_ym) in coverage_ranges.items():
        months = generate_dense_months(start_ym, end_ym)
        for y, m in months:
            for dist in sorted_districts:
                grid_rows.append({
                    "region_id": dist,
                    "sensor_family": fam,
                    "year": np.int16(y),
                    "month": np.int8(m),
                })

    grid_df = pd.DataFrame(grid_rows)
    if grid_df.empty:
        empty = pd.DataFrame(columns=MONTHLY_REGION_COLUMNS)
        return _cast_monthly_region(empty)

    # 2. Aggregate actual events if present
    if not events_df.empty:
        ev_agg = (
            events_df.groupby(
                ["district_id", "sensor_family", "year", "month"],
                as_index=False,
                sort=False,
            )
            .agg(
                event_count=("event_id", "count"),
                frp_sum=("frp_sum", "sum"),
            )
            .rename(columns={"district_id": "region_id"})
        )
        merged = grid_df.merge(
            ev_agg,
            on=["region_id", "sensor_family", "year", "month"],
            how="left",
        )
    else:
        merged = grid_df.copy()
        merged["event_count"] = 0
        merged["frp_sum"] = 0.0

    merged["event_count"] = merged["event_count"].fillna(0).astype(np.int64)
    merged["frp_sum"] = merged["frp_sum"].fillna(0.0).round(4).astype(np.float64)

    merged = merged.sort_values(
        ["region_id", "sensor_family", "year", "month"],
        ignore_index=True,
    )
    return _cast_monthly_region(merged[MONTHLY_REGION_COLUMNS])


def verify_invariants(
    monthly_cell: pd.DataFrame,
    monthly_region: pd.DataFrame,
) -> None:
    """Verify mathematical and schema invariants for aggregated tables.

    Raises:
        ValueError: If any invariant is violated.
    """
    # 1. No negative counts or FRP
    if not monthly_cell.empty:
        if (monthly_cell["event_count"] < 0).any():
            raise ValueError("Invariant failed: negative event_count in monthly_cell")
        if (monthly_cell["frp_sum"] < 0.0).any():
            raise ValueError("Invariant failed: negative frp_sum in monthly_cell")

    if not monthly_region.empty:
        if (monthly_region["event_count"] < 0).any():
            raise ValueError("Invariant failed: negative event_count in monthly_region")
        if (monthly_region["frp_sum"] < 0.0).any():
            raise ValueError("Invariant failed: negative frp_sum in monthly_region")

    # 2. One district per cell
    if not monthly_cell.empty:
        cell_districts = monthly_cell.groupby("h3_r7")["district_id"].nunique()
        bad_cells = cell_districts[cell_districts > 1]
        if not bad_cells.empty:
            raise ValueError(
                f"Invariant failed: cell maps to multiple districts: {bad_cells.index.tolist()}"
            )

    # 3. Sum of monthly_cell event_count == sum of monthly_region event_count per family & month
    if monthly_region.empty and not monthly_cell.empty:
        raise ValueError("Invariant failed: monthly_cell has rows but monthly_region is empty")

    if not monthly_region.empty:
        reg_sums = (
            monthly_region.groupby(["sensor_family", "year", "month"])["event_count"]
            .sum()
        )
        if monthly_cell.empty:
            cell_sums = pd.Series(0, index=reg_sums.index)
        else:
            cell_sums = (
                monthly_cell.groupby(["sensor_family", "year", "month"])["event_count"]
                .sum()
            )

        for key, reg_val in reg_sums.items():
            cell_val = cell_sums.get(key, 0)
            if cell_val != reg_val:
                raise ValueError(
                    f"Invariant failed: event count mismatch for {key}: "
                    f"cell={cell_val} vs region={reg_val}"
                )


def _cast_monthly_cell(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure strict dtypes on monthly_cell."""
    out = df.copy()
    if out.empty:
        return pd.DataFrame({
            "h3_r7": pd.Series(dtype="uint64"),
            "h3_r6": pd.Series(dtype="uint64"),
            "h3_r5": pd.Series(dtype="uint64"),
            "district_id": pd.Series(dtype="string"),
            "sensor_family": pd.Series(dtype="string"),
            "year": pd.Series(dtype="int16"),
            "month": pd.Series(dtype="int8"),
            "event_count": pd.Series(dtype="int32"),
            "frp_sum": pd.Series(dtype="float64"),
        })
    out["h3_r7"] = out["h3_r7"].astype(np.uint64)
    out["h3_r6"] = out["h3_r6"].astype(np.uint64)
    out["h3_r5"] = out["h3_r5"].astype(np.uint64)
    out["district_id"] = out["district_id"].astype("string")
    out["sensor_family"] = out["sensor_family"].astype("string")
    out["year"] = out["year"].astype(np.int16)
    out["month"] = out["month"].astype(np.int8)
    out["event_count"] = out["event_count"].astype(np.int32)
    out["frp_sum"] = out["frp_sum"].astype(np.float64)
    return out


def _cast_monthly_region(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure strict dtypes on monthly_region."""
    out = df.copy()
    if out.empty:
        return pd.DataFrame({
            "region_id": pd.Series(dtype="string"),
            "sensor_family": pd.Series(dtype="string"),
            "year": pd.Series(dtype="int16"),
            "month": pd.Series(dtype="int8"),
            "event_count": pd.Series(dtype="int64"),
            "frp_sum": pd.Series(dtype="float64"),
        })
    out["region_id"] = out["region_id"].astype("string")
    out["sensor_family"] = out["sensor_family"].astype("string")
    out["year"] = out["year"].astype(np.int16)
    out["month"] = out["month"].astype(np.int8)
    out["event_count"] = out["event_count"].astype(np.int64)
    out["frp_sum"] = out["frp_sum"].astype(np.float64)
    return out
