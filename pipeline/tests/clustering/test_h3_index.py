"""Unit tests for H3 spatial indexing helpers (Chunk D03)."""

from __future__ import annotations

import h3
import numpy as np
import pandas as pd
import pytest

from pyroscope_pipeline.clustering.h3_index import (
    attach_h3_indices,
    cell_to_parent_u64,
    compute_h3_hierarchy,
    hex_to_u64,
    latlng_to_h3_u64,
    u64_to_hex,
)

# Known test locations in Bangladesh with expected H3 indices
KNOWN_COORDINATES = [
    # Dhaka (23.8103 N, 90.4125 E)
    (23.8103, 90.4125, "873cf13b0ffffff", "863cf13b7ffffff", "853cf13bfffffff"),
    # Chattogram (22.3569 N, 91.7832 E)
    (22.3569, 91.7832, "873cc21a1ffffff", "863cc21a7ffffff", "853cc21bfffffff"),
    # Rajshahi (24.3636 N, 88.6241 E)
    (24.3636, 88.6241, "873cf435effffff", "863cf435fffffff", "853cf437fffffff"),
]


def test_h3_known_coordinates_and_hierarchy() -> None:
    """Verify 3 known lat/lon pairs against canonical H3 cells and parent relationships."""
    for lat, lon, exp_r7_hex, exp_r6_hex, exp_r5_hex in KNOWN_COORDINATES:
        # Check r7 resolution
        r7_u64 = latlng_to_h3_u64(lat, lon, res=7)
        r7_hex = u64_to_hex(r7_u64)
        assert r7_hex == exp_r7_hex, f"Mismatch for lat={lat}, lon={lon}: {r7_hex} vs {exp_r7_hex}"

        # Check parent resolution 6
        r6_u64 = cell_to_parent_u64(r7_u64, parent_res=6)
        r6_hex = u64_to_hex(r6_u64)
        assert r6_hex == exp_r6_hex
        assert h3.cell_to_parent(r7_hex, 6) == exp_r6_hex

        # Check parent resolution 5
        r5_u64 = cell_to_parent_u64(r7_u64, parent_res=5)
        r5_hex = u64_to_hex(r5_u64)
        assert r5_hex == exp_r5_hex
        assert h3.cell_to_parent(r7_hex, 5) == exp_r5_hex

        # Parent chain invariant
        assert cell_to_parent_u64(r6_u64, parent_res=5) == r5_u64


def test_hex_uint64_roundtrip() -> None:
    """Verify integer and hexadecimal string conversions roundtrip without precision loss."""
    for _, _, exp_r7_hex, _, _ in KNOWN_COORDINATES:
        u64_val = hex_to_u64(exp_r7_hex)
        back_hex = u64_to_hex(u64_val)
        assert back_hex == exp_r7_hex
        assert isinstance(u64_val, int)
        assert u64_val > 0


def test_compute_h3_hierarchy_vectorized() -> None:
    """Verify compute_h3_hierarchy returns correct UINT64 arrays for batch coordinates."""
    lats = [c[0] for c in KNOWN_COORDINATES]
    lons = [c[1] for c in KNOWN_COORDINATES]

    h3_dict = compute_h3_hierarchy(lats, lons)
    assert set(h3_dict.keys()) == {"h3_r7", "h3_r6", "h3_r5"}

    for arr in h3_dict.values():
        assert arr.dtype == np.uint64
        assert len(arr) == 3

    for i, (_, _, exp_r7_hex, exp_r6_hex, exp_r5_hex) in enumerate(KNOWN_COORDINATES):
        assert u64_to_hex(int(h3_dict["h3_r7"][i])) == exp_r7_hex
        assert u64_to_hex(int(h3_dict["h3_r6"][i])) == exp_r6_hex
        assert u64_to_hex(int(h3_dict["h3_r5"][i])) == exp_r5_hex


def test_attach_h3_indices_dataframe() -> None:
    """Verify attach_h3_indices attaches strictly typed UINT64 columns to a DataFrame."""
    df = pd.DataFrame({
        "lat": [23.8103, 22.3569],
        "lon": [90.4125, 91.7832],
        "dummy": ["a", "b"],
    })
    res = attach_h3_indices(df)
    assert "h3_r5" in res.columns
    assert "h3_r6" in res.columns
    assert "h3_r7" in res.columns
    assert res["h3_r5"].dtype == np.uint64
    assert res["h3_r6"].dtype == np.uint64
    assert res["h3_r7"].dtype == np.uint64
    assert len(res) == 2


def test_compute_h3_hierarchy_validation() -> None:
    """Verify compute_h3_hierarchy raises ValueError for mismatched coordinate lengths."""
    with pytest.raises(ValueError, match="equal length"):
        compute_h3_hierarchy([23.0, 24.0], [90.0])

