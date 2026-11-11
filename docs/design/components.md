# PyroScope Component Specifications

This document defines the functional contracts, TypeScript prop interfaces, state bindings, accessibility requirements, and keyboard interactions for the core frontend components across **Lane 4 (Frontend Map & Calendar)** and **Lane 5 (Frontend Rest & Design)**.

---

## 1. Application Shell (`AppShell` & `Header`)

### Purpose
Provides the dark "mission control" scaffolding, global navigation, status indicators (active data version, as-of date, NRT status), and preset area shortcuts.

### Component Structure
```
AppShell
├── Header
│   ├── LogoBadge ("PyroScope" + NASA Space Apps tag)
│   ├── AreaCombobox (quick select: CHT, BGD, Districts)
│   ├── GlobalDateRangePicker
│   ├── DataStatusPill ("Data as of 2026-10-31 | v1.0.0")
│   └── NavTabs (Map & Calendar | The Hidden Jump | Ask Assistant | Methodology)
└── MainContainer (Split Layout: 65% Interactive Map / 35% Analytical Side Panel)
```

### TypeScript Interface
```typescript
export interface HeaderProps {
  currentAreaId: string;
  onAreaChange: (areaId: string) => void;
  dateRange: { from: string; to: string }; // YYYY-MM
  onDateRangeChange: (range: { from: string; to: string }) => void;
  dataMeta: {
    dataVersion: string;
    asOf: string;
    isNrtActive: boolean;
  };
  activeTab: 'mission-control' | 'hidden-jump' | 'ask' | 'methodology';
  onTabChange: (tab: string) => void;
}
```

---

## 2. Area Selector (`AreaSelector` & `AreaCombobox`)

### Purpose
Allows instant switching between the national view (`BGD`), the high-risk `PRESET-CHT` (Chittagong Hill Tracts), administrative divisions (ADM1), districts (ADM2), or drawing a custom bounding box.

### Features
- **URL Synchronization**: Changes update `?area=BGD-ADM2-rangamati` in real-time.
- **Fast Fuzzy Search**: Matches both formal English spellings, aliases (e.g., `Chittagong` $\to$ `Chattogram`, `Hill Tracts` $\to$ `PRESET-CHT`).
- **Hierarchy Indicators**: Badges indicate `[Preset]`, `[Division]`, or `[District]`.

### TypeScript Interface
```typescript
export interface AreaOption {
  id: string; // e.g. "PRESET-CHT", "BGD-ADM2-bandarban", "bbox:91.8,21.5,92.5,22.4"
  name: string;
  level: 'country' | 'adm1' | 'adm2' | 'preset' | 'custom';
  parentName?: string;
  aliases: string[];
  bbox: [number, number, number, number]; // [minX, minY, maxX, maxY]
}

export interface AreaSelectorProps {
  selectedId: string;
  options: AreaOption[];
  onSelect: (area: AreaOption) => void;
  onCustomBBoxDraw?: () => void;
}
```

---

## 3. Map & Legend (`DeckGlHexMap` & `InfernoLegend`)

### Purpose
Renders up to 30,000 H3 resolution-7 cells on top of a dark MapLibre vector canvas using `@deck.gl/geo-layers` `H3HexagonLayer`.

### Features
- **Inferno Color Scale**: Visualizes density from step 0 (dark purple) to step 7 (blazing light yellow).
- **Interactive Tooltip**: Hovering over an H3 cell reveals:
  - H3 Index (Hex string)
  - Harmonized Event Count (or raw count if toggled)
  - Estimated Total Fire Radiative Power (MW)
  - Assigned District
- **Cell Click-to-Inspect**: Clicking a cell pins it and filters the side panel FireCalendar to that specific hexagon's temporal history.
- **3D Elevation Toggle**: Extrudes hexagons proportionally to FRP or event count.

### TypeScript Interface
```typescript
export interface HeatmapCell {
  h3: string; // 15-char lowercase hex e.g. "87642825fffffff"
  value: number; // harmonized event count
  frpMw?: number;
}

export interface DeckGlHexMapProps {
  cells: HeatmapCell[];
  metric: 'harmonized' | 'raw_modis' | 'raw_viirs';
  res: 5 | 6 | 7;
  is3d: boolean;
  selectedCellId?: string;
  onCellClick: (h3Index: string) => void;
  onCellHover: (cell: HeatmapCell | null, info?: { x: number; y: number }) => void;
}
```

---

## 4. FireCalendar Grid (`FireCalendarGrid`)

### Purpose
The signature analytical artifact: a dense 2D matrix of Years (rows: 2000–2026) $\times$ Months (columns: Jan–Dec).

### Features
- **Seasonal Highlight Band**: Columns representing the local fire season (e.g., March–May for CHT) feature a subtle ambient column glow and top header bracket (`[ Burning Season: 97% ]`).
- **Anomaly Badges**:
  - `●` Normal ($\le 90\text{th}$ percentile)
  - `▲` Elevated ($> 90\text{th}$ percentile, Amber)
  - `◆` Extreme ($> 95\text{th}$ percentile, Rose pulse)
