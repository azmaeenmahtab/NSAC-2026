"""Dataset loader: verifies `manifest.json` and registers Parquet tables as DuckDB views."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import h3
import pyarrow as pa

REQUIRED_PARQUET_TABLES: dict[str, str] = {
    "regions": "regions.parquet",
    "monthly_region": "monthly_region.parquet",
    "harmonized_region": "harmonized_region.parquet",
    "harmonized_cell": "harmonized_cell.parquet",
    "climatology": "climatology.parquet",
    "anomalies": "anomalies.parquet",
    "seasons": "seasons.parquet",
    "yearly": "yearly.parquet",
}

OPTIONAL_PARQUET_TABLES: dict[str, str] = {
    "region_cells": "region_cells.parquet",
    "monthly_cell": "monthly_cell.parquet",
    "calibration_report": "calibration_report.parquet",
    "events": "events.parquet",
}

_VALID_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


class DatasetLoadError(RuntimeError):
    """Raised on startup when `manifest.json` or any required Parquet table is missing."""


@dataclass(frozen=True)
class LoadedDataset:
    """In-memory handle for the active dataset version and its DuckDB connection."""

    data_dir: Path
    data_version: str
    as_of: str
    provisional_from: str | None
    manifest: dict[str, Any]
    connection: duckdb.DuckDBPyConnection
    registered_views: tuple[str, ...]

    def cursor(self) -> duckdb.DuckDBPyConnection:
        """Return a thread-local cursor cloned from the worker's DuckDB connection."""
        return self.connection.cursor()


def _validate_view_name(name: str) -> str:
    if not _VALID_IDENTIFIER_RE.match(name):
        raise ValueError(f"Unsafe SQL view identifier: {name!r}")
    return name


def _register_cell_centroids(
    con: duckdb.DuckDBPyConnection,
    registered: list[str],
) -> None:
    """Precompute `(h3_r7, lat, lon)` lookup table in DuckDB for fast bbox queries."""
    sources = ["SELECT DISTINCT h3_r7 FROM harmonized_cell"]
    if "monthly_cell" in registered:
        sources.append("SELECT DISTINCT h3_r7 FROM monthly_cell")

    union_sql = " UNION ".join(sources)
    rows = con.execute(union_sql).fetchall()

    if rows:
        cell_ids: list[int] = []
        lats: list[float] = []
        lons: list[float] = []
        for (cell_int,) in rows:
            u64 = int(cell_int)
            lat, lon = h3.cell_to_latlng(format(u64, "x"))
            cell_ids.append(u64)
            lats.append(float(lat))
            lons.append(float(lon))
        arrow_tbl = pa.table(
            {
                "h3_r7": pa.array(cell_ids, type=pa.uint64()),
                "lat": pa.array(lats, type=pa.float64()),
                "lon": pa.array(lons, type=pa.float64()),
            }
        )
        con.register("_tmp_centroids", arrow_tbl)
        con.execute("CREATE TABLE cell_centroids AS SELECT * FROM _tmp_centroids")
        con.unregister("_tmp_centroids")
    else:
        con.execute("CREATE TABLE cell_centroids (h3_r7 UBIGINT, lat DOUBLE, lon DOUBLE)")
    registered.append("cell_centroids")


def load_dataset(
    data_dir: Path | str,
    reference_dir: Path | str | None = None,
) -> LoadedDataset:
    """Load `manifest.json`, verify required Parquet files exist, and register DuckDB views.

    Raises:
        DatasetLoadError: If `manifest.json` or any required Parquet file is absent or invalid.
    """
    base_dir = Path(data_dir).resolve()
    if not base_dir.exists() or not base_dir.is_dir():
        raise DatasetLoadError(f"Dataset directory does not exist: {base_dir}")

    manifest_path = base_dir / "manifest.json"
    if not manifest_path.is_file():
        raise DatasetLoadError(f"Missing manifest.json in dataset directory: {manifest_path}")

    try:
        manifest_raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DatasetLoadError(f"Failed to parse manifest.json at {manifest_path}: {exc}") from exc

    if not isinstance(manifest_raw, dict):
        raise DatasetLoadError(f"manifest.json must be a JSON object: {manifest_path}")

    data_version = str(manifest_raw.get("data_version") or "").strip()
    as_of = str(manifest_raw.get("as_of_date") or "").strip()
    if not data_version or not as_of:
        raise DatasetLoadError(
            f"manifest.json at {manifest_path} is missing required 'data_version' or 'as_of_date'"
        )

    provisional_raw = manifest_raw.get("provisional_from")
    provisional_from = str(provisional_raw) if provisional_raw is not None else None

    # Verify all required Parquet files exist before opening DuckDB views
    resolved_files: dict[str, Path] = {}
    for view_name, filename in REQUIRED_PARQUET_TABLES.items():
        candidate = base_dir / filename
        if not candidate.is_file():
            raise DatasetLoadError(
                f"Required Parquet file '{filename}' for view '{view_name}' is missing in {base_dir}"
            )
        resolved_files[view_name] = candidate

    ref_dir = Path(reference_dir).resolve() if reference_dir else None
    for view_name, filename in OPTIONAL_PARQUET_TABLES.items():
        candidate = base_dir / filename
        if candidate.is_file():
            resolved_files[view_name] = candidate
        elif ref_dir is not None and (ref_dir / filename).is_file():
            resolved_files[view_name] = ref_dir / filename

    con = duckdb.connect(database=":memory:")
    registered: list[str] = []
    for view_name, parquet_path in sorted(resolved_files.items()):
        safe_view = _validate_view_name(view_name)
        posix_path = parquet_path.as_posix().replace("'", "''")
        con.execute(
            f"CREATE OR REPLACE VIEW {safe_view} AS SELECT * FROM read_parquet('{posix_path}')"
        )
        registered.append(safe_view)

    _register_cell_centroids(con, registered)

    return LoadedDataset(
        data_dir=base_dir,
        data_version=data_version,
        as_of=as_of,
        provisional_from=provisional_from,
        manifest=manifest_raw,
        connection=con,
        registered_views=tuple(registered),
    )
