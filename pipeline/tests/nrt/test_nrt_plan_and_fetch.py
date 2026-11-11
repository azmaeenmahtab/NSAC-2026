"""Unit tests for D08 NRT planning, mocked FIRMS fetching, and cross-sensor logic."""

from __future__ import annotations

from datetime import date

import httpx
import pandas as pd
import pytest

from pyroscope_pipeline.ingest.firms_api import TokenBucket
from pyroscope_pipeline.nrt.cross_sensor import (
    fit_cross_sensor_factor,
    unadjusted_provisional_label,
)
from pyroscope_pipeline.nrt.fetch import fetch_nrt_detections
from pyroscope_pipeline.nrt.plan import (
    FetchWindow,
    chunk_fetch_windows,
    plan_fetch_windows,
    plan_missing_days,
)


def test_plan_missing_days_nov1_to_nov4() -> None:
    """Given as_of_date=2026-11-01 and today=2026-11-04, plans Nov 2 to Nov 3."""
    days = plan_missing_days(as_of_date="2026-11-01", today_utc="2026-11-04")
    assert days == [date(2026, 11, 2), date(2026, 11, 3)]

    windows = plan_fetch_windows(as_of_date="2026-11-01", today_utc="2026-11-04")
    assert windows == [FetchWindow(start_date="2026-11-02", days=2, end_date="2026-11-03")]

    # Already up to date (yesterday already covered)
    assert plan_missing_days(as_of_date="2026-11-03", today_utc="2026-11-04") == []

    # Chunking > 5 days splits into multiple <=5-day windows
    many_days = plan_missing_days(as_of_date="2026-10-20", today_utc="2026-11-02")
    assert len(many_days) == 12
    chunked = chunk_fetch_windows(many_days, max_days_per_call=5)
    assert [(w.start_date, w.days, w.end_date) for w in chunked] == [
        ("2026-10-21", 5, "2026-10-25"),
        ("2026-10-26", 5, "2026-10-30"),
        ("2026-10-31", 2, "2026-11-01"),
    ]


def test_fetch_mocked_success_504_retry_and_empty_day(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mocked FIRMS responses: success, 504 then success, and empty day."""
    monkeypatch.setattr("time.sleep", lambda _sec: None)

    modis_csv = (
        "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight\n"
        "22.5,92.2,315.0,1.0,1.0,2026-11-02,0730,Terra,MODIS,85,6.1NRT,295.0,12.5,D\n"
    )
    noaa20_csv = (
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
        "22.501,92.201,325.0,0.4,0.4,2026-11-02,0732,N20,VIIRS,n,2.0NRT,292.0,4.2,D\n"
    )
    empty_header_csv = (
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
    )

    attempts: dict[str, int] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        attempts[url] = attempts.get(url, 0) + 1
        if "MODIS_NRT" in url:
            if attempts[url] == 1:
                return httpx.Response(504, text="Gateway Timeout")
            return httpx.Response(200, text=modis_csv)
        if "VIIRS_SNPP_NRT" in url:
            # S-NPP retired after Nov 1 -> empty response
            return httpx.Response(200, text=empty_header_csv)
        if "VIIRS_NOAA20_NRT" in url:
            return httpx.Response(200, text=noaa20_csv)
        return httpx.Response(200, text="")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    limiter = TokenBucket(capacity=1000.0, refill_time_sec=60.0)
    windows = [FetchWindow(start_date="2026-11-02", days=2, end_date="2026-11-03")]

    res = fetch_nrt_detections(
        windows=windows,
        bbox=[88.0, 20.5, 92.8, 26.7],
        map_key="SECRET_TEST_KEY",
        client=client,
        limiter=limiter,
    )
    assert len(res.modis_raw) == 1
    assert len(res.viirs_raw) == 1
    assert res.viirs_source_used == "VIIRS_NOAA20_NRT"
    assert res.snpp_available is False

    # Empty day across all feeds returns empty DataFrames cleanly without raising
    empty_client = httpx.Client(transport=httpx.MockTransport(lambda _req: httpx.Response(200, text="")))
    empty_res = fetch_nrt_detections(
        windows=windows,
        bbox=[88.0, 20.5, 92.8, 26.7],
        map_key="SECRET_TEST_KEY",
        client=empty_client,
        limiter=limiter,
    )
    assert empty_res.modis_raw.empty
    assert empty_res.viirs_raw.empty


def test_cross_sensor_factor_requires_2_years_or_unadjusted_label() -> None:
    """Fits S-NPP/NOAA-20 ratio with >=24 shared months; returns None (<24) with unadjusted label."""
    assert unadjusted_provisional_label("VIIRS_NOAA20_NRT") == "provisional, unadjusted NOAA-20"
    assert unadjusted_provisional_label("VIIRS_SNPP_NRT") is None

    rows_s: list[dict[str, object]] = []
    rows_n: list[dict[str, object]] = []
    for y in (2023, 2024):
        for m in range(1, 13):
            rows_s.append({"region_id": "DIST-1", "year": y, "month": m, "event_count": 10.0})
            rows_n.append({"region_id": "DIST-1", "year": y, "month": m, "event_count": 20.0})

    df_s = pd.DataFrame(rows_s)
    df_n = pd.DataFrame(rows_n)

    # Fewer than 24 shared months -> None
    assert (
        fit_cross_sensor_factor(
            df_s[df_s["year"] == 2023],
            df_n[df_n["year"] == 2023],
            district_ids=["DIST-1"],
            district_to_division={"DIST-1": "DIV-1"},
        )
        is None
    )

    model = fit_cross_sensor_factor(
        df_s,
        df_n,
        district_ids=["DIST-1"],
        district_to_division={"DIST-1": "DIV-1"},
    )
    assert model is not None
    assert model.n_shared_months == 24
    assert model.unit_month_ratios[("DIST-1", 3)] == pytest.approx(0.5, abs=1e-9)
    assert model.cv_rmse == pytest.approx(0.0, abs=1e-9)
