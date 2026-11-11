# F04 FireCalendar and the hidden-jump chart

Depends: F03. Priority: P0. Window: EVENT. Read first: API_REFERENCE.md `/api/calendar`, `/api/series`; PRODUCT_BRIEF.md section 4; `docs/design/`.

## Goal
The core of the pitch: a years x months calendar with anomaly flags and the fire season, and the chart that shows the artificial 2012 jump disappearing after harmonization.

## Files (`apps/web/src/features/calendar/` and `features/series/`)
`calendar/components/{fire-calendar.tsx,calendar-cell.tsx,season-band.tsx,month-detail-drawer.tsx,climatology-strip.tsx}`, `calendar/api/use-calendar.ts`; `series/components/{series-chart.tsx,series-toggles.tsx,overlap-marker.tsx,jump-caption.tsx}`, `series/api/use-series.ts`; each feature with `types.ts` and `index.ts`.

## Specification
- **FireCalendar**: grid with years as rows (2000 to latest) and months as columns; cell color from a sequential ramp on the harmonized value (domain per area from the climatology p95); anomaly marks: `elevated` outline, `extreme` bold outline plus a small icon (never color alone); provisional months hatched; the fire season band highlights its months in the column header; tooltip and click open a drawer with the value, percentile rank, climatology (mean, p50, p90, p95), and the class in words.
- **Climatology strip** beneath: bars for the monthly mean with p90 and p95 ticks.
- **SeriesChart** (Recharts): lines for raw MODIS, raw VIIRS, naive splice, harmonized with toggles (default: all on for the demo, and a "story mode" button that steps: raw only, then harmonized). Vertical marker at the first overlap month ("VIIRS era begins"). `jump-caption` shows the `naive_ratio` and `harmonized_ratio` from `/api/methodology` in plain words ("Without harmonization, annual counts after 2012 are N times higher than before; after harmonization the ratio is M"), only when the values exist.
- Accessibility: calendar is a real table with headers; each cell has an `aria-label` ("March 2020, 18 events, extreme"); the chart has a text summary and a data table toggle.
- Plain-language toggle (P1) switches explanatory captions only.

## Tests
- [x] Calendar renders the fixture (alpha): season band on April-June, 2020 May cell marked `extreme`
- [x] Series chart shows the fixture splice jump of about 3x between 2011 and 2012 for raw VIIRS and no jump for harmonized (assert from the data passed to the chart helper function, not from pixels)
- [x] Provisional months hatched; empty and error states
- [x] Keyboard navigation reaches every calendar cell

## Tasks
- [x] Calendar, drawer, climatology strip
- [x] Series chart, toggles, story mode, jump caption
- [x] Both views driven by `use-view-state` area
- [x] Master plan row F04 set to `[x]`
