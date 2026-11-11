"""Tests for geographic and Haversine distance helpers."""

from __future__ import annotations

import numpy as np
import pytest

from pyroscope_pipeline.clustering.geo import (
    EARTH_RADIUS_M,
    haversine_distance_m,
    meters_to_radians,
    radians_to_meters,
)


def test_meters_to_radians_and_inverse() -> None:
    """Verify conversion round-trips and basic distances."""
    dist_m = 2700.0
    rad = meters_to_radians(dist_m)
    assert np.isclose(rad, 2700.0 / EARTH_RADIUS_M)
    assert np.isclose(radians_to_meters(rad), dist_m)

    with pytest.raises(ValueError, match="cannot be negative"):
        meters_to_radians(-1.0)

    with pytest.raises(ValueError, match="cannot be negative"):
        radians_to_meters(-0.1)


def test_haversine_same_point() -> None:
    """Distance between identical coordinates is 0.0."""
    dist = haversine_distance_m(23.5, 90.0, 23.5, 90.0)
    assert isinstance(dist, float)
    assert dist == 0.0


def test_haversine_equator_longitude_step() -> None:
    """0.009 degrees of longitude at the equator is ~1000.8 m (~1 km)."""
    dist = haversine_distance_m(0.0, 0.0, 0.0, 0.009)
    assert isinstance(dist, float)
    expected = EARTH_RADIUS_M * np.radians(0.009)
    assert np.isclose(dist, expected, atol=1e-3)
    assert 1000.0 <= dist <= 1001.0


def test_haversine_vectorized() -> None:
    """Vectorized calculation produces array outputs with correct shapes and values."""
    lats1 = np.array([0.0, 10.0, 20.0])
    lons1 = np.array([0.0, 0.0, 0.0])
    lats2 = np.array([0.0, 10.0, 20.0])
    lons2 = np.array([0.009, 0.009, 0.009])

    dists = haversine_distance_m(lats1, lons1, lats2, lons2)
    assert isinstance(dists, np.ndarray)
    assert dists.shape == (3,)
    # Longitude step distance shrinks with cos(lat)
    assert dists[0] > dists[1] > dists[2]

