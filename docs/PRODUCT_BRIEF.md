# Product brief: PyroScope

## 1. Context

- Event: NASA Space Apps Challenge 2026. Hackathon Nov 14-15, 2026. Project submission opens Nov 14 at 09:00 and closes Nov 15 at 23:59 local time (VERIFY in the Project Submission Guide released Nov 13). Teams have at most 6 members.
- Challenge: Harmonization of MODIS and VIIRS Hot Spots. Build a web app that harmonizes MODIS and VIIRS active-fire records into a Burning Activity Calendar for a selected area of interest, for early warning, emergency responders, scientists and land managers.
- Team: Singularity. Project: PyroScope. Calendar feature: FireCalendar. (The research report's introduction says "Team Perceptron"; fix it everywhere to "Singularity".)
- Judging: expected criteria Impact, Creativity, Validity, Relevance, Presentation (VERIFY against the 2026 Judging and Awards Guide, released Nov 13). Local judging may use a 240-second pitch; align the demo with that.

## 2. The problem in one paragraph

MODIS (1 km, since 2000) and VIIRS (375 m, since 2012) both report active-fire pixels. VIIRS sees many more small fires, so plotting raw counts across 2012 shows a fake "hidden jump". PyroScope clusters pixels into fire events, calibrates VIIRS to the MODIS record, and shows one consistent 2000-present calendar so users can tell whether current burning is normal for the place and season.

## 3. Product scope

Area of interest for the build: **Bangladesh** (country), with districts and a **Chittagong Hill Tracts (CHT)** preset (Rangamati, Bandarban, Khagrachari). The architecture is region-agnostic; global coverage is out of scope for this event.

| Tier | Feature (pitch name) | Chunks |
| --- | --- | --- |
| P0 | Harmonized data pipeline (ingest, ST-DBSCAN events, H3, monthly tables, quantile-mapping harmonization with validation) | D01-D07 |
| P0 | Hex map of harmonized fire density with time range and metric toggle | A02, F02 |
| P0 | Area selection (country, district, CHT preset, custom bbox) with shareable URL | A01, F03 |
| P0 | FireCalendar (years x months, anomaly flags, season band) and the "hidden jump" chart (raw MODIS, raw VIIRS, naive splice, harmonized) | A03, F04 |
| P0 | Yearly area-wise burn statistics | D07, A03, F05 (basic table in F04) |
| P0 | Ask PyroScope assistant grounded in typed tools, with citations and a labelled replay mode | A05, F07 |
| P0 | Methodology and transparency page (diagnostics, parameters, limitations) | A03, F08 |
| P1 | Automatic data updates from FIRMS NRT with "data as of" and provisional flags | D08 |
| P1 | Warning notifications when an area's calendar dates approach or activity exceeds normal | A04, F06 |
| P1 | Prevention and mitigation guidance and Wildland Action Planner (rule-based checklists) | A06, F05 |
| P2 | Burned-area product comparison (MCD64A1/VNP64A1), NOAA-20/21 sensitivity, SMS/Telegram alerts, more countries | none |
| CUT | User accounts, global scale, Text-to-SQL, model training on fire data, mobile app | none |

## 4. Demo story (maps to the 240-second pitch)

1. The "hidden jump": raw counts jump in 2012 for Bangladesh. (F04 chart)
2. PyroScope removes the artificial jump: same chart with the harmonized line. (D06 result, F04)
3. Pick the CHT preset. FireCalendar shows the March-May season and flags an anomalous month. (F03, F04)
4. Click a hexagon on the 3D map to see its local calendar. (F02)
5. Ask: "When does fire season usually start in the Chittagong Hill Tracts, and was last year unusual?" and get a cited answer. (F07)
6. A warning for an area whose season is about to start; guidance checklist. (P1)
7. Methodology page: validation numbers, limitations. (F08)

Real numbers verified from data (chunk P02, `docs/DATA_FINDINGS.md`): in the 2012–2025 overlap, Bangladesh averaged 9,645 raw MODIS and 39,193 raw VIIRS detections/year (raw ratio 4.10x, filtered ratio 3.77x, not the report's 3,029 vs 10,972 or "3 to 7 times"). After ST-DBSCAN clustering, physical fire events average ~560 (MODIS) vs ~860 (VIIRS) per year (ratio only ~1.5x). Over 97% of burning in the Chittagong Hill Tracts (which accounts for ~40-45% of all national detections) occurs in March–May.

## 5. Method summary and parameters (defaults; all live in `pipeline/config.yaml`)

| Step | Rule | Default |
| --- | --- | --- |
| Sources | FIRMS Standard Processing archives: MODIS (Terra+Aqua, MCD14DL C6.1) and VIIRS S-NPP (VNP14IMGTDL). Tail filled with NRT products | Verified in P01/P02 |
| Confidence filter | MODIS numeric confidence >= 30 (drops 3.6% low); VIIRS `n` and `h` (drops 8.8% low). `type` = 0 when column exists (archive has `type`, NRT lacks `type`, drops 0.5% MODIS and 3.2% VIIRS industrial/offshore) | Verified in P02; report's ">80%" drops 65% of MODIS and breaks on VIIRS strings |
| Clustering | ST-DBSCAN per sensor family: spatial eps 2,700 m (haversine), temporal eps 24 h, min points 2 (counts the point itself) | event = cluster; noise points (label -1, ~5.7% MODIS, ~2.7% VIIRS) dropped, counted in manifest |
| Event time | start timestamp UTC; month = UTC calendar month of the start | D-05 |
| H3 | resolutions 5, 6, 7 stored; map uses 7 at high zoom | |
| Calibration unit | district (ADM2) if mean monthly MODIS events in the overlap >= 3, otherwise parent division (ADM1) | min_mean_monthly_modis = 3 |
| Overlap | months where both MODIS and VIIRS S-NPP have complete data: **2012-02 through 2026-10** (177 complete calendar months) | Verified in P02 (VIIRS S-NPP started 2012-01-20) |
| Harmonization | equal-n quantile mapping per calibration unit and pooled calendar-month group (month-1, month, month+1) vs a ratio baseline; chosen per unit by leave-one-year-out CV RMSE | |
| Harmonized record | MODIS-equivalent: months before the overlap use raw MODIS, months in and after the overlap use calibrated VIIRS | |
| Cell-level values | proportional downscaling: cell harmonized = cell raw VIIRS x (unit harmonized / unit raw VIIRS); sum over cells equals the unit total | |
| Aggregation up | division and country values are the sum of their districts (bottom-up, additive) | |
| Climatology baseline | all complete years except the evaluated year, per calendar month; percentiles p50, p90, p95 (numpy linear) | |
| Anomaly | value > p95 extreme; > p90 elevated; else normal; also percentile rank | |
| Fire season | smallest circular run of consecutive calendar months holding at least 70% of the mean annual total; start, peak, end | |

## 6. Decisions that differ from the research report

| ID | Report said | We do | Why |
| --- | --- | --- | --- |
| D-01 | Quantile mapping per H3 cell and month | Quantile mapping per district or division, then proportional downscaling to cells | A cell-month has only about 14 overlap samples, mostly zeros; the CDF is unstable. Regions have enough data and totals stay consistent |
| D-02 | Text-to-SQL inside the assistant | Typed tools only; the model never writes SQL | Safer, deterministic, easier to cite |
| D-03 | Filter MODIS/VIIRS confidence "> 80%" | MODIS >= 30, VIIRS n/h | Confidence scales differ; keep nominal and high detections |
| D-04 | GeoParquet | Plain Parquet with lat/lon and H3 columns | No geometry operations are needed at query time |
| D-05 | Not specified | Event month = UTC month of the event start | Simple, documented |
| D-06 | Global scale | Bangladesh scale; same code runs for any bbox | Fits the 2-day event |
| D-07 | Gemini 1.5 Pro | Provider adapter with `LLM_MODEL` env (VERIFY current model ids) plus a labelled replay mode | Model names change; demo must not depend on one API |
| D-08 | FIRMS country endpoint for bulk data | FIRMS archive download requests (and the area API in short windows as fallback) | The country route is reported unreliable (VERIFY) |
| D-09 | Single VIIRS record | S-NPP only for calibration; NOAA-20/21 only for NRT or sensitivity | The number of VIIRS satellites changed over time (2012, 2018, 2023) which would change counts |

## 7. Scientific honesty (must appear on the methodology page)

- Active-fire counts are not burned area. Harmonized counts are "MODIS-equivalent fire events", not hectares.
- The calibration assumes the MODIS-VIIRS relationship observed in 2012-present also holds before 2012 (it cannot be tested there).
- MODIS is itself not homogeneous: Aqua joined Terra in mid-2002, and Terra/Aqua orbits have drifted. We report this as a limitation and test sensitivity if time allows.
- Cloud, smoke and underground fires are under-detected by both sensors.
- Harmonization quality is measured by agreement over the overlap period (leave-one-year-out CV), not by the absence of change; real trends can remain.
- Alerts and guidance are advisory, not an official warning system.
- Attribution: "We acknowledge the use of data and/or imagery from NASA's Fire Information for Resource Management System (FIRMS)" (VERIFY the exact text on the FIRMS site); basemap and boundary data attributions as required.

## 8. Non-goals

User accounts, global coverage, burned-area product, model training, Text-to-SQL, mobile app, paid services beyond a free LLM tier, claims of official emergency authority.
