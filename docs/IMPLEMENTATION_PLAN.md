# Master implementation plan (PyroScope)

Live task board. Agents and humans update it as work happens.

## How to use this file (agents: read carefully)

- Status: `[ ]` not started, `[~]` in progress (put `@handle` in Owner), `[x]` done.
- **Claim before coding**: edit only your own row (`[ ]` -> `[~]` + handle), commit `chore(plan): claim <ID>`, push.
- Each chunk file has task checkboxes. Tick them as you go. When all are ticked and tests pass, set your row to `[x]`.
- A chunk may start only when every "Depends" ID is `[x]` (or the human approves a stub or fixture) and its Window is open.
- Window `PRE`: allowed any time before the event (no project application code; see P00). Window `EVENT`: starts Nov 14 at 09:00 local time unless `docs/RULES_CHECK.md` says earlier work is allowed.
- Priority: P0 required for the demo, P1 only after all P0, P2 stretch.
- Never reorder or rename rows or edit someone else's row. Keep edits to one line. Record deviations in the log at the bottom (append only).

Read order for any chunk: `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/DB_SCHEMA.md`, `docs/PRODUCT_BRIEF.md`, `docs/API_REFERENCE.md`, then the chunk file.

## Pre-event (Nov 9-13)

| Status | ID | Title | Pri | Window | Depends | Est h | Chunk file | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [x] | P00 | Lead setup: rules check, accounts, keys, tool install | P0 | PRE | none | 2 | plan/pre/P00-lead-setup.md | @azmaeenmahtab |
| [x] | P01 | Acquire historical FIRMS archives (MODIS, VIIRS S-NPP) | P0 | PRE | P00 | 3 | plan/pre/P01-data-acquisition.md | @azmaeenmahtab |
| [x] | P02 | Explore data and verify the report's claims | P0 | PRE | P01 | 3 | plan/pre/P02-data-exploration.md | @adityasaha03 |
| [x] | P03 | Region catalog and boundaries (reference data) | P0 | PRE | P00 | 2 | plan/pre/P03-regions-reference.md | @Aragon |
| [x] | P04 | Three tech spikes (deck.gl H3, DuckDB, LLM tools) | P0 | PRE | none | 4 | plan/pre/P04-tech-spikes.md | @Aragon |
| [x] | P05 | UX design pass (wireframes, tokens, copy) | P0 | PRE | none | 3 | plan/pre/P05-design.md | @adityasaha03 |

## Shared

| Status | ID | Title | Pri | Window | Depends | Est h | Chunk file | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [x] | S00 | Repo bootstrap (monorepo, Python and web tooling, CI) | P0 | EVENT | P00 | 2 | plan/shared/S00-bootstrap.md | @azmaeenmahtab |
| [x] | S01 | Contract first: OpenAPI, examples, deterministic fixtures, mocks | P0 | EVENT | S00 | 3 | plan/shared/S01-contracts-fixtures.md | @azmaeenmahtab |
| [x] | S02 | Deployment and data shipping | P0 | EVENT | A01, F01 | 3 | plan/shared/S02-deploy.md | @Aragon |

## Data lane (pipeline/)

| Status | ID | Title | Pri | Window | Depends | Est h | Chunk file | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [x] | D01 | Ingest and normalize FIRMS CSVs | P0 | EVENT | S00, P01 | 3 | plan/data/D01-ingest.md | @azmaeenmahtab |
| [x] | D02 | ST-DBSCAN engine (pure) | P0 | EVENT | S00 | 3 | plan/data/D02-st-dbscan.md | @adityasaha03 |
| [x] | D03 | Build fire events and H3 index | P0 | EVENT | D01, D02, P03 | 3 | plan/data/D03-events.md | @adityasaha03 |
| [x] | D04 | Monthly cell and region tables | P0 | EVENT | D03 | 2 | plan/data/D04-aggregate.md | @anamraiyan |
| [x] | D05 | Harmonization engine (pure): quantile mapping, ratio, CV | P0 | EVENT | S00 | 3 | plan/data/D05-harmonize-engine.md | @Aragon |
| [x] | D06 | Run harmonization, downscale to cells, validation report | P0 | EVENT | D04, D05 | 4 | plan/data/D06-harmonize-run.md | @anamraiyan |
| [~] | D07 | Climatology, anomalies, seasons, yearly stats | P0 | EVENT | D06 | 3 | plan/data/D07-calendar-stats.md | @Aragon |
| [ ] | D08 | NRT incremental update and provisional flags | P1 | EVENT | D03, D07 | 4 | plan/data/D08-nrt-update.md | |

## API lane (services/api/)

