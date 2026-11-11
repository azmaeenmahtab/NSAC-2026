"""Public interface for the PyroScope VIIRS-to-MODIS harmonization engine."""

from pyroscope_pipeline.harmonize.aggregate_up import aggregate_up_regions
from pyroscope_pipeline.harmonize.build import build_harmonization
from pyroscope_pipeline.harmonize.downscale import downscale_to_cells
from pyroscope_pipeline.harmonize.evaluate import (
    choose_method,
    cv_by_year,
    spearman_correlation,
)
from pyroscope_pipeline.harmonize.jump_metrics import (
    compute_country_cv_metrics,
    compute_jump_metrics,
    compute_qq_points,
)
from pyroscope_pipeline.harmonize.pooling import (
    circular_month_group,
    pool_month_mask,
    select_pooled_pair,
)
from pyroscope_pipeline.harmonize.quantile_map import apply_qm, fit_qm
from pyroscope_pipeline.harmonize.ratio import apply_ratio, fit_ratio
from pyroscope_pipeline.harmonize.types import CvMetrics, HarmonizeMethod, QmKnots
from pyroscope_pipeline.harmonize.units import (
    assign_calibration_units,
    build_unit_calibration_series,
    compute_district_mean_modis,
)

__all__ = [
    "CvMetrics",
    "HarmonizeMethod",
    "QmKnots",
    "aggregate_up_regions",
    "apply_qm",
    "apply_ratio",
    "assign_calibration_units",
    "build_harmonization",
    "build_unit_calibration_series",
    "choose_method",
    "circular_month_group",
    "compute_country_cv_metrics",
    "compute_district_mean_modis",
    "compute_jump_metrics",
    "compute_qq_points",
    "cv_by_year",
    "downscale_to_cells",
    "fit_qm",
    "fit_ratio",
    "pool_month_mask",
    "select_pooled_pair",
    "spearman_correlation",
]
