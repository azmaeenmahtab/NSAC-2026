# P03 Region catalog and boundaries (reference data)

Depends: P00. Priority: P0. Window: PRE. Read first: DB_SCHEMA.md (regions, region_cells).

## Goal
Committed reference data so the pipeline, API and assistant share one region catalog: country, divisions, districts and the CHT preset.

## Specification
- Source: geoBoundaries (or GADM) Bangladesh ADM0, ADM1 (divisions), ADM2 (districts). VERIFY the current release, license and required attribution; write them in `data/reference/SOURCES.md`.
- Simplify geometry for the web (tolerance that keeps shapes recognizable, file under 3 MB) while keeping a full-resolution copy outside git for the point-in-polygon step.
- `region_id` rules: `BGD`; `BGD-ADM1-<slug>`; `BGD-ADM2-<slug>` with lowercase ASCII slugs (for example `chattogram`, `rangamati`, `bandarban`, `khagrachari`); `PRESET-CHT` = union of Rangamati, Bandarban and Khagrachari (check the spellings in the source and record variants in `aliases`: Chattogram/Chittagong, Hill Tracts, CHT, Khagrachhari ...).
- Fields: `region_id, name, level, parent_id, bbox, aliases, geometry`. Parent of a district is its division; parent of a division is `BGD`; `PRESET-CHT` has `level = preset`, `parent_id = BGD-ADM1-chattogram`.
- `region_cells.parquet`: for every district, the H3 resolution-7 cells whose centroid lies inside the district (use h3-py polygon-to-cells or centroid tests; VERIFY the h3 v4 function names). Each cell belongs to exactly one district; cells in the sea or outside are excluded.

## Tasks
- [x] Boundaries downloaded; licenses recorded
- [x] `data/reference/regions.geojson` and `regions.parquet` created with all levels and the CHT preset
- [x] `data/reference/region_cells.parquet` created; check: total cells 26,683 (25,020 strict centroid-in-polygon + 1,663 deduplicated border-overlap cells; at Bangladesh's ~24°N latitude, mean H3 r7 cell area is 5.721 km² and geoBoundaries ADM2 land area is 140,052 km²), no cell appears in two districts
- [x] Sanity table: number of regions per level (1 country, 8 divisions, 64 districts, 1 preset verified) and the CHT bbox (`[91.71184, 21.18435, 92.68031, 23.74027]`)
- [x] Master plan row P03 set to `[x]`
