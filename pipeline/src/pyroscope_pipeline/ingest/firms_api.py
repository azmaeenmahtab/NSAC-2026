"""FIRMS Area API client with token bucket rate limiter and retry backoff."""

import io
import time

import httpx
import pandas as pd

from pyroscope_pipeline.common.logging import get_logger

logger = get_logger("firms_api")


class TokenBucket:
    """Thread-safe rate limiter (max 3,000 transactions per 10 minutes = 5 req/sec)."""

    def __init__(self, capacity: float = 3000.0, refill_time_sec: float = 600.0) -> None:
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = capacity / refill_time_sec  # 5.0 tokens/sec
        self.last_update = time.monotonic()

    def consume(self, amount: float = 1.0) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_update
        self.last_update = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False

    def wait_and_consume(self, amount: float = 1.0) -> None:
        while not self.consume(amount):
            time.sleep(0.1)


# Global rate limiter instance
_DEFAULT_LIMITER = TokenBucket(capacity=3000.0, refill_time_sec=600.0)


def redact_map_key(url: str, map_key: str) -> str:
    """Redact secret map_key from logs and error strings."""
    if map_key and map_key in url:
        return url.replace(map_key, "[REDACTED_MAP_KEY]")
    return url


def fetch_area(
    source: str,
    bbox: list[float],
    start_date: str,
    days: int,
    map_key: str,
    client: httpx.Client | None = None,
    limiter: TokenBucket | None = None,
    max_retries: int = 4,
) -> pd.DataFrame:
    """Fetch active-fire CSV from NASA FIRMS Area API.

    API format:
    https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{west,south,east,north}/{DAY_RANGE}/{DATE}
    """
    if not map_key:
        raise ValueError("FIRMS MAP_KEY must not be empty")

    if days < 1 or days > 10:
        raise ValueError(f"FIRMS API days parameter must be between 1 and 10, got {days}")

    west, south, east, north = bbox
    bbox_str = f"{west},{south},{east},{north}"
    base_url = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
    endpoint = f"{base_url}/{map_key}/{source}/{bbox_str}/{days}/{start_date}"

    log_url = redact_map_key(endpoint, map_key)
    rate_limiter = limiter or _DEFAULT_LIMITER

    should_close_client = False
    if client is None:
        client = httpx.Client(timeout=30.0)
        should_close_client = True

    try:
        delay = 1.0
        for attempt in range(max_retries):
            rate_limiter.wait_and_consume(1.0)
            logger.info(f"FIRMS API request (attempt {attempt + 1}/{max_retries}): {log_url}")

            try:
                response = client.get(endpoint)
                if response.status_code == 200:
                    text_content = response.text
                    if "Invalid MAP_KEY" in text_content:
                        raise ValueError("NASA FIRMS returned 'Invalid MAP_KEY'")
                    if not text_content.strip():
                        return pd.DataFrame()
                    return pd.read_csv(io.StringIO(text_content))

                if response.status_code in (429, 500, 502, 503, 504):
                    logger.warning(
                        f"Server error {response.status_code} on {log_url}. Backoff {delay:.1f}s"
                    )
                    time.sleep(delay)
                    delay *= 2.0
                    continue

                response.raise_for_status()

            except (httpx.RequestError, httpx.HTTPStatusError):
                if attempt == max_retries - 1:
                    raise
                time.sleep(delay)
                delay *= 2.0

        raise httpx.RequestError(f"Failed to fetch {log_url} after {max_retries} retries")

    finally:
        if should_close_client:
            client.close()
