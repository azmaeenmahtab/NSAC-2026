"""Chunked CSV readers for NASA FIRMS satellite archives and NRT data."""

from collections.abc import Generator
from pathlib import Path

import pandas as pd


def detect_sensor_family(file_path: Path | str) -> str:
    """Identify whether a file is MODIS or VIIRS based on path or headers."""
    name = Path(file_path).name.upper()
    if "M-C61" in name or "MODIS" in name:
        return "MODIS"
    if "SV-C2" in name or "VNP" in name or "VIIRS" in name or "SNPP" in name:
        return "VIIRS"

    # Inspect first row
    sample = pd.read_csv(file_path, nrows=2)
    if "bright_ti4" in sample.columns:
        return "VIIRS"
    return "MODIS"


def read_firms_chunks(
    csv_path: Path | str,
    chunksize: int = 100_000,
) -> Generator[pd.DataFrame, None, None]:
    """Read FIRMS CSV in memory-bounded chunks."""
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"FIRMS CSV not found: {path}")

    yield from pd.read_csv(path, chunksize=chunksize, low_memory=False)


def clip_bounding_box(
    df: pd.DataFrame,
    bbox: list[float],
) -> tuple[pd.DataFrame, int]:
    """Clip coordinates to bounding box [west, south, east, north].

    Returns (clipped_df, dropped_count)
    """
    if df.empty or len(bbox) != 4:
        return df, 0

    west, south, east, north = bbox
    lat_ok = (df["lat"] >= south) & (df["lat"] <= north)
    lon_ok = (df["lon"] >= west) & (df["lon"] <= east)
    valid_coords = lat_ok & lon_ok

    dropped = int((~valid_coords).sum())
    return df.loc[valid_coords].copy(), dropped
