# D02 ST-DBSCAN engine (pure)

Depends: S00. Priority: P0. Window: EVENT. Read first: PRODUCT_BRIEF.md section 5 (clustering).

## Goal
A tested, pure spatio-temporal DBSCAN that groups pixel detections into fire clusters.

## Files (`pipeline/src/pyroscope_pipeline/clustering/`)
`st_dbscan.py`, `geo.py` (haversine helpers), `__init__.py`; tests in `pipeline/tests/clustering/`.

## Specification
- Signature: `st_dbscan(lat, lon, t_hours, eps_s_m, eps_t_hours, min_pts) -> labels` (NumPy arrays in, int labels out; `-1` = noise; labels are consecutive from 0, ordered by the lowest input index in each cluster so output is deterministic).
- Neighbor definition: point j is a neighbor of i iff haversine distance <= `eps_s_m` AND `abs(t_i - t_j) <= eps_t_hours` (both inclusive). `min_pts` counts the point itself.
- Implementation: `sklearn.neighbors.BallTree(metric="haversine")` radius query (radius = eps_s_m / 6,371,000 in radians) to get spatial neighbors, then filter by time; standard DBSCAN expansion (core points, density-reachable border points). Sort input by time first for locality. For memory, process in spatial tiles with overlap (tile size at least 2 x eps) if the point count exceeds 500,000; this is optional now.
- Border points are assigned to the cluster of the first core point that reaches them (deterministic by index order).
- No I/O, no global state, no randomness.

## Hand-verified fixtures (near the equator, 0.009 degrees of longitude is about 1.0 km)
Use `eps_s_m = 2700`, `eps_t_hours = 24`, `min_pts = 2`.
1. Chain: A (lon 0.000, t 0 h), B (lon 0.009, t 6 h), C (lon 0.018, t 30 h). A-B: 1 km, 6 h: neighbors. B-C: 1 km, 24 h: neighbors (inclusive). A-C: 2 km, 30 h: not neighbors. All three are core points (each has at least 2 points including itself), so all share one cluster: labels `[0, 0, 0]`.
2. Isolated: D at lon 0.45 (about 50 km away), t 0 h: label `-1`.
3. Time gap: E (lon 0.000, t 0 h) and F (lon 0.000, t 24 h + 1 minute): not neighbors, both noise `[-1, -1]`. With F at exactly 24 h: one cluster `[0, 0]`.
4. Two groups far apart (50 km), each with two close points at the same time: labels `[0, 0, 1, 1]`.
5. Border point: with `min_pts = 3`, points P1, P2, P3 mutually within range and Q within range of P1 only: P1, P2, P3 core, Q border (assigned to the same cluster since it is density-reachable): `[0, 0, 0, 0]`.
6. Determinism: shuffling the input order and mapping labels back yields the same partition.
Also a property test: no cluster contains two points with a chain break (every cluster is connected under the neighbor relation through core points).

## Tasks
- [x] Implementation per spec with docstrings stating units
- [x] All six fixtures pass; property test passes
- [x] Performance check on 250,000 synthetic points (record seconds and memory in the PR; target under 3 minutes)
- [x] Master plan row D02 set to `[x]`
