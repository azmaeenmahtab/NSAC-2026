"""Standardized error responses and exceptions."""

from fastapi import Request, Response
from fastapi.responses import JSONResponse


class APIException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


async def api_exception_handler(request: Request, exc: Exception) -> Response:
    request_id = request.headers.get("x-request-id", "unknown")
    if isinstance(exc, APIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "requestId": request_id,
                }
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL",
                "message": "Internal server error",
                "requestId": request_id,
            }
        },
    )
