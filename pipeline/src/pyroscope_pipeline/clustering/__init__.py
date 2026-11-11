"""Clustering feature module for PyroScope pipeline."""

from __future__ import annotations

from pyroscope_pipeline.clustering.events import (
    EVENTS_SCHEMA_COLUMNS,
    build_events,
    cluster_sensor_family,
)
from pyroscope_pipeline.clustering.geo import (
    EARTH_RADIUS_M,
    haversine_distance_m,
    meters_to_radians,
    radians_to_meters,
)
from pyroscope_pipeline.clustering.h3_index import (
    attach_h3_indices,
    cell_to_parent_u64,
    compute_h3_hierarchy,
    hex_to_u64,
    latlng_to_h3_u64,
    u64_to_hex,
)
from pyroscope_pipeline.clustering.regions import (
    assign_districts,
    load_district_cells_map,
    lookup_point_district,
    lookup_point_in_polygon,
)
from pyroscope_pipeline.clustering.run import (
    EVENTS_ARROW_SCHEMA,
    compute_annual_sensor_ratios,
    run_clustering,
)
from pyroscope_pipeline.clustering.st_dbscan import st_dbscan

__all__ = [
    "EARTH_RADIUS_M",
    "EVENTS_ARROW_SCHEMA",
    "EVENTS_SCHEMA_COLUMNS",
    "assign_districts",
    "attach_h3_indices",
    "build_events",
    "cell_to_parent_u64",
    "cluster_sensor_family",
    "compute_annual_sensor_ratios",
    "compute_h3_hierarchy",
    "haversine_distance_m",
    "hex_to_u64",
    "latlng_to_h3_u64",
    "load_district_cells_map",
    "lookup_point_district",
    "lookup_point_in_polygon",
    "meters_to_radians",
    "radians_to_meters",
    "run_clustering",
    "st_dbscan",
    "u64_to_hex",
]
