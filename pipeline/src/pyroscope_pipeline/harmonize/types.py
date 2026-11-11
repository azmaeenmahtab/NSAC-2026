"""Pure data types for the PyroScope VIIRS-to-MODIS harmonization engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

HarmonizeMethod = Literal["quantile_map", "ratio"]


@dataclass(frozen=True)
class QmKnots:
    """Piecewise-linear empirical quantile-mapping knots.

    Attributes:
        knots_v: Strictly increasing 1D float64 array of sorted unique VIIRS values.
        knots_m: Non-decreasing 1D float64 array of corresponding averaged MODIS values.
    """

    knots_v: NDArray[np.float64]
    knots_m: NDArray[np.float64]

    def to_dict(self) -> dict[str, list[float]]:
        """Serialize knots into JSON-compatible lists of floats."""
        return {
            "knots_v": [float(v) for v in self.knots_v],
            "knots_m": [float(m) for m in self.knots_m],
        }


@dataclass(frozen=True)
class CvMetrics:
    """Leave-one-year-out cross-validation metrics over the overlap window.

    All error metrics are in units of monthly MODIS-equivalent fire events,
    except ``spearman_rho`` (unitless rank correlation in [-1, 1]) and
    ``annual_total_rel_error`` (unitless mean absolute relative error of annual totals).
    """

    method: HarmonizeMethod
    rmse: float
    mae: float
    bias: float
    spearman_rho: float
    annual_total_rel_error: float
    n_months: int
    n_years: int
    predictions: NDArray[np.float64]
