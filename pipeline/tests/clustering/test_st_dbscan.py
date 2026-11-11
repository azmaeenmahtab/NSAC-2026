"""Unit and property tests for pure ST-DBSCAN clustering engine."""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.metrics import adjusted_rand_score  # type: ignore[import-untyped]

from pyroscope_pipeline.clustering.geo import haversine_distance_m
from pyroscope_pipeline.clustering.st_dbscan import st_dbscan


def test_fixture_1_chain() -> None:
    """Fixture 1: Chain of three points A -> B -> C where A-B and B-C are neighbors but A-C is not.

    A (lon 0.000, t 0 h), B (lon 0.009, t 6 h), C (lon 0.018, t 30 h).
    A-B: ~1 km, 6 h (neighbors).
    B-C: ~1 km, 24 h (neighbors, inclusive boundary).
    A-C: ~2 km, 30 h (not neighbors due to time gap > 24 h).
    All three are core points; all share one cluster: labels [0, 0, 0].
    """
    lats = [0.0, 0.0, 0.0]
    lons = [0.000, 0.009, 0.018]
    t_hours = [0.0, 6.0, 30.0]

    labels = st_dbscan(
        lat=lats,
        lon=lons,
        t_hours=t_hours,
        eps_s_m=2700.0,
        eps_t_hours=24.0,
        min_pts=2,
    )

    assert isinstance(labels, np.ndarray)
    assert np.array_equal(labels, [0, 0, 0])


def test_fixture_2_isolated() -> None:
    """Fixture 2: Isolated point D at lon 0.45 (~50 km away), t 0 h.

    Has no neighbors within eps_s_m; label is -1 (noise).
    """
    labels = st_dbscan(
        lat=[0.0],
        lon=[0.45],
        t_hours=[0.0],
        eps_s_m=2700.0,
        eps_t_hours=24.0,
        min_pts=2,
    )

    assert np.array_equal(labels, [-1])


def test_fixture_3_time_gap() -> None:
    """Fixture 3: Time gap sensitivity.

    E (lon 0.000, t 0 h) and F (lon 0.000, t 24 h + 1 minute):
    Spatial distance 0 m, but temporal gap > 24 h -> not neighbors, both noise [-1, -1].
    With F at exactly 24.0 h (inclusive boundary):
    Temporal gap == 24 h -> neighbors, one cluster [0, 0].
    """
    # 24 hours + 1 minute
    labels_gap = st_dbscan(
        lat=[0.0, 0.0],
        lon=[0.0, 0.0],
        t_hours=[0.0, 24.0 + 1.0 / 60.0],
        eps_s_m=2700.0,
        eps_t_hours=24.0,
        min_pts=2,
    )
    assert np.array_equal(labels_gap, [-1, -1])

    # Exactly 24.0 hours (inclusive)
    labels_exact = st_dbscan(
        lat=[0.0, 0.0],
        lon=[0.0, 0.0],
        t_hours=[0.0, 24.0],
        eps_s_m=2700.0,
        eps_t_hours=24.0,
        min_pts=2,
    )
    assert np.array_equal(labels_exact, [0, 0])


def test_fixture_4_two_groups_far_apart() -> None:
    """Fixture 4: Two groups 50 km apart, each with two close points at the same time.

    Labels must be [0, 0, 1, 1] in order of appearance.
    """
    lats = [0.0, 0.0, 0.0, 0.0]
    lons = [0.000, 0.009, 0.450, 0.459]
    t_hours = [0.0, 0.0, 0.0, 0.0]

    labels = st_dbscan(
        lat=lats,
        lon=lons,
        t_hours=t_hours,
        eps_s_m=2700.0,
        eps_t_hours=24.0,
        min_pts=2,
    )

    assert np.array_equal(labels, [0, 0, 1, 1])


def test_fixture_5_border_point() -> None:
    """Fixture 5: Border point handling with min_pts = 3.

    Points P1, P2, P3 are mutually within range (~1.1 km apart).
    Point Q is within range of P1 (~1.67 km) but > 2.7 km from P2 (~2.78 km) and P3 (~3.89 km).
    P1, P2, P3 are core points (each has >= 3 neighbors).
    Q has only 2 neighbors (P1 and itself), so Q is a border point.
    Q is density-reachable from P1, so all 4 points share cluster 0: [0, 0, 0, 0].
    """
    lats = [0.0, 0.0, 0.0, 0.0]
    lons = [0.000, 0.010, 0.020, -0.015]
    t_hours = [0.0, 0.0, 0.0, 0.0]

    labels = st_dbscan(
        lat=lats,
        lon=lons,
        t_hours=t_hours,
        eps_s_m=2700.0,
        eps_t_hours=24.0,
        min_pts=3,
    )

    assert np.array_equal(labels, [0, 0, 0, 0])


