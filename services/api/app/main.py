"""FastAPI Application Factory for PyroScope API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings, settings
from app.core.dataset import load_dataset
from app.core.errors import (
    APIException,
    RequestIdMiddleware,
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
from app.features.alerts import router as alerts_router
from app.features.areas import router as areas_router
from app.features.ask import router as ask_router
from app.features.calendar import router as calendar_router
from app.features.guidance import guidance_router
from app.features.heatmap import router as heatmap_router
from app.features.meta import router as meta_router
from app.features.methodology import router as methodology_router
from app.features.series import router as series_router
from app.features.stats import router as stats_router

logger = setup_api_logger()


def create_app(app_settings: Settings | None = None) -> FastAPI:
    """Create and configure the PyroScope FastAPI application.

    Router registration pattern (Sync Rule 5):
        Each API feature registers its router with a single `app.include_router(...)`
        line in the "Feature routers" section below.
    """
    cfg = app_settings or settings

    @asynccontextmanager
    async def lifespan(app_instance: FastAPI) -> AsyncIterator[None]:
        dataset = load_dataset(cfg.data_dir, reference_dir=cfg.reference_dir)
        app_instance.state.dataset = dataset
        logger.info(
            "Loaded dataset %s (as_of=%s) from %s",
            dataset.data_version,
            dataset.as_of,
            dataset.data_dir,
        )
        try:
            yield
        finally:
            dataset.connection.close()

    app_instance = FastAPI(
        title="PyroScope API Contract",
        version="0.1.0",
        description="API specifications for PyroScope NASA MODIS & VIIRS fire harmonization platform.",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Eagerly load dataset so both lifespan and direct TestClient(app) usage work seamlessly
    app_instance.state.dataset = load_dataset(cfg.data_dir, reference_dir=cfg.reference_dir)
    app_instance.state.settings = cfg
    app_instance.state.limiter = limiter

    # Middleware: CORS restricted strictly to WEB_ORIGIN, Request-ID, and per-IP Rate Limiting
    app_instance.add_middleware(
         SlidingWindowRateLimitMiddleware,
        default_limit=cfg.rate_limit_default,
    )
    app_instance.add_middleware(RequestIdMiddleware)
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=[cfg.web_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Exception handlers (400 validation, 404 not found, 429 rate limit, 502 upstream, 500 internal)
    app_instance.add_exception_handler(APIException, api_exception_handler)
    app_instance.add_exception_handler(RequestValidationError, validation_exception_handler)
    app_instance.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app_instance.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
    app_instance.add_exception_handler(Exception, api_exception_handler)

    # --- Feature routers (one line per feature chunk) ---
    app_instance.include_router(meta_router)
    app_instance.include_router(areas_router)
    app_instance.include_router(heatmap_router)
    app_instance.include_router(series_router)
    app_instance.include_router(calendar_router)
    app_instance.include_router(stats_router)
    app_instance.include_router(methodology_router)
    app_instance.include_router(ask_router)
    app_instance.include_router(guidance_router)
    app_instance.include_router(alerts_router)

    return app_instance


app = create_app()
