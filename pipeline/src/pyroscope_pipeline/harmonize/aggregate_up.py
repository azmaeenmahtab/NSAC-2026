"""Bottom-up aggregation of harmonized district series to divisions and country.

Pure scientific functions: no file, network, or clock access.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def aggregate_up_regions(
    district_harmonized_df: pd.DataFrame,
    district_to_division: dict[str, str],
    divisions: list[str],
) -> pd.DataFrame:
    """Aggregate district harmonized series bottom-up into divisions and country BGD.

    Specification:
        - Division and country rows are the sum of their constituent districts
          for raw_modis, raw_viirs, and harmonized counts.
        - Preserves strict schema invariants per DB_SCHEMA.md.
    """
    if district_harmonized_df.empty:
        return district_harmonized_df.copy()

    df = district_harmonized_df.copy()
    df["division_id"] = df["region_id"].map(district_to_division)

    # 1. Division aggregations
    div_rows: list[dict[str, object]] = []
    country_rows: list[dict[str, object]] = []

    # Group by (division_id, year, month)
    div_grouped = df.groupby(["division_id", "year", "month"], as_index=False)
    for (div_id, y, m), group in div_grouped:
        first_row = group.iloc[0]
        in_overlap = bool(first_row["in_overlap"])
        source_used = str(first_row["source_used"])

        mod_sum = float(group["raw_modis"].sum())
        harm_sum = float(group["harmonized"].sum())

        if in_overlap or source_used == "viirs_calibrated":
            vii_sum: float | None = float(group["raw_viirs"].sum())
        else:
            vii_sum = np.nan

        div_rows.append({
            "region_id": str(div_id),
            "year": np.int16(y),
            "month": np.int8(m),
            "raw_modis": mod_sum,
            "raw_viirs": vii_sum,
            "harmonized": harm_sum,
            "source_used": source_used,
            "method": "none",
            "calibration_unit_id": str(div_id),
            "in_overlap": in_overlap,
        })

    # Group by (year, month) for Country (BGD)
    country_grouped = df.groupby(["year", "month"], as_index=False)
    for (y, m), group in country_grouped:
        first_row = group.iloc[0]
        in_overlap = bool(first_row["in_overlap"])
        source_used = str(first_row["source_used"])

        mod_sum = float(group["raw_modis"].sum())
        harm_sum = float(group["harmonized"].sum())

        if in_overlap or source_used == "viirs_calibrated":
            vii_sum = float(group["raw_viirs"].sum())
        else:
            vii_sum = np.nan

        country_rows.append({
            "region_id": "BGD",
            "year": np.int16(y),
            "month": np.int8(m),
            "raw_modis": mod_sum,
            "raw_viirs": vii_sum,
            "harmonized": harm_sum,
            "source_used": source_used,
            "method": "none",
            "calibration_unit_id": "BGD",
            "in_overlap": in_overlap,
        })

    # Combine districts, divisions, and country
    clean_districts = df.drop(columns=["division_id"])
    div_df = pd.DataFrame(div_rows)
    country_df = pd.DataFrame(country_rows)

    combined = pd.concat([clean_districts, div_df, country_df], ignore_index=True)
    combined = combined.sort_values(["region_id", "year", "month"], ignore_index=True)

    # Clean types
    combined["region_id"] = combined["region_id"].astype("string")
    combined["year"] = combined["year"].astype(np.int16)
    combined["month"] = combined["month"].astype(np.int8)
    combined["raw_modis"] = combined["raw_modis"].astype(np.float64)
    combined["raw_viirs"] = combined["raw_viirs"].astype(np.float64)
    combined["harmonized"] = combined["harmonized"].astype(np.float64)
    combined["source_used"] = combined["source_used"].astype("string")
    combined["method"] = combined["method"].astype("string")
    combined["calibration_unit_id"] = combined["calibration_unit_id"].astype("string")
    combined["in_overlap"] = combined["in_overlap"].astype(bool)
    return combined
