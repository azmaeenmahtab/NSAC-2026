"""Calendar statistics pure engines and processed dataset assembly (D07)."""

from pyroscope_pipeline.stats.anomalies import (
    ANOMALIES_COLUMNS,
    DEFAULT_MIN_BASELINE_YEARS,
    AnomalyClass,
    compute_anomalies,
    evaluate_month_anomaly,
)
from pyroscope_pipeline.stats.climatology import (
    CLIMATOLOGY_COLUMNS,
    compute_climatology,
    compute_month_climatology,
    determine_complete_years,
)
from pyroscope_pipeline.stats.seasons import (
    SEASONS_COLUMNS,
    compute_season_from_means,
    compute_seasons,
)
from pyroscope_pipeline.stats.yearly import (
    YEARLY_COLUMNS,
    aggregate_region_frp,
    compute_region_yearly_stats,
    compute_yearly,
)

__all__ = [
    "ANOMALIES_COLUMNS",
    "CLIMATOLOGY_COLUMNS",
    "DEFAULT_MIN_BASELINE_YEARS",
    "SEASONS_COLUMNS",
    "YEARLY_COLUMNS",
    "AnomalyClass",
    "aggregate_region_frp",
    "compute_anomalies",
    "compute_climatology",
    "compute_month_climatology",
    "compute_region_yearly_stats",
    "compute_season_from_means",
    "compute_seasons",
    "compute_yearly",
    "determine_complete_years",
    "evaluate_month_anomaly",
]
