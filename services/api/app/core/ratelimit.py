"""Rate limiting configuration and middleware using slowapi + per-IP sliding window."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import build_error_response

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


def _parse_rate_limit(spec: str) -> tuple[int, float]:
    """Parse a rate limit string like `'120/minute'` or `'5/hour'` into `(count, window_sec)`."""
    parts = spec.strip().lower().split("/")
    if len(parts) != 2:
        return (120, 60.0)
    count = int(parts[0])
    unit = parts[1]
    window_map = {
        "second": 1.0,
        "sec": 1.0,
        "minute": 60.0,
        "min": 60.0,
        "hour": 3600.0,
        "hr": 3600.0,
    }
    return (count, window_map.get(unit, 60.0))


class SlidingWindowRateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-IP rate limits (120/min default, 10/min `/api/ask`, 5/hr `/api/alerts/subscriptions`)."""

    def __init__(self, app: object, default_limit: str = "120/minute") -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.default_max, self.default_window = _parse_rate_limit(default_limit)
        self._buckets: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def reset(self) -> None:
        """Clear all rate-limit buckets (used between test cases)."""
        self._buckets.clear()

    def _rule_for_path(self, path: str) -> tuple[str, int, float]:
        if path.startswith("/api/ask"):
            return ("ask", 10, 60.0)
        if path.startswith("/api/alerts/subscriptions") and not path.endswith("/confirm"):
            return ("alerts_sub", 5, 3600.0)
        return ("default", self.default_max, self.default_window)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        client_ip = request.client.host if request.client else "127.0.0.1"
        bucket_name, max_requests, window_sec = self._rule_for_path(request.url.path)
        key = (client_ip, bucket_name)

        now = time.monotonic()
        dq = self._buckets[key]
        cutoff = now - window_sec
        while dq and dq[0] <= cutoff:
            dq.popleft()

        if len(dq) >= max_requests:
            retry_after = max(1, int(window_sec - (now - dq[0])))
            return build_error_response(
                request=request,
                code="RATE_LIMITED",
                message=f"Rate limit exceeded ({max_requests} requests per {int(window_sec)}s)",
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )

        dq.append(now)
        return await call_next(request)


async def rate_limit_exception_handler(request: Request, exc: Exception) -> Response:
    """Render `slowapi.errors.RateLimitExceeded` into the standard 429 `ErrorEnvelope`."""
    detail = getattr(exc, "detail", "Rate limit exceeded") if isinstance(exc, RateLimitExceeded) else str(exc)
    return build_error_response(
        request=request,
        code="RATE_LIMITED",
        message=f"Rate limit exceeded: {detail}",
        status_code=429,
        headers={"Retry-After": "60"},
    )