- **Cell Hover / Focus**: Tooltip reveals exact harmonized count, baseline mean, baseline 95th percentile, and percentile rank.
- **Keyboard Navigation**: Full arrow-key grid navigation with ARIA grid semantics (`role="grid"`, `role="row"`, `role="gridcell"`).

### TypeScript Interface
```typescript
export interface CalendarCellData {
  year: number;
  month: number;
  harmonizedValue: number;
  anomalyClass: 'normal' | 'elevated' | 'extreme';
  percentileRank: number; // 0.00 to 1.00
  baselineMean: number;
  baselineP95: number;
}

export interface FireCalendarGridProps {
  areaId: string;
  areaName: string;
  cells: CalendarCellData[];
  season: {
    startMonth: number;
    peakMonth: number;
    endMonth: number;
    shareOfAnnual: number;
  };
  onCellSelect?: (year: number, month: number) => void;
}
```

---

## 5. "Hidden Jump" Diagnostic Chart (`HiddenJumpChart`)

### Purpose
Directly demonstrates the scientific necessity of PyroScope by plotting raw vs harmonized time series across the 2012 sensor transition.

### Rendered Series (Multi-Line Chart with Recharts)
1. **Raw MODIS (`#38BDF8`, dotted)**: Continuous 2000–2026, 1 km resolution.
2. **Raw VIIRS (`#F43F5E`, dashed)**: Begins Feb 2012, 375 m resolution (appears ~4.1x higher).
3. **Naive Splice (`#A855F7`, solid with sharp spike)**: Splicing raw MODIS then raw VIIRS at Jan 2012 shows a deceptive 400% jump.
4. **PyroScope Harmonized (`#FF6B00`, thick glowing line)**: Calibrated MODIS-equivalent series removing the artificial sensor jump.

### Interactivity
- Hover cursor with synchronized tooltip showing all 4 values for any given month.
- Toggle checkboxes to show/hide individual lines.
- Zoom range sliders (focusing on the 2011–2014 transition window).

---

## 6. Grounded Assistant Chat (`AskMessageBubble`)

### Purpose
Presents questions and answers from the "Ask PyroScope" agent.

### Features
- **Replay Badge**: Displays `[REPLAY MODE - Pre-Verified]` or `[LIVE GEMINI 2.0]` status.
- **Streaming Output**: Markdown text rendering with typewriter animation.
- **Evidence Chips**: Clickable references at the foot of each answer (`[Dataset: BGD-ADM2-rangamati | March 2021 | Tool: get_climatology]`).
- **No Hallucinations Guarantee**: Explanatory banner emphasizing that all numbers are retrieved via strictly typed tools directly from DuckDB.

---

## 7. Tool-Call Execution Timeline (`ToolCallTimeline`)

### Purpose
Renders expandable inspector cards detailing the exact tool calls made by the assistant, showing transparency and auditability.

### Visual Items
- **Tool Name**: `get_fire_season`, `get_anomalies`, `get_monthly_series`
- **Execution Time**: `e.g. 14ms (DuckDB Parquet View)`
- **Input Arguments**: JSON syntax-highlighted drawer
- **Output Return**: Typed numbers returned by the backend

---

## 8. Summary Component Matrix

| Component | Lane | File Location | Accessibility Target |
| :--- | :---: | :--- | :--- |
| `AppShell` | Lane 4 | `apps/web/src/features/shell/components/app-shell.tsx` | Landmark regions (`banner`, `main`, `complementary`) |
| `AreaSelector` | Lane 4 | `apps/web/src/features/areas/components/area-selector.tsx` | ARIA combobox pattern, Esc to dismiss, arrow keys |
| `DeckGlHexMap` | Lane 4 | `apps/web/src/features/map/components/deck-gl-hex-map.tsx` | Canvas accessible fallback description, keyboard zoom |
| `InfernoLegend` | Lane 4 | `apps/web/src/features/map/components/inferno-legend.tsx` | Labeled value gradients, text annotations |
| `FireCalendarGrid`| Lane 4 | `apps/web/src/features/calendar/components/calendar-grid.tsx`| ARIA `grid`, `rowheader`, `columnheader`, roving tabindex |
| `HiddenJumpChart` | Lane 4 | `apps/web/src/features/series/components/hidden-jump-chart.tsx`| SVG accessible titles, data table fallback |
| `AskPanel` | Lane 5 | `apps/web/src/features/ask/components/ask-panel.tsx` | `aria-live="polite"` for streaming assistant tokens |
| `ToolCallTimeline`| Lane 5 | `apps/web/src/features/ask/components/tool-timeline.tsx` | Accordion disclosure pattern, screen-reader details |
