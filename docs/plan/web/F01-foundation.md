# F01 Next.js foundation, shell, API client, mocks

Depends: S01, P05. Priority: P0. Window: EVENT. Read first: ARCHITECTURE.md sections 1, 5, 9; `docs/design/` (P05); the current Next.js, Tailwind and shadcn/ui setup docs.

## Goal
The app shell in the dark "mission control" theme with a typed API client, TanStack Query, MSW mocks and shared UI states, so every feature lane builds on the same base.

## Files (`apps/web/src/`)
- `app/layout.tsx`, `app/page.tsx` (composes the main screen), placeholder routes `app/methodology/page.tsx`, `app/ask/page.tsx` if used as pages; each under 40 lines
- `components/ui/*` shadcn primitives (button, card, tabs, dialog, sheet, select, input, badge, skeleton, tooltip, toggle-group, sonner)
- `components/layout/{app-shell.tsx,header.tsx,side-panel.tsx,attribution.tsx}`
- `components/feedback/{query-boundary.tsx,empty-state.tsx,error-state.tsx}`
- `lib/api/{client.ts,errors.ts,types.gen.ts}` (types generated from `contracts/openapi.yaml`), `lib/env.ts`, `lib/color/{scales.ts,legend.ts}`, `lib/format.ts` (numbers, months)
- `providers/{query-provider.tsx,theme-provider.tsx}`, `mocks/{browser.ts,handlers.ts}`
- `features/shell/` (header content, data-as-of badge, provisional badge)

## Specification
- Theme from `docs/design/tokens.md`: dark background, one accent, semantic colors for `normal`, `elevated`, `extreme`; Inferno ramp helpers (`d3-scale-chromatic`) with a quantile or clipped-linear domain using `p95` from the API.
- `client.ts`: `apiGet<T>(path, params)` with the success and error envelopes, `ApiError`, base URL from `NEXT_PUBLIC_API_URL`; when `NEXT_PUBLIC_USE_MOCKS=true`, MSW serves `contracts/examples`.
- `QueryBoundary` renders skeleton, empty, error (with retry) or children for every query.
- The header shows the data version, the as-of date (from `/api/meta`) and a "provisional data included" badge when `provisionalFrom` is set; the footer shows the NASA FIRMS acknowledgement and basemap attribution from `/api/meta`.
- Responsive shell: map area plus a resizable or collapsible side panel; at narrow widths the panel becomes a bottom sheet.

## Tasks
- [x] App generated and configured (Tailwind dark theme, shadcn initialised)
- [x] API client, types generation, mocks, query provider
- [x] Shell, header badges, attribution, query boundary
- [x] RTL tests: `QueryBoundary` states, header badge when `provisionalFrom` is present
- [x] `pnpm build`, `pnpm lint`, `pnpm typecheck` pass
- [x] Master plan row F01 set to `[x]`
