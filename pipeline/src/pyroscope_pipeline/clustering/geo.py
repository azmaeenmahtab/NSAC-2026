"""Geographic calculation helpers for spatio-temporal clustering.

Provides Haversine distance calculations and coordinate conversions using a spherical Earth model.
"""

from __future__ import annotations

import numpy as np

# Spherical Earth radius in meters matching NASA FIRMS and scikit-learn standard
EARTH_RADIUS_M: float = 6_371_000.0


def meters_to_radians(
    meters: float,
    earth_radius_m: float = EARTH_RADIUS_M,
) -> float:
    """Convert distance in meters to angular distance in radians on a spherical Earth.

    Args:
        meters: Distance in meters (m). Must be non-negative.
        earth_radius_m: Earth radius in meters (default 6,371,000.0 m).

    Returns:
        Angular distance in radians (rad).
    """
    if meters < 0:
        raise ValueError("Distance in meters cannot be negative")
    return meters / earth_radius_m


def radians_to_meters(
    radians: float,
    earth_radius_m: float = EARTH_RADIUS_M,
) -> float:
    """Convert angular distance in radians to distance in meters on a spherical Earth.

    Args:
        radians: Angular distance in radians (rad). Must be non-negative.
        earth_radius_m: Earth radius in meters (default 6,371,000.0 m).

    Returns:
        Distance in meters (m).
    """
    if radians < 0:
        raise ValueError("Angular distance in radians cannot be negative")
    return radians * earth_radius_m


def haversine_distance_m(
    lat1: float | np.ndarray,
    lon1: float | np.ndarray,
    lat2: float | np.ndarray,
    lon2: float | np.ndarray,
    earth_radius_m: float = EARTH_RADIUS_M,
) -> float | np.ndarray:
    """Compute the Haversine great-circle distance between coordinate pairs.

    Args:
        lat1: Latitude of first point(s) in decimal degrees [-90.0, 90.0].
        lon1: Longitude of first point(s) in decimal degrees [-180.0, 180.0].
        lat2: Latitude of second point(s) in decimal degrees [-90.0, 90.0].
        lon2: Longitude of second point(s) in decimal degrees [-180.0, 180.0].
        earth_radius_m: Earth radius in meters (default 6,371,000.0 m).

    Returns:
        Great-circle distance in meters (m). Returns a float if all inputs are scalar,
        or a NumPy array if any input is an array.
    """
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    # Guard against precision errors exceeding [0.0, 1.0]
    a = np.clip(a, 0.0, 1.0)
    c = 2.0 * np.arcsin(np.sqrt(a))
    dist = earth_radius_m * c

    if np.isscalar(lat1) and np.isscalar(lon1) and np.isscalar(lat2) and np.isscalar(lon2):
        return float(dist)
    return np.asarray(dist, dtype=np.float64)

