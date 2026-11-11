# API reference (FastAPI, base path /api)

The machine-readable contract is `contracts/openapi.yaml` (chunk S01 writes it first; web types and mocks are generated from it). Update both together. Success: `{ "data": ..., "meta": { "dataVersion": "...", "asOf": "YYYY-MM-DD" } }`. Error: `{ "error": { "code", "message", "requestId" } }`. H3 ids are lowercase hex strings. `area_id` is a region id or `bbox:<w>,<s>,<e>,<n>`.

| Method and path | Chunk | Purpose and key parameters |
| --- | --- | --- |
| GET /api/health | A01 | liveness; reports `dataLoaded` and `dataVersion` |
| GET /api/meta | A01 | data version, as-of date, provisional-from, parameters summary, sources, counts, attribution text |
| GET /api/areas | A01 | list presets and regions: id, name, level, parent, bbox, aliases; `?level=` filter |
| GET /api/heatmap | A02 | `bbox`, `from` (YYYY-MM), `to`, `metric` = `harmonized`\|`raw_modis`\|`raw_viirs`, `res` = 5\|6\|7. Returns `{ res, metric, from, to, cells: [{ h3, value }], stats: { min, max, p95 } }`; max 40,000 cells |
| GET /api/series | A02 | `area_id`, optional `from`/`to`. Monthly records: `raw_modis`, `raw_viirs`, `naive_splice` (MODIS before 2012-02 then VIIRS raw), `harmonized`, flags `in_overlap`, `source_used`, `provisional` |
| GET /api/calendar | A03 | `area_id`. Years x months grid of harmonized values with `class` (normal/elevated/extreme), `percentile_rank`; the climatology (mean, p50, p90, p95) per month; the fire season (start, peak, end, share) |
| GET /api/stats/yearly | A03 | `area_id`. Rows from `yearly`: total, FRP, rank, vs mean, peak month |
| GET /api/anomalies | A03 | `area_id`, optional `year`, `class` filter |
| GET /api/methodology | A03 | parameters, per-unit calibration report summary (CV metrics chosen method), Q-Q data points for display, jump metrics (before/after), limitations list |
| POST /api/ask | A05 | body `{ question (<=500), area_id?, style: "standard"\|"plain" }`. Returns `{ answer, citations: [{ tool, areaId, years, dataVersion }], toolCalls: [{ name, args, durationMs }], mode: "live"\|"replay" }` |
| GET /api/guidance | A06 (P1) | `area_id`, optional `month`, `stage`, `audience`. Rule-based checklist items with source info and `verified` flag |
| POST /api/alerts/subscriptions | A04 (P1) | `{ email, area_id, rule, lead_days }` -> sends a confirmation email |
| GET /api/alerts/subscriptions/confirm | A04 (P1) | `token` |
| DELETE /api/alerts/subscriptions | A04 (P1) | `token` (unsubscribe) |
| GET /api/alerts/active | A04 (P1) | `area_id`. Current alert state for display (season approaching, above normal) |

Rate limits: `/api/ask` 10 per minute per IP; `/api/alerts/subscriptions` 5 per hour per IP; everything else 120 per minute per IP. 429 includes `Retry-After`.

Jump metrics (in `/api/methodology`): `naive_ratio` = mean annual raw VIIRS-spliced series 2012-2016 divided by mean annual raw MODIS 2007-2011; `harmonized_ratio` = the same ratio computed on the harmonized series; plus `overlap_cv_rmse` and `overlap_cv_bias`. These describe the data; they do not claim to be a trend test.
