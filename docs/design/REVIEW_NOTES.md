# P05 UX Design Review & Alignment Notes

This document records the alignment review for the **PyroScope** UX design pass (P05) between the frontend development teams (Lane 4: Map & Calendar, Lane 5: Rest & Design) and the pitch owner (240-second pitch flow).

---

## 1. Pitch Owner Review (240-Second Pitch Alignment)

The design directly maps to the pitch story articulated in [`PRODUCT_BRIEF.md`](file:///e:/NSAC-2026/docs/PRODUCT_BRIEF.md#L33-L44):

| Pitch Second | Story Beat | Target UI Component & Screen | Confirmed Design Element |
| :---: | :--- | :--- | :--- |
| **0 - 45s** | The "Hidden Jump" Problem | Screen 2: `HiddenJumpChart` | Purple naive splice line jumping +311% in 2012 due to 375m VIIRS pixels; callout cards showing raw 4.10x ratio. |
| **45 - 90s** | PyroScope Harmonization | Screen 2 & Screen 1 | Orange continuous harmonized line proving zero artificial surge; ST-DBSCAN physical event cluster explanation. |
| **90 - 150s** | CHT Preset & FireCalendar | Screen 1: `FireCalendarGrid` | Quick-select `PRESET-CHT`; visual March–May season bracket (97.2% annual fires); anomaly flags (March 2021 extreme ◆). |
| **150 - 195s** | Grounded AI Assistant | Screen 3: `AskPanel` & `ToolTimeline` | User asks about CHT fire onset; answer renders verified metrics with tool-call chips; replay badge active. |
| **195 - 225s** | Early Warning & Action | Screen 5: Alerts & Guidance | 14-day lead time notification modal and seasonal checklist for jhum farmers and forest rangers. |
| **225 - 240s** | Transparency & Closing | Screen 4: Methodology | Leave-one-year-out CV scores, limitations disclosure, and NASA FIRMS / geoBoundaries acknowledgements. |

---

## 2. Lane 4 Frontend Review (Map & Calendar: F01, F02, F03, F04)

- **MapLibre & deck.gl Integration**:
  - Confirmed 8-step Inferno color scale mapping (`#000004` to `#FCFFA4`) to maintain >30 FPS at 30,000 H3 resolution-7 cells.
  - Cell click pins H3 hex ID and syncs URL query parameters (`?area=...&cell=...`).
- **FireCalendar Grid**:
  - Confirmed CSS grid structure: 26 rows (2000–2026) by 12 columns (Jan–Dec).
  - Ensured non-color cues (`●`, `▲`, `◆`) are rendered inside cells alongside hex colors to guarantee full accessibility.
- **Hidden Jump Multi-line Chart**:
  - Recharts integration verified with four designated colors:
    - Raw MODIS: `#38BDF8` (Sky blue, dotted)
    - Raw VIIRS: `#F43F5E` (Rose, dashed)
    - Naive Splice: `#A855F7` (Purple, solid)
    - Harmonized: `#FF6B00` (Orange, thick solid glow)

---

## 3. Lane 5 Frontend Review (Design, Assistant & Docs: F05, F06, F07, F08, F09)

- **Ask PyroScope Component**:
  - Established dedicated tool execution inspector drawer on desktop to make typed tool calls visible and verifiable during live demos.
  - Clarified that all LLM outputs stream as plain text with citation pills at the foot.
- **Early Warning & Action Planner**:
  - Email notification form designed with simple SQLite-compatible fields (`email`, `area_id`, `rule`, `lead_days`).
  - Pre-season, in-season, and post-season stages directly bind to the rule-based checklist data in `guidance.json`.
- **Methodology & Diagnostics**:
  - Standardized display of leave-one-out cross-validation table comparing Quantile Mapping against the simple ratio baseline.

---

## 4. Design Sign-Off Summary

- **Design Tokens**: Standardized in `docs/design/tokens.md`.
- **Copy Deck**: Standardized in `docs/design/copy.md`.
- **Component Interface**: Defined in `docs/design/components.md`.
- **Wireframes**: 6 vector SVG wireframes delivered in `docs/design/wireframes/` and documented in `docs/design/wireframes.md`.
- **Result**: Frontend lanes have full visual, architectural, and textual specifications to build against without ambiguity.
