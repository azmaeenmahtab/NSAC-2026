# P01 Acquire historical FIRMS archives

Depends: P00. Priority: P0. Window: PRE. Read first: PRODUCT_BRIEF.md section 5; the current FIRMS pages for Archive Download, the API area page and the FAQ (VERIFY everything below).

## Goal
Raw CSVs for MODIS (2000-11 to latest) and VIIRS S-NPP (2012-01 to latest) covering Bangladesh plus a margin, stored outside git with a checksum manifest, ready for chunk D01.

## Specification
- Area: bounding box `88.0,20.5,92.8,26.7` expanded by 0.5 degrees on each side (so border clipping happens later with the country polygon). VERIFY that this box contains all of Bangladesh.
- Sensors and products: MODIS Collection 6.1 Standard Processing (Terra+Aqua), VIIRS S-NPP 375 m Standard Processing. Optional: VIIRS NOAA-20 Standard Processing for a later sensitivity check. Standard Processing lags the present by weeks to months; fill the recent tail with NRT products later (chunk D08) and mark it provisional.
- Method 1 (preferred): the FIRMS Archive Download request form (custom area, date range, CSV). Large requests are processed on the server and a download link is provided; submit them today.
- Method 2 (fallback): FIRMS area API `/api/area/csv/{MAP_KEY}/{SOURCE}/{west,south,east,north}/{DAY_RANGE}/{DATE}` with `SOURCE` = `MODIS_SP` or `VIIRS_SNPP_SP`. VERIFY the allowed `DAY_RANGE` (the official page says 1 to 10; some sources say 5), the transaction cost per call, and that the country endpoint is not used. Write a throwaway script in `spikes/firms_area_download.py` that loops over date windows, throttles to at most 3,000 transactions per 10 minutes, retries 5xx/504 with exponential backoff, and resumes after a crash.
- Check coverage with the FIRMS data-availability endpoint (VERIFY name) and note gaps.
- Storage: `data/raw/<sensor>/<name>.csv` on the shared drive; never commit. Create `data/raw/MANIFEST.json` listing file name, sensor, date range, row count, sha256, download date, request id or URL (without the MAP_KEY).

## Tasks
- [x] Archive requests submitted for MODIS and VIIRS S-NPP (request IDs 842592 and 842593)
- [x] Fallback downloader written and tested on one month (archive succeeded directly)
- [x] Files downloaded; row counts per file logged; manifest with checksums created (837,168 total fire detections)
- [x] Coverage check: first and last date per sensor verified (2000-11-02 to 2026-11-01)
- [x] Shared drive link and manifest committed (manifest only) to `data/raw/MANIFEST.json`
- [x] Master plan row P01 set to `[x]`
