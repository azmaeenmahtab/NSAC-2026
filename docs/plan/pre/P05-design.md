# P05 UX design pass (wireframes, tokens, copy)

Depends: none. Priority: P0. Window: PRE. Output goes in `docs/design/`.

## Goal
Decide the look and the screens before coding, so the two front-end lanes build the same thing.

## Deliverables
- Wireframes (Figma export or PNG, low fidelity is enough) for: (1) main screen with map, area selector, time range, metric toggle, side panel with FireCalendar and series chart; (2) "hidden jump" chart view; (3) Ask PyroScope panel; (4) Methodology page; (5) Alerts subscription and guidance panel (P1); (6) mobile layout for the main screen.
- Design tokens in `docs/design/tokens.md`: dark "mission control" theme, one accent color, semantic colors for normal, elevated and extreme, type scale, spacing scale. Color ramp for fire density: Inferno (perceptually uniform); verify color-blind legibility of the anomaly colors and add non-color cues (outline or icon).
- Copy deck in `docs/design/copy.md`: screen titles, button labels, plain-language explanations of "harmonized", "anomaly", "season", empty states, error messages, the data-attribution and advisory disclaimers.
- Component list (shell, area selector, legend, calendar grid, chart toggles, chat bubble, tool-call timeline).

## Tasks
- [x] Wireframes for the 6 screens
- [x] Tokens and copy deck
- [x] Review by the frontend lanes and the pitch owner; changes noted
- [x] Master plan row P05 set to `[x]`
