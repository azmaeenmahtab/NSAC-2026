# PyroScope Wireframes & UX Layout Specification

This document provides the complete wireframe layouts, ASCII blueprints, information architecture, interaction flows, and responsive specifications for the **PyroScope** web application (NASA Space Apps Challenge 2026).

Vector SVG wireframes for all 6 screens are rendered in [`docs/design/wireframes/`](file:///e:/NSAC-2026/docs/design/wireframes/):
1. **Screen 1**: [Main Mission Control Dashboard](file:///e:/NSAC-2026/docs/design/wireframes/screen1-main.svg)
2. **Screen 2**: [The "Hidden Jump" Calibration Diagnostic](file:///e:/NSAC-2026/docs/design/wireframes/screen2-hidden-jump.svg)
3. **Screen 3**: [Ask PyroScope Grounded Assistant](file:///e:/NSAC-2026/docs/design/wireframes/screen3-ask-panel.svg)
4. **Screen 4**: [Scientific Methodology & Diagnostic Transparency](file:///e:/NSAC-2026/docs/design/wireframes/screen4-methodology.svg)
5. **Screen 5**: [Early Warning Alerts & Wildland Action Planner](file:///e:/NSAC-2026/docs/design/wireframes/screen5-alerts-guidance.svg)
6. **Screen 6**: [Mobile Viewport Layout](file:///e:/NSAC-2026/docs/design/wireframes/screen6-mobile.svg)

---

## Screen 1: Main Mission Control Dashboard

### Layout Strategy
- **Split Screen**: Desktop displays a high-performance interactive deck.gl map on the left (65% width) and a dense analytical side panel on the right (35% width).
- **Synchronized State**: Panning/zooming the map or selecting an administrative boundary updates the side panel FireCalendar and series in real time via URL query params (`?area=PRESET-CHT&metric=harmonized`).

### ASCII Wireframe
```
+-----------------------------------------------------------------------------------------------------------------------+
| [🔥 PyroScope] [NASA Space Apps]  Area: [Chittagong Hill Tracts ▾]  Range: [2000-11 – 2026-10]  Metric: [Harmonized|MODIS|VIIRS] [Nav] |
+---------------------------------------------------------------------------------------------------+-------------------+
|                                                                                                   | FIRECALENDAR      |
|  [MAP VIEWPORT (MapLibre + deck.gl H3HexagonLayer)]                                              | Area: CHT Preset  |
|                                                                                                   | Season: Mar–May   |
|                                                                                                   +-------------------+
|     +-------------------------+                                     [+ - 3D R7] (Map Controls)    | [384 Events] Normal|
|     | Bangladesh Landmass     |                                                                   | [97.2%] In-Season |
|     |                         |                                                                   | [April] Peak Risk |
|     |        +--------------+ |                                                                   +-------------------+
|     |        | CHT PRESET   | |   [Hover Tooltip]                                                 | ANOMALY MATRIX    |
|     |        | [876428...]  | |   H3: 87642825fffffff                                             | J F M A M J J A...|
|     |        | ⬡ ⬡ ⬡ (Inferno)| |   District: Rangamati                                             | 2024: . . ▲ ◆ . . |
|     |        |   ⬢ ⬢ (Hot)  | |   Harmonized: 42.8 events                                         | 2023: . . . ▲ . . |
|     |        +--------------+ |   FRP: 184 MW                                                     | Keys: ● ▲ ◆       |
|     +-------------------------+                                                                   +-------------------+
|                                                                                                   | TIME SERIES TREND |
|                                                                                                   |   /\    Baseline  |
|                                                                                                   |  /  \--- -------  |
|                                                                                                   +-------------------+
|  [Inferno Density Legend: 0 ----------------- 15 -------- 75 ----------- 300+ fires/mo]           | [💬 Ask Assistant]|
+---------------------------------------------------------------------------------------------------+-------------------+
| NASA FIRMS MODIS/VIIRS Attribution | geoBoundaries CC BY 3.0 | Advisory Decision Support Notice                       |
+-----------------------------------------------------------------------------------------------------------------------+
```

---

## Screen 2: The "Hidden Jump" Calibration Diagnostic View

### Layout Strategy
- Dedicated pitch and scientific validation view.
- Multi-series chart contrasting **Raw MODIS**, **Raw VIIRS**, the deceptive **Naive Splice** (which exhibits a spurious 400% surge at 2012 due to 375m pixels), and the continuous **PyroScope Harmonized Line**.

### ASCII Wireframe
```
+-----------------------------------------------------------------------------------------------------------------------+
| [🔥 PyroScope] [The "Hidden Jump": Why Naive Satellite Splicing Misleads]                              [Nav Links...] |
+-----------------------------------------------------------------------------------------------------------------------+
|  [ +311% Jump (Naive Splice) ]   [ 4.10x Pixel Ratio (Raw) ]   [ 1.54x Event Ratio (DBSCAN) ]   [ 0% Fake Surge (Calibrated) ]|
+-----------------------------------------------------------------------------------------------------------------------+
|  ANNUAL ACTIVE-FIRE COUNT (2000–2026)                               [Legend: - Naive Splice  -- VIIRS  ·· MODIS  ━ Harmonized]|
|  40k |                                                        --- - - - - [Raw VIIRS (375m)]                          |
|      |                                                       /                                                        |
|  30k |                                                      /  (Deceptive +311% Jump)                                 |
|      |                                                     /                                                          |
|  20k |                                                    /                                                           |
|      |                                                   /                                                            |
|  10k | · · · · · · · · · · · · · · · · · · · · · · · · ·/· · · · · · · · · · [Raw MODIS (1km)]                        |
|      | ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ [PyroScope Harmonized Line]              |
|    0 +--------------------------------------------------|-------------------------------------------------------------+
|        2001   2003   2005   2007   2009   2011        2012 (VIIRS S-NPP Launch)     2018      2021     2024      2026   |
+-----------------------------------------------------------------------------------------------------------------------+
|  HOW PYROSCOPE HARMONIZES:                                                                                            |
|  [1. Low-Conf Filter] -> [2. ST-DBSCAN Clustering (2.7km/24h)] -> [3. Quantile Mapping] -> [4. Cell Downscaling]     |
+-----------------------------------------------------------------------------------------------------------------------+
```

---

## Screen 3: Ask PyroScope Grounded Assistant

### Layout Strategy
- **Split Audit Layout**: 60% Left pane dedicated to conversation and citations; 40% Right pane dedicated to real-time inspectable tool-call execution trace.
- **Architectural Guardrail**: Visual proof that the LLM invokes typed API queries against DuckDB and never writes arbitrary SQL.

### ASCII Wireframe
```
+-----------------------------------------------------------------------------------------------------------------------+
| [🔥 PyroScope] [Ask PyroScope Assistant]  [✓ Grounded by Typed Tools]                                 [Nav Links...] |
+-------------------------------------------------------------------+---------------------------------------------------+
| CONVERSATION STREAM                                               | TOOL EXECUTION INSPECTOR                          |
|                                                                   |                                                   |
|   [User Query Bubble]                                             | [✓] get_fire_season (14 ms)                       |
|   "When does fire season start in CHT, and was 2021 unusual?"     |     Args: { "area_id": "PRESET-CHT" }             |
|                                                                   |     Return: { start: 3, peak: 4, end: 5 }         |
|   [PyroScope Assistant Bubble] [Gemini 2.0] [● Replay Verified]   |                                                   |
|   Based on the 26-year harmonized record for PRESET-CHT:          | [✓] get_anomalies (18 ms)                         |
|   1. Season Window: March–May (accounts for 97.2% annual fires).  |     Args: { "area_id": "PRESET-CHT", year: 2021 } |
|   2. 2021 Anomaly: March 2021 was an EXTREME ANOMALY (◆)          |     Return: Month 3: 142 fires (98.4%ile, extreme)|
|      exceeding the 95th percentile baseline (142 vs 88 events).   |                                                   |
|                                                                   | [ARCHITECTURAL RULES]                             |
|   [Citations: Tool:get_fire_season | Tool:get_anomalies | v0.1.0] | • LLM never writes SQL                            |
|                                                                   | • LLM never extrapolates arithmetic               |
|   [Suggestions: "Was 2024 abnormal?" | "Compare Bandarban"]       | • Replay mode serves verified test fixtures       |
|   [Input: Ask a scientific question...               ] [Send]     |                                                   |
+-------------------------------------------------------------------+---------------------------------------------------+
```

---

## Screen 4: Scientific Methodology & Diagnostic Transparency

### Layout Strategy
- Clear visual breakdowns of:
  1. ST-DBSCAN spatio-temporal clustering mathematics ($\epsilon_s = 2,700\text{ m}$, $\epsilon_t = 24\text{ h}$).
  2. Quantile mapping transfer function curves ($F_{\text{MODIS}}^{-1}(F_{\text{VIIRS}}(x))$).
  3. Leave-one-year-out cross-validation error reduction table (QM vs simple ratio).
  4. Explicit scientific limitations and assumptions.

---

## Screen 5: Early Warning Alerts & Wildland Action Planner (P1)

### Layout Strategy
- Left: **Alerts Subscription Modal** allowing users to input email, select area, choose trigger condition (`Season Approaching`, `Above Normal`, or `Both`), and customize advance lead days.
- Right: **Wildland Action Planner** interactive checklist categorizing actions by seasonal fire stage:
  - **Pre-Season (Jan–Feb)**: Fuel breaks, pump inspections, controlled burn awareness.
  - **In-Season Peak (Mar–May)**: Vigilance, ban high-risk burns on low-humidity days, ridge lookouts.
  - **Post-Season (Jun–Aug)**: Mudslide mitigation, vetiver grass slope stabilization, fire scar review.

---

## Screen 6: Mobile Viewport Layout (390px)

### Layout Strategy
- Optimized for single-hand tactical field usage:
  - Top condensed header with quick preset pill.
  - Interactive map canvas supporting touch gestures (pan, pinch-to-zoom).
  - Floating density legend and real-time status chip.
  - Collapsible swipeable bottom sheet containing the FireCalendar matrix, anomaly badges, and action triggers.
  - Fixed bottom navigation bar with tap targets meeting 48px touch standards.

---

## Responsive Breakpoints & Device Targets

| Device Category | Viewport Width | Layout Mode | Side Panel Behavior |
| :--- | :--- | :--- | :--- |
| **Desktop / Pitch Display** | $\ge 1280\text{ px}$ | Split 65% Map / 35% Panel | Side panel permanently docked |
| **Tablet / Small Laptop** | $768\text{ px} - 1279\text{ px}$| Split 55% Map / 45% Panel | Collapsible side panel toggle |
| **Mobile Handheld** | $< 768\text{ px}$ | Single Column / Map Centric | Bottom sheet drawer (Swipe up to expand) |
