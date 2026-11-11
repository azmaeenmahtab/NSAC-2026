"""FastAPI dependencies for accessing the active `LoadedDataset` and DuckDB cursors."""

from __future__ import annotations

from collections.abc import Generator

import duckdb
from fastapi import Request

from app.core.dataset import DatasetLoadError, LoadedDataset


def get_dataset(request: Request) -> LoadedDataset:
    """Return the active `LoadedDataset` stored on `request.app.state.dataset`."""
    dataset = getattr(request.app.state, "dataset", None)
    if not isinstance(dataset, LoadedDataset):
        raise DatasetLoadError("Dataset is not loaded on application state")
    return dataset


def get_db_cursor(request: Request) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Yield a thread-safe DuckDB cursor from the active dataset connection."""
    dataset = get_dataset(request)
    cursor = dataset.cursor()
    try:
        yield cursor
    finally:
        cursor.close()

