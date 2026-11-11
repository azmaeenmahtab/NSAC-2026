"""Service logic for `/api/health` and `/api/meta`."""

from __future__ import annotations

from typing import Any

from app.core.dataset import LoadedDataset
from app.core.responses import ResponseMeta
from app.features.meta.schemas import HealthResponse, MetaData, MetaEnvelope

DEFAULT_ATTRIBUTION = (
    "We acknowledge the use of data and/or imagery from NASA's Fire Information for "
    "Resource Management System (FIRMS) (https://firms.modaps.eosdis.nasa.gov), part of "
    "NASA's Earth Observing System Data and Information System (EOSDIS). Administrative "
    "boundaries from geoBoundaries v6.0.0 (Bangladesh Bureau of Statistics & UN OCHA ROAP, "
    "CC BY 3.0 IGO / CC0 1.0)."
)

_SAFE_PARAMETER_KEYS = {
    "eps_spatial_meters",
    "eps_temporal_hours",
    "min_pts",
    "min_mean_monthly_modis",
    "month_pool_width",
    "cv_method",
    "methods",
    "percentiles",
    "season_share_threshold",
    "h3_resolutions",
    "bbox_bangladesh",
    "sources",
    "clustering",
    "spatial",
    "harmonization",
}


def _filter_safe_parameters(raw_params: Any) -> dict[str, Any]:
    if not isinstance(raw_params, dict):
        return {}
    safe: dict[str, Any] = {}
    for key, val in raw_params.items():
        key_str = str(key)
        if key_str in _SAFE_PARAMETER_KEYS or not any(
            secret in key_str.lower() for secret in ("key", "token", "secret", "password", "smtp")
        ):
            safe[key_str] = val
    return safe


def build_health_response(dataset: LoadedDataset) -> HealthResponse:
    """Construct the `/api/health` response from the active dataset."""
    return HealthResponse(
        status="healthy",
        service="PyroScope API",
        version="0.1.0",
        dataLoaded=len(dataset.registered_views) > 0,
        dataVersion=dataset.data_version,
    )


def build_meta_envelope(dataset: LoadedDataset) -> MetaEnvelope:
    """Construct the `/api/meta` envelope from the loaded `manifest.json`."""
    manifest = dataset.manifest
    raw_sources = manifest.get("sources")
    sources: list[dict[str, Any]] = []
    if isinstance(raw_sources, list):
        for item in raw_sources:
            if isinstance(item, dict):
                sources.append(dict(item))

    raw_counts = manifest.get("counts")
    counts: dict[str, Any] = dict(raw_counts) if isinstance(raw_counts, dict) else {}

    data = MetaData(
        dataVersion=dataset.data_version,
        asOf=dataset.as_of,
        provisionalFrom=dataset.provisional_from,
        parametersSummary=_filter_safe_parameters(manifest.get("parameters")),
        sources=sources,
        counts=counts,
        attribution=DEFAULT_ATTRIBUTION,
    )
    return MetaEnvelope(
        data=data,
        meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
    )

