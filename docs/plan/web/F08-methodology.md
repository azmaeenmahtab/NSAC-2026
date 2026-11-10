# F08 Methodology and transparency page

Depends: F01. Priority: P0. Window: EVENT. Read first: API_REFERENCE.md `/api/methodology`; PRODUCT_BRIEF.md sections 5 to 7.

## Goal
Show the validity of the work: how harmonization works, the measured validation, parameters, data sources and honest limitations. This page carries the "Validity" criterion.

## Files (`apps/web/src/features/methodology/`)
`components/{method-steps.tsx,validation-summary.tsx,qq-chart.tsx,jump-metrics.tsx,parameters-table.tsx,sources-list.tsx,limitations.tsx}`, `api/use-methodology.ts`, `types.ts`, `index.ts`; page `app/methodology/page.tsx`.

## Specification
- Steps in plain language with a simple diagram: detections -> events -> monthly counts -> calibration -> calendar.
- Validation: country-level overlap CV (RMSE, bias, rank correlation), count of calibration units by method and by fallback, worst units flagged; Q-Q chart of VIIRS against MODIS before and after mapping; the jump metrics (`naive_ratio`, `harmonized_ratio`) with a sentence that these describe the data and do not prove the absence of real trends.
- Parameters table from the manifest; data counts (kept and dropped detections by reason); sources with versions and the required attribution; the data version and as-of date.
- Limitations list exactly as served by the API (from the brief): not burned area; pre-2012 relation assumed; MODIS inhomogeneity (Aqua from mid-2002, orbit drift); cloud, smoke and underground fires; advisory only.
- Every number comes from the API; no hard-coded results in the front end.

## Tasks
- [ ] Sections implemented with the mock data and then the real data
- [ ] Q-Q chart with accessible data table
- [ ] RTL tests: limitations always rendered, jump caption absent when metrics are missing
- [ ] Master plan row F08 set to `[x]`
