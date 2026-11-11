"""Public interface for the PyroScope VIIRS-to-MODIS harmonization engine."""

from pyroscope_pipeline.harmonize.evaluate import (
    choose_method,
    cv_by_year,
    spearman_correlation,
)
from pyroscope_pipeline.harmonize.pooling import (
    circular_month_group,
    pool_month_mask,
    select_pooled_pair,
)
from pyroscope_pipeline.harmonize.quantile_map import apply_qm, fit_qm
from pyroscope_pipeline.harmonize.ratio import apply_ratio, fit_ratio
from pyroscope_pipeline.harmonize.types import CvMetrics, HarmonizeMethod, QmKnots

__all__ = [
    "CvMetrics",
    "HarmonizeMethod",
    "QmKnots",
    "apply_qm",
    "apply_ratio",
    "choose_method",
    "circular_month_group",
    "cv_by_year",
    "fit_qm",
    "fit_ratio",
    "pool_month_mask",
    "select_pooled_pair",
    "spearman_correlation",
]
