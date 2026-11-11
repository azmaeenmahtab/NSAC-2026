"""Service logic and fixed limitations for `/api/methodology`."""

from __future__ import annotations

from collections import OrderedDict

import duckdb

from app.core.dataset import LoadedDataset
from app.core.responses import ResponseMeta
from app.features.meta.service import _filter_safe_parameters
from app.features.methodology.repository import (
    compute_jump_metrics,
    fetch_calibration_summary,
    fetch_qq_data,
)
from app.features.methodology.schemas import (
    MethodologyData,
    MethodologyEnvelope,
)

_MAX_CACHE_ENTRIES = 16
_METHODOLOGY_CACHE: OrderedDict[str, MethodologyEnvelope] = OrderedDict()

METHODOLOGY_LIMITATIONS: list[str] = [
    "Active-fire counts are not burned area. Harmonized counts are 'MODIS-equivalent fire events', not hectares.",
    "The calibration assumes the MODIS-VIIRS relationship observed in 2012-present also holds before 2012 (it cannot be tested there).",
    "MODIS is itself not homogeneous: Aqua joined Terra in mid-2002, and Terra/Aqua orbits have drifted. We report this as a limitation and test sensitivity if time allows.",
    "Cloud, smoke and underground fires are under-detected by both sensors.",
    "Harmonization quality is measured by agreement over the overlap period (leave-one-year-out CV), not by the absence of change; real trends can remain.",
    "Alerts and guidance are advisory, not an official warning system.",
]


def clear_methodology_cache() -> None:
    """Clear methodology in-process cache."""
    _METHODOLOGY_CACHE.clear()


def get_methodology_envelope(
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
) -> MethodologyEnvelope:
    """Build methodology envelope containing parameters, jump metrics, and limitations."""
    cache_key = dataset.data_version
    if cache_key in _METHODOLOGY_CACHE:
        _METHODOLOGY_CACHE.move_to_end(cache_key)
        return _METHODOLOGY_CACHE[cache_key]

    params = _filter_safe_parameters(dataset.manifest.get("parameters", {}))
    jump_metrics = compute_jump_metrics(cursor, region_id="BGD")
    cal_summary = fetch_calibration_summary(cursor, dataset.registered_views)
    qq_data = fetch_qq_data(cursor, region_id="BGD")

    envelope = MethodologyEnvelope(
        data=MethodologyData(
            parameters=params,
            calibration_summary=cal_summary,
            jump_metrics=jump_metrics,
            qq_data=qq_data,
            limitations=list(METHODOLOGY_LIMITATIONS),
        ),
        meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
    )

    _METHODOLOGY_CACHE[cache_key] = envelope
    if len(_METHODOLOGY_CACHE) > _MAX_CACHE_ENTRIES:
        _METHODOLOGY_CACHE.popitem(last=False)

    return envelope
