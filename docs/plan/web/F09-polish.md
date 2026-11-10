# F09 Polish, accessibility, performance (P1, after all P0 frontend chunks)

Depends: F02-F08. Priority: P1. Window: EVENT.

## Tasks
- [ ] Four-state audit (loading, empty, error, data) for every screen
- [ ] Keyboard navigation and focus order for map controls, calendar, dialogs; visible focus rings
- [ ] Color-blind check of the anomaly colors and map ramp; non-color cues present
- [ ] Responsive check at 390, 768 and 1280 px; bottom sheet panel on mobile
- [ ] Performance: lazy-load map and charts, measure the main route Lighthouse score and the map fps; record numbers in the PR
- [ ] Copy review against `docs/design/copy.md`: plain language, advisory and attribution texts present
- [ ] Demo helpers: a "Demo guide" dismissible card with the pitch steps; a `?demo=1` URL that sets the CHT preset and the story mode
- [ ] Master plan row F09 set to `[x]`
