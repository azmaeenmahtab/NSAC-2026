# F03 Area selection and URL state

Depends: F01. Priority: P0. Window: EVENT. Read first: API_REFERENCE.md `/api/areas`; ARCHITECTURE.md section 5.

## Goal
Choose an area of interest (country, division, district, CHT preset, or a drawn bounding box) and keep the whole view shareable in the URL.

## Files (`apps/web/src/features/areas/`)
`components/{area-selector.tsx,bbox-draw.tsx,area-breadcrumb.tsx}`, `api/use-areas.ts`, `hooks/use-view-state.ts` (URL state), `lib/{url-state.ts,bbox.ts}`, `types.ts`, `index.ts`.

## Specification
- URL parameters: `area` (region id or `bbox:w,s,e,n`), `from`, `to` (YYYY-MM), `metric`, `cell`. `use-view-state` reads and writes them (Next.js `useSearchParams` and `router.replace` without scroll); invalid values fall back to defaults and are corrected in the URL.
- Selector: searchable list from `/api/areas` grouped by level (country, divisions, districts, presets), with the CHT preset pinned at the top; selecting an area fits the map to its bbox.
- Custom area: a draw-box tool on the map (two clicks or drag) producing `bbox:`; validate size limits matching the API (show the API error message if rejected); a clear-selection button.
- Breadcrumb: country > division > district for district selections.
- Other features read the state only through `features/areas` exports.

## Tests
- [x] URL round trip: state -> URL -> state is identity for valid values (include `bbox:88.1,21.5,92.6,26.4`)
- [x] Invalid `area` or reversed dates are corrected to defaults
- [x] `bbox.ts`: west >= east or out-of-range latitudes rejected; area size helper

## Tasks
- [x] Selector, draw tool, breadcrumb, URL state hook
- [x] Map fits to the selected area (coordinate with F02 through the shared state, not by importing internals)
- [x] Master plan row F03 set to `[x]`