def test_fixture_6_determinism_under_shuffle() -> None:
    """Fixture 6: Shuffling input order and mapping labels back yields the exact same partition."""
    rng = np.random.RandomState(42)
    # Construct 4 clusters and 10 noise points
    c1_lats = rng.normal(21.0, 0.005, 15)
    c1_lons = rng.normal(89.0, 0.005, 15)
    c1_t = rng.uniform(0.0, 10.0, 15)

    c2_lats = rng.normal(23.0, 0.005, 20)
    c2_lons = rng.normal(90.5, 0.005, 20)
    c2_t = rng.uniform(50.0, 60.0, 20)

    noise_lats = rng.uniform(25.0, 26.0, 10)
    noise_lons = rng.uniform(91.0, 92.0, 10)
    noise_t = np.arange(10) * 100.0  # Far apart in time

    lats = np.concatenate([c1_lats, c2_lats, noise_lats])
    lons = np.concatenate([c1_lons, c2_lons, noise_lons])
    times = np.concatenate([c1_t, c2_t, noise_t])

    orig_labels = st_dbscan(lats, lons, times, eps_s_m=2700.0, eps_t_hours=24.0, min_pts=2)

    for seed in [1, 7, 42, 99]:
        perm_rng = np.random.RandomState(seed)
        perm = perm_rng.permutation(len(lats))

        shuff_labels = st_dbscan(
            lats[perm],
            lons[perm],
            times[perm],
            eps_s_m=2700.0,
            eps_t_hours=24.0,
            min_pts=2,
        )

        mapped_back = np.empty_like(shuff_labels)
        mapped_back[perm] = shuff_labels

        # Adjusted Rand Index equals 1.0 (identical cluster partitions)
        ari = adjusted_rand_score(orig_labels, mapped_back)
        assert ari == 1.0
        # Noise sets are identical
        assert np.array_equal(orig_labels == -1, mapped_back == -1)


def test_property_no_chain_breaks() -> None:
    """Property test: No cluster contains two points with a chain break.

    Every cluster is connected under the neighbor relation through core points.
    """
    rng = np.random.RandomState(1337)
    n = 200
    lats = rng.uniform(22.0, 24.0, n)
    lons = rng.uniform(89.5, 91.5, n)
    times = rng.uniform(0.0, 200.0, n)

    eps_s_m = 2700.0
    eps_t_hours = 24.0
    min_pts = 2

    labels = st_dbscan(
        lats,
        lons,
        times,
        eps_s_m=eps_s_m,
        eps_t_hours=eps_t_hours,
        min_pts=min_pts,
    )

    # Reconstruct exact neighbor adjacency
    adj: list[list[int]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            d_s = haversine_distance_m(lats[i], lons[i], lats[j], lons[j])
            d_t = abs(times[i] - times[j])
            if d_s <= eps_s_m and d_t <= eps_t_hours:
                adj[i].append(j)
                if i != j:
                    adj[j].append(i)

    is_core = np.array([len(adj[i]) >= min_pts for i in range(n)])
    unique_clusters = set(labels[labels >= 0])

    for c in unique_clusters:
        pts = np.where(labels == c)[0]
        cores = [p for p in pts if is_core[p]]
        assert len(cores) > 0, f"Cluster {c} has no core points"

        # Verify connectivity of all core points within this cluster
        visited_core: set[int] = set()
        queue = [cores[0]]
        visited_core.add(cores[0])
        while queue:
            curr = queue.pop(0)
            for nb in adj[curr]:
                if nb in cores and nb not in visited_core:
                    visited_core.add(nb)
                    queue.append(nb)

        assert len(visited_core) == len(cores), f"Cluster {c} has disconnected core points"

        # Verify every border point in the cluster connects directly to at least one core point
        for p in pts:
            if not is_core[p]:
                has_core_neighbor = any(nb in cores for nb in adj[p])
                assert has_core_neighbor, f"Border point {p} in cluster {c} is disconnected from core"


def test_edge_cases_and_validations() -> None:
    """Test boundary cases, empty inputs, and input validation errors."""
    # Empty input
    empty_res = st_dbscan([], [], [])
    assert isinstance(empty_res, np.ndarray)
    assert len(empty_res) == 0

    # min_pts = 1 makes single isolated point a cluster
    single_res = st_dbscan([23.0], [90.0], [0.0], min_pts=1)
    assert np.array_equal(single_res, [0])

    # Mismatched array lengths
    with pytest.raises(ValueError, match="identical lengths"):
        st_dbscan([23.0, 24.0], [90.0], [0.0])

    # Negative epsilon
    with pytest.raises(ValueError, match="eps_s_m must be non-negative"):
        st_dbscan([23.0], [90.0], [0.0], eps_s_m=-1.0)

    with pytest.raises(ValueError, match="eps_t_hours must be non-negative"):
        st_dbscan([23.0], [90.0], [0.0], eps_t_hours=-1.0)

    # min_pts < 1
    with pytest.raises(ValueError, match="min_pts must be at least 1"):
        st_dbscan([23.0], [90.0], [0.0], min_pts=0)

    # NaN coordinates
    with pytest.raises(ValueError, match="contain NaN"):
        st_dbscan([np.nan], [90.0], [0.0])

    # Out of range coordinates
    with pytest.raises(ValueError, match="Latitude values must be within"):
        st_dbscan([95.0], [90.0], [0.0])

    with pytest.raises(ValueError, match="Longitude values must be within"):
        st_dbscan([23.0], [-190.0], [0.0])

