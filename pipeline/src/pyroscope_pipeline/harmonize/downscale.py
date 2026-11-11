"""Proportional downscaling of district harmonized totals to H3 cells.

Pure scientific functions: no file, network, or clock access.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

HARMONIZED_CELL_COLUMNS = [
    "h3_r7",
    "h3_r6",
    "h3_r5",
    "district_id",
    "year",
    "month",
    "harmonized",
    "source_used",
]


def downscale_to_cells(
    monthly_cell_df: pd.DataFrame,
    district_harmonized_df: pd.DataFrame,
) -> tuple[pd.DataFrame, float]:
    """Downscale district harmonized monthly totals proportionally to H3 r7 cells.

    Specification:
        - For 'viirs_calibrated' months:
          When district_raw_viirs > 0:
            cell_harmonized = cell_raw_viirs * (district_harmonized / district_raw_viirs)
          When district_raw_viirs == 0:
            all cells in district are 0; district_harmonized is accumulated into unallocated_harmonized.
        - For 'modis_raw' months:
          cell_harmonized = float(cell_raw_modis)
        - Sparse: only cells with harmonized > 0.0 are output.

    Returns:
        Tuple of (harmonized_cell_df, unallocated_harmonized_total).
    """
    if monthly_cell_df.empty or district_harmonized_df.empty:
        empty_df = pd.DataFrame(columns=HARMONIZED_CELL_COLUMNS)
        return _cast_harmonized_cell(empty_df), 0.0

    # Index district harmonized table by (district_id, year, month)
    dist_lookup = (
        district_harmonized_df.set_index(["region_id", "year", "month"])[
            ["raw_modis", "raw_viirs", "harmonized", "source_used"]
        ]
        .to_dict("index")
    )

    unallocated_harmonized = 0.0
    cell_rows: list[dict[str, object]] = []

    # Process month by month
    grouped = monthly_cell_df.groupby(["district_id", "year", "month"], as_index=False)
    seen_district_months: set[tuple[str, int, int]] = set()

    for (dist_id, y, m), cell_group in grouped:
        dist_key = (str(dist_id), int(y), int(m))
        seen_district_months.add(dist_key)
        dist_info = dist_lookup.get(dist_key)
        if not dist_info:
            continue

        source_used = str(dist_info["source_used"])
        dist_harm = float(dist_info["harmonized"])

        if source_used == "viirs_calibrated":
            viirs_sub = cell_group[cell_group["sensor_family"] == "VIIRS"]
            dist_raw_viirs = float(dist_info["raw_viirs"]) if not np.isnan(dist_info["raw_viirs"]) else 0.0
            cell_sum_viirs = float(viirs_sub["event_count"].sum())

            if dist_raw_viirs > 0.0 and cell_sum_viirs > 0.0:
                scale_factor = dist_harm / dist_raw_viirs
                for _, row in viirs_sub.iterrows():
                    cell_harm = float(row["event_count"]) * scale_factor
                    if cell_harm > 0.0:
                        cell_rows.append({
                            "h3_r7": np.uint64(row["h3_r7"]),
                            "h3_r6": np.uint64(row["h3_r6"]),
                            "h3_r5": np.uint64(row["h3_r5"]),
                            "district_id": str(dist_id),
                            "year": np.int16(y),
                            "month": np.int8(m),
                            "harmonized": cell_harm,
                            "source_used": source_used,
                        })
            elif dist_harm > 0.0:
                unallocated_harmonized += dist_harm

        else:  # modis_raw
            modis_sub = cell_group[cell_group["sensor_family"] == "MODIS"]
            for _, row in modis_sub.iterrows():
                cell_harm = float(row["event_count"])
                if cell_harm > 0.0:
                    cell_rows.append({
                        "h3_r7": np.uint64(row["h3_r7"]),
                        "h3_r6": np.uint64(row["h3_r6"]),
                        "h3_r5": np.uint64(row["h3_r5"]),
                        "district_id": str(dist_id),
                        "year": np.int16(y),
                        "month": np.int8(m),
                        "harmonized": cell_harm,
                        "source_used": source_used,
                    })

    # Check for district-months in district_harmonized that had 0 cell events
    for dist_key, dist_info in dist_lookup.items():
        if dist_key not in seen_district_months:
            dist_harm = float(dist_info["harmonized"])
            source_used = str(dist_info["source_used"])
            if source_used == "viirs_calibrated" and dist_harm > 0.0:
                unallocated_harmonized += dist_harm

    out_df = pd.DataFrame(cell_rows)
    if out_df.empty:
        empty = pd.DataFrame(columns=HARMONIZED_CELL_COLUMNS)
        return _cast_harmonized_cell(empty), float(unallocated_harmonized)

    out_df = out_df.sort_values(
        ["district_id", "year", "month", "h3_r7"],
        ignore_index=True,
    )
    return _cast_harmonized_cell(out_df[HARMONIZED_CELL_COLUMNS]), float(unallocated_harmonized)


def _cast_harmonized_cell(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure strict dtypes on harmonized_cell."""
    out = df.copy()
    if out.empty:
        return pd.DataFrame({
            "h3_r7": pd.Series(dtype="uint64"),
            "h3_r6": pd.Series(dtype="uint64"),
            "h3_r5": pd.Series(dtype="uint64"),
            "district_id": pd.Series(dtype="string"),
            "year": pd.Series(dtype="int16"),
            "month": pd.Series(dtype="int8"),
            "harmonized": pd.Series(dtype="float64"),
            "source_used": pd.Series(dtype="string"),
        })
    out["h3_r7"] = out["h3_r7"].astype(np.uint64)
    out["h3_r6"] = out["h3_r6"].astype(np.uint64)
    out["h3_r5"] = out["h3_r5"].astype(np.uint64)
    out["district_id"] = out["district_id"].astype("string")
    out["year"] = out["year"].astype(np.int16)
    out["month"] = out["month"].astype(np.int8)
    out["harmonized"] = out["harmonized"].astype(np.float64)
    out["source_used"] = out["source_used"].astype("string")
    return out
