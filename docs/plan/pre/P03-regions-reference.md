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
- [ ] Boundaries downloaded; licenses recorded
- [ ] `data/reference/regions.geojson` and `regions.parquet` created with all levels and the CHT preset
- [ ] `data/reference/region_cells.parquet` created; check: total cells about 28,000 to 30,000 (Bangladesh is about 148,000 km2 and an r7 cell is about 5.2 km2), no cell appears in two districts
- [ ] Sanity table: number of regions per level (1, 8, 64 expected; VERIFY) and the CHT bbox
- [ ] Master plan row P03 set to `[x]`
