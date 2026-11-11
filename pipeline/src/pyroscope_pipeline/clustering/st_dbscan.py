"""Spatio-Temporal Density-Based Spatial Clustering of Applications with Noise (ST-DBSCAN).

Pure engine implementation for clustering satellite active-fire detections into physical
fire events based on spatial (Haversine distance in meters) and temporal (elapsed hours)
proximity constraints.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence

import numpy as np
from sklearn.neighbors import BallTree  # type: ignore[import-untyped]

from pyroscope_pipeline.clustering.geo import EARTH_RADIUS_M, meters_to_radians


def st_dbscan(
    lat: np.ndarray | Sequence[float],
    lon: np.ndarray | Sequence[float],
    t_hours: np.ndarray | Sequence[float],
    eps_s_m: float = 2700.0,
    eps_t_hours: float = 24.0,
    min_pts: int = 2,
) -> np.ndarray:
    """Group spatio-temporal detections into clusters using ST-DBSCAN.

    Neighbor definition:
        Point j is a neighbor of i iff haversine distance <= eps_s_m AND
        abs(t_i - t_j) <= eps_t_hours (both inclusive).
        min_pts counts the point itself (core point has at least min_pts neighbors).

    Border points are assigned to the cluster of the first core point that reaches
    them in index order. Unclustered points are assigned label -1 (noise).
    Cluster labels are consecutive integers starting from 0, ordered deterministically
    by the lowest input index in each cluster.

    Args:
        lat: Latitude coordinates in decimal degrees [-90.0, 90.0].
        lon: Longitude coordinates in decimal degrees [-180.0, 180.0].
        t_hours: Elapsed time in hours (UTC).
        eps_s_m: Spatial neighborhood threshold in meters (default: 2,700 m).
        eps_t_hours: Temporal neighborhood threshold in hours (default: 24.0 h).
        min_pts: Minimum number of points (including self) to form a core point.

    Returns:
        1D NumPy array of int64 cluster labels (-1 for noise, 0..K-1 for clusters).

    Raises:
        ValueError: If input lengths mismatch, inputs contain NaN or infinite values,
            coordinates are out of valid geographic ranges, or parameters are invalid.
    """
    lat_arr = np.asarray(lat, dtype=np.float64)
    lon_arr = np.asarray(lon, dtype=np.float64)
    t_arr = np.asarray(t_hours, dtype=np.float64)

    if lat_arr.ndim != 1 or lon_arr.ndim != 1 or t_arr.ndim != 1:
        raise ValueError("lat, lon, and t_hours must be 1-dimensional arrays")

    n_points = len(lat_arr)
    if not (len(lon_arr) == n_points and len(t_arr) == n_points):
        raise ValueError(
            f"lat, lon, and t_hours must have identical lengths, got {n_points}, {len(lon_arr)}, {len(t_arr)}"
        )

    if eps_s_m < 0.0:
        raise ValueError(f"eps_s_m must be non-negative, got {eps_s_m}")
    if eps_t_hours < 0.0:
        raise ValueError(f"eps_t_hours must be non-negative, got {eps_t_hours}")
    if min_pts < 1:
        raise ValueError(f"min_pts must be at least 1, got {min_pts}")

    if np.isnan(lat_arr).any() or np.isnan(lon_arr).any() or np.isnan(t_arr).any():
        raise ValueError("Coordinates and timestamps must not contain NaN")
    if np.isinf(lat_arr).any() or np.isinf(lon_arr).any() or np.isinf(t_arr).any():
        raise ValueError("Coordinates and timestamps must not contain infinite values")

    if np.any((lat_arr < -90.0) | (lat_arr > 90.0)):
        raise ValueError("Latitude values must be within [-90.0, 90.0]")
    if np.any((lon_arr < -180.0) | (lon_arr > 180.0)):
        raise ValueError("Longitude values must be within [-180.0, 180.0]")

    if n_points == 0:
        return np.zeros(0, dtype=np.int64)

    # 1. Spatial indexing using spherical BallTree with Haversine metric
    coords_rad = np.column_stack([np.radians(lat_arr), np.radians(lon_arr)])
    tree = BallTree(coords_rad, metric="haversine")
    r_rad = meters_to_radians(eps_s_m, earth_radius_m=EARTH_RADIUS_M)
    spatial_neighbors = tree.query_radius(coords_rad, r=r_rad)

    # 2. Filter spatio-temporal neighbors and identify core points
    st_neighbors: list[np.ndarray] = [None] * n_points  # type: ignore[list-item]
    is_core = np.zeros(n_points, dtype=bool)

    for i in range(n_points):
        cand = spatial_neighbors[i]
        # Temporal window condition: abs(t_i - t_j) <= eps_t_hours
        t_diff = np.abs(t_arr[cand] - t_arr[i])
        valid = cand[t_diff <= eps_t_hours]
        valid.sort()
        st_neighbors[i] = valid
        if len(valid) >= min_pts:
            is_core[i] = True

    # 3. Standard DBSCAN expansion with deterministic queue order
    labels = np.full(n_points, -1, dtype=np.int64)
    visited = np.zeros(n_points, dtype=bool)
    cluster_id = 0

    for i in range(n_points):
        if visited[i]:
            continue
        visited[i] = True

        if not is_core[i]:
            continue

        labels[i] = cluster_id
        queue: deque[int] = deque()

        for nb in st_neighbors[i]:
            if nb == i:
                continue
            if labels[nb] == -1:
                labels[nb] = cluster_id
            if not visited[nb]:
                visited[nb] = True
                if is_core[nb]:
                    queue.append(int(nb))

        while queue:
            curr = queue.popleft()
            for nb in st_neighbors[curr]:
                if labels[nb] == -1:
                    labels[nb] = cluster_id
                if not visited[nb]:
                    visited[nb] = True
                    if is_core[nb]:
                        queue.append(int(nb))

        cluster_id += 1

    # 4. Guarantee deterministic cluster IDs ordered by lowest input index
    if cluster_id > 0:
        min_indices: dict[int, int] = {}
        for idx, c in enumerate(labels):
            c_int = int(c)
            if c_int >= 0 and c_int not in min_indices:
                min_indices[c_int] = idx

        sorted_clusters = sorted(min_indices.keys(), key=lambda c: min_indices[c])
        if sorted_clusters != list(range(len(sorted_clusters))):
            mapping_arr = np.full(cluster_id, -1, dtype=np.int64)
            for new_c, old_c in enumerate(sorted_clusters):
                mapping_arr[old_c] = new_c
            mask = labels >= 0
            labels[mask] = mapping_arr[labels[mask]]

    return labels

