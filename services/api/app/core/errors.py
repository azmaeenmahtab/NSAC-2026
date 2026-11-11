"""Standardized error responses, exceptions, and FastAPI exception handlers."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class ErrorDetail(BaseModel):
    """Structured error body matching `contracts/openapi.yaml`."""

    code: str = Field(..., examples=["VALIDATION_ERROR"])
    message: str = Field(..., examples=["Invalid area identifier"])
    requestId: str = Field(..., examples=["req-12345"])


class ErrorEnvelope(BaseModel):
    """Top-level `{ error: { code, message, requestId } }` error envelope."""

    error: ErrorDetail


class APIException(Exception):
    """Base application exception rendered into `ErrorEnvelope`."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.headers = headers or {}


class ValidationAPIError(APIException):
    """400 Bad Request / Validation error."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR") -> None:
        super().__init__(code=code, message=message, status_code=400)


class NotFoundAPIError(APIException):
    """404 Not Found error."""

    def __init__(self, message: str, code: str = "NOT_FOUND") -> None:
        super().__init__(code=code, message=message, status_code=404)


class RateLimitAPIError(APIException):
    """429 Too Many Requests error with Retry-After header."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
    ) -> None:
        super().__init__(
            code="RATE_LIMITED",
            message=message,
            status_code=429,
            headers={"Retry-After": str(retry_after)},
        )


class UpstreamAPIError(APIException):
    """502 Bad Gateway / upstream provider error."""

    def __init__(self, message: str = "Upstream service unavailable") -> None:
        super().__init__(code="UPSTREAM_ERROR", message=message, status_code=502)


def get_request_id(request: Request) -> str:
    """Resolve the active request ID from `request.state` or header."""
    state_id = getattr(request.state, "request_id", None)
    if isinstance(state_id, str) and state_id:
        return state_id
    header_id = request.headers.get("x-request-id")
    if header_id:
        return header_id
    return f"req-{uuid.uuid4().hex[:12]}"


def build_error_response(
    request: Request,
    code: str,
    message: str,
    status_code: int,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build a JSONResponse conforming to `ErrorEnvelope`."""
    request_id = get_request_id(request)
    merged_headers = dict(headers or {})
    merged_headers.setdefault("X-Request-ID", request_id)
    return JSONResponse(
        status_code=status_code,
        headers=merged_headers,
        content={
            "error": {
                "code": code,
                "message": message,
                "requestId": request_id,
            }
        },
    )


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a deterministic or generated `X-Request-ID` to every request and response."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        req_id = request.headers.get("x-request-id") or f"req-{uuid.uuid4().hex[:12]}"
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers.setdefault("X-Request-ID", req_id)
        return response


async def api_exception_handler(request: Request, exc: Exception) -> Response:
    """Handle `APIException` and fallback 500 internal errors."""
    if isinstance(exc, APIException):
        return build_error_response(
            request=request,
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            headers=exc.headers,
        )
    return build_error_response(
        request=request,
        code="INTERNAL_ERROR",
        message="Internal server error",
        status_code=500,
    )


async def validation_exception_handler(request: Request, exc: Exception) -> Response:
    """Convert FastAPI `RequestValidationError` (422) into 400 `ErrorEnvelope`."""
    if isinstance(exc, RequestValidationError):
        errors = exc.errors()
        if errors:
            first = errors[0]
            loc = ".".join(str(part) for part in first.get("loc", []) if part != "query")
            msg = first.get("msg", "Invalid request parameters")
            detail = f"{loc}: {msg}" if loc else msg
        else:
            detail = "Invalid request parameters"
    else:
        detail = str(exc)
    return build_error_response(
        request=request,
        code="VALIDATION_ERROR",
        message=detail,
        status_code=400,
    )


async def http_exception_handler(request: Request, exc: Exception) -> Response:
    """Convert Starlette/FastAPI HTTPExceptions into `ErrorEnvelope`."""
    if isinstance(exc, StarletteHTTPException):
        status = exc.status_code
        code_map = {
            400: "VALIDATION_ERROR",
            404: "NOT_FOUND",
            429: "RATE_LIMITED",
            502: "UPSTREAM_ERROR",
        }
        code = code_map.get(status, f"HTTP_{status}")
        return build_error_response(
            request=request,
            code=code,
            message=str(exc.detail),
            status_code=status,
        )
    return await api_exception_handler(request, exc)
