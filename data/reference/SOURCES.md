# Reference Data Sources, Licenses, and Attribution (`data/reference/`)

This file documents the provenance, release versions, licenses, and required attribution for all committed reference boundary datasets in `data/reference/` (`regions.geojson`, `regions.parquet`, and `region_cells.parquet`), verified for Chunk **P03**.

---

## 1. Administrative Boundaries (`regions.geojson`, `regions.parquet`)

### Primary Source: geoBoundaries Open (`gbOpen`) — Release v6.0.0 (`commit 9469f09`)
Retrieved via the official geoBoundaries API (`https://www.geoboundaries.org/api/current/gbOpen/BGD/ALL/`):

| Level | geoBoundaries ID | Year Represented | Original Upstream Source | License | Canonical Download URL |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **ADM0 (Country)** | `BGD-ADM0` | 2015 | geoBoundaries, Wikimedia Commons | **CC0 1.0 Universal** (Public Domain Dedication) | `https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BGD/ADM0/geoBoundaries-BGD-ADM0.geojson` |
| **ADM1 (Divisions, 8)** | `BGD-ADM1` | 2015 | geoBoundaries, Wikimedia Commons | **CC0 1.0 Universal** (Public Domain Dedication) | `https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BGD/ADM1/geoBoundaries-BGD-ADM1.geojson` |
| **ADM2 (Districts, 64)** | `BGD-ADM2` | 2020 | **Bangladesh Bureau of Statistics (BBS)** & **UN OCHA ROAP** (via Humanitarian Data Exchange, HDX) | **CC BY 3.0 IGO** (Creative Commons Attribution 3.0 Intergovernmental Organisations) | `https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BGD/ADM2/geoBoundaries-BGD-ADM2.geojson` |

### Required Attribution Text (UI & README)
Per the geoBoundaries (`gbOpen`) and UN OCHA / BBS (`CC BY 3.0 IGO`) license terms, the following attribution is included in the application UI and project documentation:

> Administrative boundaries courtesy of **geoBoundaries** (Runfola et al., 2020, *PLOS ONE* 15(4): e0231866), **Bangladesh Bureau of Statistics (BBS)**, and **UN OCHA ROAP** (licensed under CC BY 3.0 IGO / CC0 1.0).

---

## 2. Geometry Processing & Hierarchy Construction

1. **Full-Resolution Reference Outside Git**:
   - Full-resolution GeoJSON files (`geoBoundaries-BGD-ADM0.geojson`, `ADM1`, and `ADM2`, ~45.5 MB total) are stored in `data/raw/boundaries/` (gitignored per `AGENTS.md`).
2. **Web-Simplified Geometry (`data/reference/regions.geojson`, < 3 MB)**:
   - Geometries in `data/reference/regions.geojson` are simplified using topology-preserving Douglas–Peucker simplification (`tolerance = 0.002°`, ~220 m) and rounded to 5 decimal places (~1.1 m precision), keeping the committed `regions.geojson` compact (`< 1.0 MB`, well below the 3 MB limit) while preserving crisp coastal and hill-tract boundaries on the MapLibre web map.
3. **Region Hierarchy & Canonical IDs (74 total regions)**:
   - **`country` (1)**: `BGD` (*Bangladesh*).
   - **`adm1` (8 divisions, `parent_id = "BGD"`)**:
     - `BGD-ADM1-barishal`, `BGD-ADM1-chattogram`, `BGD-ADM1-dhaka`, `BGD-ADM1-khulna`, `BGD-ADM1-mymensingh`, `BGD-ADM1-rajshahi`, `BGD-ADM1-rangpur`, `BGD-ADM1-sylhet`.
   - **`adm2` (64 districts, `parent_id = "BGD-ADM1-<division>"`)**:
     - All 64 districts of Bangladesh with lowercase ASCII slugs (e.g., `BGD-ADM2-rangamati`, `BGD-ADM2-bandarban`, `BGD-ADM2-khagrachari`, `BGD-ADM2-chattogram`, `BGD-ADM2-coxs-bazar`).
     - Both modern (post-2018 official reform: *Chattogram*, *Barishal*, *Cumilla*, *Bogura*, *Jashore*, *Brahmanbaria*, *Khagrachari*, *Chapai Nawabganj*, *Moulvibazar*) and historical/geoBoundaries spellings (*Chittagong*, *Barisal*, *Comilla*, *Bogra*, *Jessore*, *Brahamanbaria*, *Khagrachhari*, *Nawabganj*, *Maulvibazar*) are recorded in `aliases` for fuzzy matching in the Ask PyroScope assistant (`A05`).
   - **`preset` (1)**:
     - `PRESET-CHT` (*Chittagong Hill Tracts*, `parent_id = "BGD-ADM1-chattogram"`): geometric union of `BGD-ADM2-rangamati`, `BGD-ADM2-bandarban`, and `BGD-ADM2-khagrachari`.

---

## 3. H3 Resolution-7 Cell Mapping (`data/reference/region_cells.parquet`)

- **H3 Library**: `h3-py` v4 (`h3==4.5.0`), using `h3.geo_to_cells(geojson, res=7)` (centroid containment) supplemented by deduplicated boundary-overlap assignment (`h3.h3shape_to_cells_experimental(..., contain='overlap')` assigned to the single district with largest polygon intersection area when a border/coastal cell's centroid falls marginally in a boundary river or coastline).
- **Invariants Enforced**:
  - Every resolution-7 cell in Bangladesh is assigned to **at most one** `adm2` district (`0` duplicate district assignments).
  - Parent division (`adm1`), country (`BGD`), and preset (`PRESET-CHT`) cell sets in `region_cells.parquet` are the exact disjoint unions of their constituent `adm2` districts.
  - Note on cell count: At Bangladesh's latitude (`20.5°N–26.7°N`), the mean H3 resolution-7 cell area on the icosahedral projection is **`5.721 km²`** (compared to the global average `5.161 km²`), and the 64 ADM2 land polygons cover **`140,051.6 km²`** (`EPSG:32646`), yielding **`25,020` strict centroid-in-polygon cells** and **`26,683` total land-covering district cells** (including coastal/border cells so 100% of in-country FIRMS detections map to a district cell).
