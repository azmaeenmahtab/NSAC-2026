import httpx
import pytest

from pyroscope_pipeline.ingest.firms_api import TokenBucket, fetch_area, redact_map_key


def test_token_bucket_rate_limiter() -> None:
    bucket = TokenBucket(capacity=5.0, refill_time_sec=1.0)
    assert bucket.consume(3.0) is True
    assert bucket.consume(2.0) is True
    assert bucket.consume(1.0) is False  # exhausted


def test_redact_map_key() -> None:
    url = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/SECRET_KEY_123/MODIS"
    redacted = redact_map_key(url, "SECRET_KEY_123")
    assert "SECRET_KEY_123" not in redacted
    assert "[REDACTED_MAP_KEY]" in redacted


def test_fetch_area_mocked_http() -> None:
    csv_payload = (
        "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight\n"
        "23.5,90.2,310.5,1.0,1.0,2026-10-01,1330,Terra,MODIS,75,6.1,295.0,15.2,D\n"
    )

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=csv_payload)

    client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    limiter = TokenBucket(capacity=100.0, refill_time_sec=1.0)

    df = fetch_area(
        source="MODIS_SP",
        bbox=[88.0, 20.5, 92.8, 26.7],
        start_date="2026-10-01",
        days=1,
        map_key="test_key",
        client=client,
        limiter=limiter,
    )

    assert len(df) == 1
    assert df["latitude"].iloc[0] == 23.5
    assert df["confidence"].iloc[0] == 75


def test_fetch_area_invalid_map_key_raises() -> None:
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="Invalid MAP_KEY")

    client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    limiter = TokenBucket(capacity=100.0, refill_time_sec=1.0)

    with pytest.raises(ValueError, match="Invalid MAP_KEY"):
        fetch_area(
            source="MODIS_SP",
            bbox=[88.0, 20.5, 92.8, 26.7],
            start_date="2026-10-01",
            days=1,
            map_key="bad_key",
            client=client,
            limiter=limiter,
        )
