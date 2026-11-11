"""Standardized API success envelope and metadata helpers."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ResponseMeta(BaseModel):
    """Metadata attached to every enveloped API response."""

    dataVersion: str = Field(..., examples=["v0.1.0-fixtures"])
    asOf: str = Field(..., examples=["2025-12-31"])


class ApiEnvelope[T](BaseModel):
    """Generic `{ data, meta }` API envelope."""

    data: T
    meta: ResponseMeta


def wrap_envelope[T](data: T, data_version: str, as_of: str) -> dict[str, object]:
    """Construct a `{ data, meta: { dataVersion, asOf } }` dictionary."""
    return {
        "data": data,
        "meta": {
            "dataVersion": data_version,
            "asOf": as_of,
        },
    }