| Status | ID | Title | Pri | Window | Depends | Est h | Chunk file | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [~] | A01 | API foundation, data loading, meta and areas | P0 | EVENT | S01 | 2 | plan/api/A01-foundation.md | @Aragon |
| [~] | A02 | Heatmap and series endpoints | P0 | EVENT | A01 | 3 | plan/api/A02-heatmap-series.md | @Aragon |
| [~] | A03 | Calendar, yearly stats, anomalies, methodology | P0 | EVENT | A01 | 4 | plan/api/A03-calendar-stats.md | @Aragon |
| [ ] | A04 | Alert subscriptions and evaluation | P1 | EVENT | A03, D08 | 4 | plan/api/A04-alerts.md | |
| [x] | A05 | Ask PyroScope agent (typed tools, replay mode) | P0 | EVENT | A03 | 5 | plan/api/A05-ask-agent.md | @adityasaha03 |
| [x] | A06 | Guidance and Wildland Action Planner | P1 | EVENT | A03 | 3 | plan/api/A06-guidance.md | @adityasaha03 |

## Web lane (apps/web/)

| Status | ID | Title | Pri | Window | Depends | Est h | Chunk file | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [x] | F01 | Next.js foundation, shell, API client, mocks | P0 | EVENT | S01, P05 | 2 | plan/web/F01-foundation.md | @Aragon |
| [x] | F02 | Hex map (MapLibre + deck.gl H3) | P0 | EVENT | F01 | 4 | plan/web/F02-map.md | @Aragon |
| [x] | F03 | Area selection and URL state | P0 | EVENT | F01 | 3 | plan/web/F03-area-selection.md | @Aragon |
| [x] | F04 | FireCalendar and the hidden-jump chart | P0 | EVENT | F03 | 5 | plan/web/F04-calendar-series.md | @Aragon |
| [x] | F05 | Yearly stats, guidance and action planner UI | P1 | EVENT | F04 | 3 | plan/web/F05-stats-guidance.md | @Aragon |
| [x] | F06 | Alerts UI | P1 | EVENT | F03 | 3 | plan/web/F06-alerts-ui.md | @Aragon |
| [x] | F07 | Ask PyroScope chat UI | P0 | EVENT | F01 | 4 | plan/web/F07-ask-ui.md | @Aragon |
| [x] | F08 | Methodology and transparency page | P0 | EVENT | F01 | 3 | plan/web/F08-methodology.md | @Aragon |
| [x] | F09 | Polish, accessibility, performance | P1 | EVENT | F02-F08 | 3 | plan/web/F09-polish.md | @Aragon |

## Deliver

| Status | ID | Title | Pri | Window | Depends | Est h | Chunk file | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [ ] | X01 | Submission package (README, summary, video, deck sync, AI disclosure) | P0 | EVENT | all P0 | 4 | plan/deliver/X01-submission.md | |
| [ ] | X02 | Final QA, demo rehearsal, offline fallback | P0 | EVENT | all P0 | 3 | plan/deliver/X02-qa-rehearsal.md | |

## Suggested lanes (6 people; assign by strengths)

| Lane | Focus | Chunks |
| --- | --- | --- |
| 1 | Data engineering A | P01, P02, D01, D02, D03, D08 |
| 2 | Data science B | P03, D04, D05, D06, D07 |
| 3 | API and AI | A01, A02, A03, A05, A04, A06 |
| 4 | Frontend map and calendar | F01, F02, F03, F04 |
| 5 | Frontend rest and design | P05, F05, F06, F07, F08, F09 |
| 6 | Lead, QA, release, pitch | P00, P04, S00, S01, S02, X01, X02 |

## Schedule (Dhaka time, UTC+6; confirm the local event schedule with your Local Lead)

| When | Target |
| --- | --- |
| Nov 9 | P00 (rules check, accounts), P01 requests submitted, everyone installs tools and reads the docs |
| Nov 10-12 | P01 downloads, P02 findings, P03, P04 spikes, P05 design; update docs with real numbers |
| Nov 13 | Read the Project Submission Guide and Judging Guide (released today); fill `docs/RULES_CHECK.md`; dry-run the chunk loop on a tiny task |
| Nov 14, 09:00 | Kickoff: S00 (2h), S01 (3h). Then in parallel D01, D02, D05, A01, F01 |
| Nov 14, evening | Target: D03, D04 done; real hexes on the map (A02, F02); area selection (F03); API skeleton deployed (S02 draft) |
| Nov 15, 09:00-13:00 | D06, D07, A03, F04, A05, F07, F08; then **13:00 feature freeze** (P0 bugs only) |
| Nov 15, 13:00-18:00 | S02 final deploy, X01 package, video recording, X02 rehearsal |
| Nov 15, 18:00 | First complete submission; verify it opens and the receipt shows |
| Nov 15, 23:59 | Hard cutoff (local time). Never wait for the last hour |

