# F05 Yearly stats, guidance and action planner UI

Depends: F04. Priority: P1. Window: EVENT. Read first: API_REFERENCE.md `/api/stats/yearly`, `/api/guidance`.

## Goal
Yearly area-wise burn statistics and sourced preparedness checklists beside the calendar.

## Files (`apps/web/src/features/stats/` and `features/guidance/`)
`stats/components/{yearly-table.tsx,yearly-bars.tsx,rank-badge.tsx}`, `stats/api/use-yearly-stats.ts`; `guidance/components/{action-planner.tsx,checklist.tsx,stage-badge.tsx,guidance-disclaimer.tsx}`, `guidance/api/use-guidance.ts`.

## Specification
- Yearly table: year, harmonized total, FRP sum, rank, percent versus the mean of other years, peak month; sortable; a bar chart of totals with the current year highlighted. Label units "MODIS-equivalent fire events".
- Action planner: shows the stage for the current month (pre-season, in season, post-season, extreme, off season), checklist items grouped by audience (community, land manager, responder), each with its source link and a "not yet verified" label when `verified` is false; a printable view; the advisory disclaimer is always visible.
- Plain text only; no HTML from the API.

## Tasks
- [ ] Yearly table and bars with tests (sort order, rank badge)
- [ ] Action planner with unverified labels and disclaimer (RTL test)
- [ ] Master plan row F05 set to `[x]`
