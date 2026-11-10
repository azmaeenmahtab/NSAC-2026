# F02 Hex map (MapLibre + deck.gl H3)

Depends: F01. Priority: P0. Window: EVENT. Read first: `docs/SPIKE_RESULTS.md` (spike A) and the current deck.gl `H3HexagonLayer` and react-map-gl docs. Do not write those APIs from memory.

## Goal
An interactive 2D and 3D hexagon map of fire density for the selected area and period, built on the pattern proven in spike A.

## Files (`apps/web/src/features/map/`)
`components/{fire-map.tsx,map-controls.tsx,legend.tsx,hex-tooltip.tsx,time-range.tsx,metric-toggle.tsx}`, `api/use-heatmap.ts`, `hooks/use-map-viewport.ts`, `lib/{layer.ts,resolution.ts}`, `types.ts`, `index.ts`.

## Specification
- Client-only component (dynamic import with `ssr: false` if the docs or spike require it). Base map style from `NEXT_PUBLIC_BASEMAP_STYLE_URL` with attribution displayed.
- Layer: `H3HexagonLayer` with `getHexagon = d.h3` (hex string), `getFillColor` from the Inferno scale (domain from API `stats.p95`, values above clipped), `extruded` toggle with `getElevation` proportional to value (scale from the legend), pickable cells, transitions kept short.
- Resolution by zoom (`lib/resolution.ts`): zoom below 6 uses `res=5`, 6 to 8 uses `res=6`, 8 and above uses `res=7` (tune with spike numbers; VERIFY visually); the viewport bbox is debounced (300 ms) before requesting.
- Controls: metric toggle (`harmonized`, `raw_modis`, `raw_viirs`), time range (month range picker with defaults to the last 12 complete months, from API `meta`), 2D/3D toggle, reset view.
- Interaction: hover tooltip (hex id short, value, period); click selects the cell and writes `cell=<hex>` to the URL (F03 owns URL state; this feature calls the shared setter); selected cell is outlined.
- Legend with units: "MODIS-equivalent fire events per cell per selected period" for harmonized, event counts for raw metrics.
- Performance: at least 30 fps while panning with 30,000 cells on a mid-range laptop (measure with the browser performance tools and note in the PR); cancel in-flight requests when the viewport changes.
- Accessibility: a text summary above the map (highest cell value and location name if available), keyboard focus on controls, no information carried by color alone in the legend.

## Tasks
- [ ] Map renders fixture hexes with the mock API
- [ ] Controls, legend, tooltip, selection
- [ ] Debounced viewport requests with cancellation; resolution by zoom
- [ ] Measured fps and request timings in the PR
- [ ] RTL tests for legend, controls and the resolution function (zoom 5 -> 5, 7 -> 6, 9 -> 7 boundaries)
- [ ] Master plan row F02 set to `[x]`