## Deviation Log (append only: date, chunk, what, why, impact)

- 2026-11-11, P02: Replaced research report draft estimates (3,029 vs 10,972 annual fires; "3 to 7 times") with empirical figures from raw FIRMS data (MODIS raw ~9,645, VIIRS raw ~39,193; raw ratio 4.10x, filtered ratio 3.77x; ST-DBSCAN physical fire events ~560 vs ~860, ratio 1.5x; overlap window 2012-02 to 2026-10). Impact: ensures scientific accuracy in pitch, methodology page, and algorithm parameters.
- 2026-11-11, P02: Confirmed that NRT CSVs lack the `type` column present in archive CSVs. Impact: pipeline ingest must treat missing `type` as NaN rather than failing or dropping rows.
- 2026-11-11, P04: Verified and pinned exact tech stack versions in `docs/ARCHITECTURE.md` and `docs/SPIKE_RESULTS.md`: `@deck.gl/*@9.4.1` (`@deck.gl/mapbox` `MapboxOverlayProps`), `react-map-gl@8.1.3`, `maplibre-gl@^5.24.0` (avoids v6 bundler worker changes), `h3-js@4.5.0`, `d3-color@3.1.1` alongside `d3-scale-chromatic@3.1.1`, `duckdb@2.0.0` (requires `CAST(year AS INTEGER) * 100 + month` to avoid `INT16` multiplication overflow), and `google-genai>=2.30.1` Interactions API (`client.interactions.create`) with `gemini-3.8-flash` and keyless CARTO Dark Matter / OpenFreeMap dark basemap URLs. Impact: removes integration and runtime risk for F02, A02, and A05.
- 2026-11-11, P03: Built `data/reference/` (`regions.geojson`, `regions.parquet`, `region_cells.parquet`, `SOURCES.md`) from geoBoundaries v6.0.0 (`gbOpen`, commit `9469f09`, BBS/UN OCHA CC BY 3.0 IGO & CC0 1.0). Empirical H3 r7 cell count across the 64 districts is 26,683 (25,020 strict centroid-in-polygon + 1,663 deduplicated border/coastal-overlapping cells) rather than the rough 28k-30k estimate because mean H3 r7 cell area at Bangladesh's ~24°N latitude is 5.721 km² (vs 5.161 km² global average) over 140,052 km² of ADM2 land polygon area; including deduplicated border-overlap cells guarantees 100% of in-country FIRMS detections map to a unique district cell per `DB_SCHEMA.md` invariant.

- 2026-11-11, A01/A02: Correction by @Aragon. Rows set back to `[~]` because two boxes had been ticked without verification: A01 "Dockerfile stub builds" (Docker not installed locally, never built) and A02 "Timing measured on real data" (no real processed data exists yet; the earlier "sub-15 ms" figure was not measured). Also updated `contracts/openapi.yaml` and `docs/API_REFERENCE.md`, which had not been changed when `/api/health` gained `dataLoaded`/`dataVersion` and `/api/heatmap` gained `res`/`metric`/`from`/`to`. Code on main is unchanged and its tests pass. Impact: none of the features are blocked; the rows can return to `[x]` after a Docker build check and a real-data timing run.
- 2026-11-11, A03: Implemented calendar, yearly stats, anomalies, and methodology for named regions and presets using fixtures; custom-bbox on-the-fly statistics deferred per user decision 1.(a) until D07 stats engine lands. Kept row as [~] per decision 2 so we return to finish custom bbox once D07 is merged.
- 2026-11-11, D04: Verified and confirmed VIIRS S-NPP first complete calendar month is 2012-02 (earliest detection 2012-01-20), and latest complete month is 2026-10 (November 2026 is partial, handled by D08). MODIS coverage spans 2000-11 through 2026-10 (312 months), VIIRS spans 2012-02 through 2026-10 (177 months). Generated 31,296 dense district-months across all 64 districts and 27,494 sparse cell-months with 100% invariant consistency. Impact: establishes dense baseline tables for D06 quantile-mapping harmonization.
- 2026-11-11, D06: Run harmonization on real dataset (109,246 events). 61 of 64 districts fell back to parent division due to mean monthly MODIS < 3 (only Bandarban, Khagrachari, Rangamati calibrated directly). 1 unit (Barishal division) chose QM while 10 units chose Ratio based on LOYO CV RMSE. Country jump reduced from 1.85x naive splice to 0.86x harmonized with 0 unallocated cell events. Impact: produces harmonized tables for D07 calendar stats.
