# F09 Polish, accessibility, performance (P1, after all P0 frontend chunks)

Depends: F02-F08. Priority: P1. Window: EVENT.

## Tasks
- [x] Four-state audit (loading, empty, error, data) for every screen
- [x] Keyboard navigation and focus order for map controls, calendar, dialogs; visible focus rings
- [x] Color-blind check of the anomaly colors and map ramp; non-color cues present
- [x] Responsive check at 390, 768 and 1280 px; bottom sheet panel on mobile
- [x] Performance: lazy-load map and charts, measure the main route Lighthouse score and the map fps; record numbers in the PR
- [x] Copy review against `docs/design/copy.md`: plain language, advisory and attribution texts present
- [x] Demo helpers: a "Demo guide" dismissible card with the pitch steps; a `?demo=1` URL that sets the CHT preset and the story mode
- [x] Master plan row F09 set to `[x]`
