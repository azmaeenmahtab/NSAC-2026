"""H3 spatial indexing pure helpers for fire events.

Provides high-performance conversion from WGS84 geographic coordinates (lat/lon)
to Uber H3 hierarchical hexagonal spatial indexes at resolutions 5, 6, and 7,
stored strictly as UINT64 per DB_SCHEMA.md.
"""

from __future__ import annotations

from collections.abc import Sequence

import h3
import numpy as np
import pandas as pd


def latlng_to_h3_u64(lat: float, lon: float, res: int = 7) -> int:
    """Convert a single lat/lon coordinate to an H3 integer index at given resolution."""
    hex_str = h3.latlng_to_cell(float(lat), float(lon), int(res))
    return int(hex_str, 16)


def cell_to_parent_u64(cell_u64: int, parent_res: int) -> int:
    """Derive parent H3 integer index at a coarser resolution."""
    hex_str = f"{cell_u64:x}"
    parent_hex = h3.cell_to_parent(hex_str, int(parent_res))
    return int(parent_hex, 16)


def u64_to_hex(cell_u64: int) -> str:
    """Format an H3 UINT64 integer index to lowercase hexadecimal string."""
    return f"{cell_u64:x}"


def hex_to_u64(cell_hex: str) -> int:
    """Parse an H3 hexadecimal string to integer."""
    return int(cell_hex.strip(), 16)


def compute_h3_hierarchy(
    latitudes: np.ndarray | Sequence[float],
    longitudes: np.ndarray | Sequence[float],
) -> dict[str, np.ndarray]:
    """Compute H3 resolution 7, 6, and 5 integer cells for coordinate arrays.

    Args:
        latitudes: 1D array of latitude coordinates.
        longitudes: 1D array of longitude coordinates.

    Returns:
        Dictionary mapping column names ('h3_r7', 'h3_r6', 'h3_r5') to
        NumPy arrays with dtype np.uint64.
    """
    lats = np.asarray(latitudes, dtype=np.float64)
    lons = np.asarray(longitudes, dtype=np.float64)

    if lats.ndim != 1 or lons.ndim != 1 or len(lats) != len(lons):
        raise ValueError("latitudes and longitudes must be 1D arrays of equal length")

    n = len(lats)
    r7_arr = np.empty(n, dtype=np.uint64)
    r6_arr = np.empty(n, dtype=np.uint64)
    r5_arr = np.empty(n, dtype=np.uint64)

    for i in range(n):
        c7_hex = h3.latlng_to_cell(float(lats[i]), float(lons[i]), 7)
        c6_hex = h3.cell_to_parent(c7_hex, 6)
        c5_hex = h3.cell_to_parent(c7_hex, 5)

        r7_arr[i] = np.uint64(int(c7_hex, 16))
        r6_arr[i] = np.uint64(int(c6_hex, 16))
        r5_arr[i] = np.uint64(int(c5_hex, 16))

    return {
        "h3_r7": r7_arr,
        "h3_r6": r6_arr,
        "h3_r5": r5_arr,
    }


def attach_h3_indices(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
) -> pd.DataFrame:
    """Return a copy of DataFrame with h3_r5, h3_r6, h3_r7 columns attached.

    Columns are strictly typed as np.uint64.
    """
    if df.empty:
        out = df.copy()
        out["h3_r5"] = np.empty(0, dtype=np.uint64)
        out["h3_r6"] = np.empty(0, dtype=np.uint64)
        out["h3_r7"] = np.empty(0, dtype=np.uint64)
        return out

    h3_cols = compute_h3_hierarchy(df[lat_col].values, df[lon_col].values)
    out = df.copy()
    out["h3_r5"] = h3_cols["h3_r5"]
    out["h3_r6"] = h3_cols["h3_r6"]
    out["h3_r7"] = h3_cols["h3_r7"]
    return out

