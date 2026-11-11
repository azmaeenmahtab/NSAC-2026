"""Public exports for `services/api/app/core`."""

from app.core.config import Settings, settings
from app.core.dataset import DatasetLoadError, LoadedDataset, load_dataset
from app.core.db import get_dataset, get_db_cursor
from app.core.errors import (
    APIException,
    ErrorDetail,
    ErrorEnvelope,
    NotFoundAPIError,
    RateLimitAPIError,
    RequestIdMiddleware,
    UpstreamAPIError,
    ValidationAPIError,
    api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_api_logger
from app.core.ratelimit import (
    SlidingWindowRateLimitMiddleware,
    limiter,
    rate_limit_exception_handler,
)
from app.core.responses import ApiEnvelope, ResponseMeta, wrap_envelope

__all__ = [
    "APIException",
    "ApiEnvelope",
    "DatasetLoadError",
    "ErrorDetail",
    "ErrorEnvelope",
    "LoadedDataset",
    "NotFoundAPIError",
    "RateLimitAPIError",
    "RequestIdMiddleware",
    "ResponseMeta",
    "Settings",
    "SlidingWindowRateLimitMiddleware",
    "UpstreamAPIError",
    "ValidationAPIError",
    "api_exception_handler",
    "get_dataset",
    "get_db_cursor",
    "http_exception_handler",
    "limiter",
    "load_dataset",
    "rate_limit_exception_handler",
    "settings",
    "setup_api_logger",
    "validation_exception_handler",
    "wrap_envelope",
]
