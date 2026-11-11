# P02 Explore the data and verify the report's claims

Depends: P01. Priority: P0. Window: PRE. Throwaway notebook or script in `spikes/explore/`, not part of the submission build.

## Goal
Know the real numbers before we build and pitch: verify or correct every claim in the research report, and set the parameters that depend on data.

## Questions to answer in `docs/DATA_FINDINGS.md` (tables plus 3 to 5 plain sentences each)
1. Row counts per sensor and per year (Bangladesh polygon or bbox). Annual detections MODIS vs VIIRS; the ratio VIIRS/MODIS per year from 2012. Does it match the report's 3,029 vs 10,972 and "3 to 7 times"? Report the real values.
2. Confidence field: value distributions for MODIS (numeric) and VIIRS (l, n, h). What share is dropped by the filter in PRODUCT_BRIEF section 5? Does the MODIS `type` column exist in the SP files?
3. Column names and types per sensor; how `acq_time` looks (HHMM, leading zeros); any duplicates; any rows outside the box.
4. Coverage: first complete month for MODIS and for VIIRS S-NPP; any missing days; which months form the overlap.
5. Day/night split and FRP statistics.
6. Monthly pattern for the Chittagong Hill Tracts box (about 91.6 to 92.7 E, 21.2 to 23.8 N, VERIFY with P03 polygons): is March-May dominant in both sensors?
7. Sensor steps: does the MODIS yearly count change around 2002 (Aqua joined)? Does VIIRS change in 2018 or 2023 if NOAA-20/21 files are examined?
8. A rough estimate of events per year after a quick DBSCAN at the default parameters, to size the pipeline runtime.

## Tasks
- [x] Exploration script or notebook runs end to end on the raw files (outputs not committed)
- [x] `docs/DATA_FINDINGS.md` written with the tables above
- [x] PRODUCT_BRIEF.md section 4 and 5 updated where the findings differ; list changes in the Deviation Log
- [x] Decision recorded: whether the NOAA-20 sensitivity check (P2) is worth planning
- [x] Master plan row P02 set to `[x]`
