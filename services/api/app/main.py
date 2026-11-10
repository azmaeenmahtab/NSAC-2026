"""FastAPI Application Factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import APIException, api_exception_handler
from app.core.logging import setup_api_logger

logger = setup_api_logger()


def create_app() -> FastAPI:
    app = FastAPI(
        title="PyroScope API",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler
    app.add_exception_handler(APIException, api_exception_handler)

    @app.get("/api/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "PyroScope API",
            "version": "0.1.0",
        }

    return app


app = create_app()
