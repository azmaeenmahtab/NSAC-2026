"""Pure NRT calibration applicator using stored transfer functions (no refit).

Pure scientific functions: no disk, network, or clock access.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from pyroscope_pipeline.harmonize.quantile_map import apply_qm
from pyroscope_pipeline.harmonize.ratio import apply_ratio
from pyroscope_pipeline.harmonize.types import QmKnots
from pyroscope_pipeline.nrt.cross_sensor import CrossSensorModel


def load_stored_models(
    cal_report_df: pd.DataFrame,
) -> dict[str, tuple[str, dict[int, QmKnots | float]]]:
    """Deserialize stored monthly QM knots / ratios from `calibration_report.parquet`."""
    models: dict[str, tuple[str, dict[int, QmKnots | float]]] = {}
    for _, row in cal_report_df.iterrows():
        uid = str(row["calibration_unit_id"])
        method = str(row["method_chosen"])
        raw_knots = json.loads(str(row["knots_json"]))
        per_month: dict[int, QmKnots | float] = {}
        for m_str, payload in raw_knots.items():
            m_int = int(m_str)
            if method == "quantile_map":
                per_month[m_int] = QmKnots(
                    knots_v=np.asarray(payload["knots_v"], dtype=np.float64),
                    knots_m=np.asarray(payload["knots_m"], dtype=np.float64),
                )
            else:
                per_month[m_int] = float(payload["ratio"])
        models[uid] = (method, per_month)
    return models


def harmonize_affected_districts(
    monthly_region_sub: pd.DataFrame,
    district_ids: list[str],
    district_to_unit: dict[str, str],
    stored_models: dict[str, tuple[str, dict[int, QmKnots | float]]],
    affected_months: set[tuple[int, int]],
    cross_sensor_model: CrossSensorModel | None = None,
) -> pd.DataFrame:
    """Apply stored VIIRS->MODIS transfer functions for `affected_months` (no refitting)."""
    piv = monthly_region_sub.pivot(
        index=["region_id", "year", "month"],
        columns="sensor_family",
        values="event_count",
    ).reset_index()
    for col in ("MODIS", "VIIRS"):
        if col not in piv.columns:
            piv[col] = 0.0
    piv["MODIS"] = piv["MODIS"].fillna(0.0).astype(float)
    piv["VIIRS"] = piv["VIIRS"].fillna(0.0).astype(float)

    rows: list[dict[str, object]] = []
    for dist in sorted(district_ids):
        unit_id = district_to_unit.get(dist, dist)
        method, per_month = stored_models[unit_id]
        sub = piv[piv["region_id"] == dist]
        by_ym = {
            (int(r["year"]), int(r["month"])): (float(r["MODIS"]), float(r["VIIRS"]))
            for _, r in sub.iterrows()
        }
        for y, m in sorted(affected_months):
            raw_m, raw_v = by_ym.get((y, m), (0.0, 0.0))
            scaled_v = (
                raw_v * cross_sensor_model.unit_month_ratios.get((unit_id, m), 1.0)
                if cross_sensor_model
                else raw_v
            )
            model = per_month[m]
            if method == "quantile_map" and isinstance(model, QmKnots):
                harm_val = apply_qm(model, scaled_v)
            else:
                harm_val = apply_ratio(float(model), scaled_v)  # type: ignore[arg-type]
            rows.append(
                {
                    "region_id": dist,
                    "year": np.int16(y),
                    "month": np.int8(m),
                    "raw_modis": raw_m,
                    "raw_viirs": raw_v,
                    "harmonized": float(harm_val),
                    "source_used": "viirs_calibrated",
                    "method": method,
                    "calibration_unit_id": unit_id,
                    "in_overlap": (y * 100 + m) >= 201202,
                }
            )
    return pd.DataFrame(rows)
