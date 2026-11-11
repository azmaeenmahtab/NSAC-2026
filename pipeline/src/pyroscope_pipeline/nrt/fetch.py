"""NRT FIRMS fetcher with S-NPP -> NOAA-20/NOAA-21 fallback and rate limiting."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

import httpx
import pandas as pd

from pyroscope_pipeline.common.logging import get_logger
from pyroscope_pipeline.ingest.firms_api import TokenBucket, fetch_area, redact_map_key
from pyroscope_pipeline.nrt.plan import FetchWindow, chunk_fetch_windows, parse_iso_date

logger = get_logger("nrt.fetch")

MODIS_NRT_SOURCE = "MODIS_NRT"
VIIRS_NRT_FALLBACK_CHAIN: tuple[str, ...] = (
    "VIIRS_SNPP_NRT",
    "VIIRS_NOAA20_NRT",
    "VIIRS_NOAA21_NRT",
)


@dataclass(frozen=True)
class NrtFetchResult:
    """Combined MODIS and VIIRS NRT fetch payload with provenance metadata."""

    modis_raw: pd.DataFrame
    viirs_raw: pd.DataFrame
    viirs_source_used: str
    snpp_available: bool
    windows_fetched: tuple[FetchWindow, ...]
    requests_made: int
    errors: tuple[str, ...]


def fetch_source_windows(
    source: str,
    windows: Sequence[FetchWindow],
    bbox: list[float],
    map_key: str,
    client: httpx.Client | None = None,
    limiter: TokenBucket | None = None,
    max_retries: int = 4,
) -> tuple[pd.DataFrame, bool, int, list[str]]:
    """Fetch all planned `windows` for one FIRMS NRT `source`."""
    if not windows:
        return pd.DataFrame(), True, 0, []

    frames: list[pd.DataFrame] = []
    requests_made = 0
    errors: list[str] = []

    for win in windows:
        requests_made += 1
        try:
            df = fetch_area(
                source=source,
                bbox=bbox,
                start_date=win.start_date,
                days=win.days,
                map_key=map_key,
                client=client,
                limiter=limiter,
                max_retries=max_retries,
            )
            if not df.empty:
                frames.append(df)
        except ValueError as exc:
            if "Invalid MAP_KEY" in str(exc) or "MAP_KEY must not be empty" in str(exc):
                raise
            errors.append(redact_map_key(f"{source} {win.start_date}+{win.days}: {exc}", map_key))
            return pd.DataFrame(), False, requests_made, errors
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            errors.append(redact_map_key(f"{source} {win.start_date}+{win.days}: {exc}", map_key))
            return pd.DataFrame(), False, requests_made, errors

    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return combined, True, requests_made, errors


def _windows_after_date(windows: Sequence[FetchWindow], cutoff_str: str) -> list[FetchWindow]:
    cutoff = parse_iso_date(cutoff_str)
    remaining_days: list[date] = []
    for w in windows:
        start_d = parse_iso_date(w.start_date)
        for offset in range(w.days):
            d = start_d + timedelta(days=offset)
            if d > cutoff:
                remaining_days.append(d)
    return chunk_fetch_windows(remaining_days, max_days_per_call=5)


def fetch_nrt_detections(
    windows: Sequence[FetchWindow],
    bbox: list[float],
    map_key: str,
    client: httpx.Client | None = None,
    limiter: TokenBucket | None = None,
    max_retries: int = 4,
    viirs_sources: Sequence[str] = VIIRS_NRT_FALLBACK_CHAIN,
    snpp_retirement_date: date = date(2026, 11, 1),
) -> NrtFetchResult:
    """Fetch MODIS NRT and VIIRS NRT detections across planned date windows.

    Tries `VIIRS_SNPP_NRT` first; if S-NPP fails, returns empty, or ceases mid-range
    (on/before `snpp_retirement_date` while later dates are requested), seamlessly
    fetches remaining dates from `VIIRS_NOAA20_NRT` / `VIIRS_NOAA21_NRT`.
    """
    if not windows:
        return NrtFetchResult(
            modis_raw=pd.DataFrame(),
            viirs_raw=pd.DataFrame(),
            viirs_source_used="none",
            snpp_available=False,
            windows_fetched=(),
            requests_made=0,
            errors=(),
        )

    all_errors: list[str] = []
    modis_df, modis_ok, req_m, errs_m = fetch_source_windows(
        source=MODIS_NRT_SOURCE,
        windows=windows,
        bbox=bbox,
        map_key=map_key,
        client=client,
        limiter=limiter,
        max_retries=max_retries,
    )
    all_errors.extend(errs_m)
    if not modis_ok:
        logger.warning(f"MODIS_NRT fetch failed: {errs_m}")

    total_requests = req_m
    viirs_parts: list[pd.DataFrame] = []
    used_sources: list[str] = []
    snpp_available = False
    active_windows: Sequence[FetchWindow] = windows
    post_cutoff_filter: str | None = None

    for candidate in viirs_sources:
        df_v, ok_v, req_v, errs_v = fetch_source_windows(
            source=candidate,
            windows=active_windows,
            bbox=bbox,
            map_key=map_key,
            client=client,
            limiter=limiter,
            max_retries=max_retries,
        )
        total_requests += req_v
        all_errors.extend(errs_v)

        if not ok_v:
            continue

        if post_cutoff_filter is not None and not df_v.empty and "acq_date" in df_v.columns:
            df_v = df_v[df_v["acq_date"].astype(str).str.strip() > post_cutoff_filter].copy()

        if not df_v.empty:
            viirs_parts.append(df_v)
            used_sources.append(candidate)
            if candidate == "VIIRS_SNPP_NRT":
                max_snpp_str = str(df_v["acq_date"].astype(str).str.strip().max())
                max_snpp_d = parse_iso_date(max_snpp_str)
                end_req_d = parse_iso_date(windows[-1].end_date)
                if end_req_d > max_snpp_d and max_snpp_d <= snpp_retirement_date:
                    post_windows = _windows_after_date(windows, max_snpp_str)
                    if post_windows:
                        logger.info(
                            f"VIIRS_SNPP_NRT stopped at {max_snpp_str}; switching to fallback for {post_windows[0].start_date}..{post_windows[-1].end_date}."
                        )
                        active_windows = post_windows
                        post_cutoff_filter = max_snpp_str
                        continue
                snpp_available = True
            break

        if candidate == "VIIRS_SNPP_NRT":
            logger.info("VIIRS_SNPP_NRT returned 0 detections; checking NOAA-20/NOAA-21 NRT.")
            continue
        if not used_sources:
            used_sources.append(candidate)
        break

    viirs_df = pd.concat(viirs_parts, ignore_index=True) if viirs_parts else pd.DataFrame()
    viirs_source_used = "+".join(used_sources) if used_sources else "none"

    return NrtFetchResult(
        modis_raw=modis_df,
        viirs_raw=viirs_df,
        viirs_source_used=viirs_source_used,
        snpp_available=snpp_available,
        windows_fetched=tuple(windows),
        requests_made=total_requests,
        errors=tuple(all_errors),
    )
