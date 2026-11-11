"""Deterministic synthetic fixture generator for PyroScope per S01 specification."""

from pathlib import Path

import h3
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pyroscope_pipeline.common.manifest import DatasetManifest, PipelineCounts, SourceManifest


def generate_fixtures(output_dir: Path | str) -> dict[str, Path]:
    """Generate deterministic Parquet fixture datasets."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1. Regions
    regions_data = [
        {
            "region_id": "BGD",
            "name": "Bangladesh",
            "level": "country",
            "parent_id": None,
            "bbox": [88.0, 20.5, 92.8, 26.7],
            "aliases": ["Bangladesh", "BD"],
        },
        {
            "region_id": "BGD-ADM2-alpha",
            "name": "Alpha District",
            "level": "adm2",
            "parent_id": "BGD",
            "bbox": [89.0, 22.0, 90.0, 23.0],
            "aliases": ["Alpha"],
        },
        {
            "region_id": "BGD-ADM2-beta",
            "name": "Beta District",
            "level": "adm2",
            "parent_id": "BGD",
            "bbox": [91.0, 22.0, 92.0, 23.0],
            "aliases": ["Beta"],
        },
    ]
    df_regions = pd.DataFrame(regions_data)

    # 2. Time range: 2000-11 to 2025-12
    months_list: list[tuple[int, int]] = []
    # 2000: Nov, Dec
    months_list.append((2000, 11))
    months_list.append((2000, 12))
    # 2001 to 2025: all 12 months
    for y in range(2001, 2026):
        for m in range(1, 13):
            months_list.append((y, m))

    base_pattern = [1, 1, 2, 8, 10, 6, 1, 1, 1, 1, 1, 1]  # 1 to 12

    monthly_region_rows = []
    harmonized_region_rows = []

    for y, m in months_list:
        base_val = base_pattern[m - 1] * 10.0
        # Deliberate anomaly for alpha in 2020-05
        if y == 2020 and m == 5:
            alpha_val = 200.0  # 2x normal p95 (100)
        else:
            alpha_val = base_val

        beta_val = alpha_val * 0.5
        bgd_val = alpha_val + beta_val

        region_vals = [
            ("BGD-ADM2-alpha", alpha_val),
            ("BGD-ADM2-beta", beta_val),
            ("BGD", bgd_val),
        ]

        in_overlap = (y > 2012) or (y == 2012 and m >= 2)

        for rid, val in region_vals:
            # MODIS (available full period)
            monthly_region_rows.append(
                {
                    "region_id": rid,
                    "sensor_family": "MODIS",
                    "year": np.int16(y),
                    "month": np.int8(m),
                    "event_count": np.int64(round(val)),
                    "frp_sum": float(val * 25.5),
                }
            )

            # VIIRS (available from 2012-02)
            if in_overlap:
                viirs_count = val * 3.0
                monthly_region_rows.append(
                    {
                        "region_id": rid,
                        "sensor_family": "VIIRS",
                        "year": np.int16(y),
                        "month": np.int8(m),
                        "event_count": np.int64(round(viirs_count)),
                        "frp_sum": float(viirs_count * 15.0),
                    }
                )
                raw_viirs = float(viirs_count)
                source_used = "viirs_calibrated"
                method = "quantile_map"
            else:
                raw_viirs = np.nan
                source_used = "modis_raw"
                method = "none"

            harmonized_region_rows.append(
                {
                    "region_id": rid,
                    "year": np.int16(y),
                    "month": np.int8(m),
                    "raw_modis": float(val),
                    "raw_viirs": raw_viirs,
                    "harmonized": float(val),
                    "source_used": source_used,
                    "method": method,
                    "calibration_unit_id": rid if rid != "BGD" else "BGD",
                    "in_overlap": in_overlap,
                }
            )

    df_monthly_region = pd.DataFrame(monthly_region_rows).sort_values(
        ["region_id", "sensor_family", "year", "month"]
    )
    df_harmonized_region = pd.DataFrame(harmonized_region_rows).sort_values(
        ["region_id", "year", "month"]
    )

    # 3. 200 r7 hex cells (pre-compute parent resolutions)
    center_cell = h3.latlng_to_cell(23.8, 90.4, 7)
    cells = sorted(h3.grid_disk(center_cell, 8))[:200]

    cell_info_alpha = [
        (
            np.uint64(int(c, 16)),
            np.uint64(int(h3.cell_to_parent(c, 6), 16)),
            np.uint64(int(h3.cell_to_parent(c, 5), 16)),
        )
        for c in cells[:100]
    ]
    cell_info_beta = [
        (
            np.uint64(int(c, 16)),
            np.uint64(int(h3.cell_to_parent(c, 6), 16)),
            np.uint64(int(h3.cell_to_parent(c, 5), 16)),
        )
        for c in cells[100:]
    ]

    harmonized_cell_rows = []
    for y, m in months_list:
        in_overlap = (y > 2012) or (y == 2012 and m >= 2)
        source_used = "viirs_calibrated" if in_overlap else "modis_raw"

        # Lookup alpha & beta values
        if y == 2020 and m == 5:
            alpha_val = 200.0
        else:
            alpha_val = base_pattern[m - 1] * 10.0
        beta_val = alpha_val * 0.5
        alpha_cell_val = float(alpha_val * 0.01)
        beta_cell_val = float(beta_val * 0.01)

        for r7, r6, r5 in cell_info_alpha:
            harmonized_cell_rows.append(
                {
                    "h3_r7": r7,
                    "h3_r6": r6,
                    "h3_r5": r5,
                    "district_id": "BGD-ADM2-alpha",
                    "year": np.int16(y),
                    "month": np.int8(m),
                    "harmonized": alpha_cell_val,
                    "source_used": source_used,
                }
            )

        for r7, r6, r5 in cell_info_beta:
            harmonized_cell_rows.append(
                {
                    "h3_r7": r7,
                    "h3_r6": r6,
                    "h3_r5": r5,
                    "district_id": "BGD-ADM2-beta",
                    "year": np.int16(y),
                    "month": np.int8(m),
                    "harmonized": beta_cell_val,
                    "source_used": source_used,
                }
            )

    df_harmonized_cell = pd.DataFrame(harmonized_cell_rows).sort_values(
        ["district_id", "year", "month", "h3_r7"]
    )

    # 4. Climatology (baseline complete years 2001-2025)
    climatology_rows = []
    for rid, mult in [("BGD-ADM2-alpha", 1.0), ("BGD-ADM2-beta", 0.5), ("BGD", 1.5)]:
        for m in range(1, 13):
            # 25 years: 2020 has anomaly for m=5
            vals = []
            for y in range(2001, 2026):
                if y == 2020 and m == 5 and rid != "BGD-ADM2-beta":
                    val = 200.0 if rid == "BGD-ADM2-alpha" else 250.0
                else:
                    val = base_pattern[m - 1] * 10.0 * mult
                vals.append(val)
            arr = np.array(vals)
            climatology_rows.append(
                {
                    "region_id": rid,
                    "month": np.int8(m),
                    "n_years": np.int32(25),
                    "mean": float(np.mean(arr)),
                    "p50": float(np.percentile(arr, 50)),
                    "p90": float(np.percentile(arr, 90)),
                    "p95": float(np.percentile(arr, 95)),
                    "baseline_year_min": np.int16(2001),
                    "baseline_year_max": np.int16(2025),
                }
            )
    df_climatology = pd.DataFrame(climatology_rows).sort_values(["region_id", "month"])

    # 5. Anomalies
    anomalies_rows = []
    for rid, mult in [("BGD-ADM2-alpha", 1.0), ("BGD-ADM2-beta", 0.5), ("BGD", 1.5)]:
        for y, m in months_list:
            if y == 2020 and m == 5 and rid != "BGD-ADM2-beta":
                val = 200.0 if rid == "BGD-ADM2-alpha" else 250.0
                rank = 1.0
                cls_name = "extreme"
            else:
                val = base_pattern[m - 1] * 10.0 * mult
                rank = 0.5
                cls_name = "normal"

            anomalies_rows.append(
                {
                    "region_id": rid,
                    "year": np.int16(y),
                    "month": np.int8(m),
                    "value": float(val),
                    "percentile_rank": float(rank),
                    "class": cls_name,
                }
            )
    df_anomalies = pd.DataFrame(anomalies_rows).sort_values(["region_id", "year", "month"])

    # 6. Seasons
    seasons_rows = [
        {
            "region_id": "BGD-ADM2-alpha",
            "start_month": np.int8(4),
            "peak_month": np.int8(5),
            "end_month": np.int8(6),
            "share_of_annual": 24.0 / 34.0,
            "window_length": np.int32(3),
        },
        {
            "region_id": "BGD-ADM2-beta",
            "start_month": np.int8(4),
            "peak_month": np.int8(5),
            "end_month": np.int8(6),
            "share_of_annual": 24.0 / 34.0,
            "window_length": np.int32(3),
        },
        {
            "region_id": "BGD",
            "start_month": np.int8(4),
            "peak_month": np.int8(5),
            "end_month": np.int8(6),
            "share_of_annual": 24.0 / 34.0,
            "window_length": np.int32(3),
        },
    ]
    df_seasons = pd.DataFrame(seasons_rows).sort_values(["region_id"])

    # 7. Yearly stats (complete years 2001-2025)
    yearly_rows = []
    for rid, mult in [("BGD-ADM2-alpha", 1.0), ("BGD-ADM2-beta", 0.5), ("BGD", 1.5)]:
        normal_total = 340.0 * mult
        normal_frp = normal_total * 25.5
        for y in range(2001, 2026):
            if y == 2020 and rid != "BGD-ADM2-beta":
                total = (340.0 + 100.0) * mult
                frp = total * 25.5
                rank = 1
                vs_mean = (total / normal_total - 1.0) * 100.0
            else:
                total = normal_total
                frp = normal_frp
                rank = 2 if rid != "BGD-ADM2-beta" else 1
                vs_mean = 0.0

            yearly_rows.append(
                {
                    "region_id": rid,
                    "year": np.int16(y),
                    "harmonized_total": float(total),
                    "frp_sum": float(frp),
                    "rank": np.int32(rank),
                    "vs_mean_pct": float(vs_mean),
                    "peak_month": np.int8(5),
                }
            )
    df_yearly = pd.DataFrame(yearly_rows).sort_values(["region_id", "year"])

    # Write Parquet files with deterministic settings
    written_files = {}
    tables = {
        "regions.parquet": df_regions,
        "monthly_region.parquet": df_monthly_region,
        "harmonized_region.parquet": df_harmonized_region,
        "harmonized_cell.parquet": df_harmonized_cell,
        "climatology.parquet": df_climatology,
        "anomalies.parquet": df_anomalies,
        "seasons.parquet": df_seasons,
        "yearly.parquet": df_yearly,
    }

    for filename, df in tables.items():
        filepath = out / filename
        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_table(
            table,
            filepath,
            compression="ZSTD",
            version="2.6",
        )
        written_files[filename] = filepath

    # 8. Manifest
    manifest = DatasetManifest(
        data_version="v0.1.0-fixtures",
        git_commit="fixtures-deterministic",
        as_of_date="2025-12-31",
        parameters={"eps_spatial_meters": 2700.0, "eps_temporal_hours": 24.0},
        sources=[
            SourceManifest(
                file_name="synthetic_modis.csv",
                sensor="MODIS",
                row_count=len(df_monthly_region),
                sha256="deterministic-fixtures-sha256",
                date_range=["2000-11-01", "2025-12-31"],
            )
        ],
        counts=PipelineCounts(
            detections_raw=10000,
            detections_kept=10000,
            events_created=len(df_harmonized_region),
        ),
        unallocated_harmonized=0.0,
    )
    manifest_path = out / "manifest.json"
    manifest.write_json(manifest_path)
    written_files["manifest.json"] = manifest_path

    return written_files


if __name__ == "__main__":
    from pyroscope_pipeline.common.paths import FIXTURES_DIR

    files = generate_fixtures(FIXTURES_DIR)
    print(f"Generated {len(files)} fixture files in {FIXTURES_DIR}")
