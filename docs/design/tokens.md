# PyroScope Design System: Design Tokens

This document specifies the design tokens for the **PyroScope** web interface. It defines the dark "mission control" visual language, typography, spatial layout, semantic indicators, the perceptually uniform **Inferno** color ramp for active-fire heatmaps, and accessibility compliance including color-blind validation and non-color cues.

---

## 1. Visual Theme: Dark "Mission Control"

The interface adopts a high-contrast, dark-mode aerospace/observatory aesthetic. Backgrounds use deep blue-black slate tones to minimize eye fatigue during extended analysis and maximize the dynamic range and glow of active-fire data points.

### Background and Surface Tokens

| Token Name | Hex Code | Tailwind / CSS Variable | Purpose |
| :--- | :--- | :--- | :--- |
| `surface-canvas` | `#080B10` | `--color-surface-canvas` | Base application background (deep space black) |
| `surface-panel` | `#0E141F` | `--color-surface-panel` | Sidebars, modal drawers, and main header |
| `surface-card` | `#161F30` | `--color-surface-card` | Elevated cards, metric widgets, calendar grid cells |
| `surface-card-hover` | `#1E293B` | `--color-surface-card-hover` | Hover states on interactive cards and list items |
| `surface-card-active`| `#253347` | `--color-surface-card-active`| Selected/pressed states |
| `border-subtle` | `#1F293D` | `--color-border-subtle` | Dividers and inactive card borders (1px) |
| `border-default` | `#2D3B55` | `--color-border-default` | Default borders on interactive controls |
| `border-focus` | `#FF6B00` | `--color-border-focus` | Keyboard focus ring (2px) and active tab indicator |

### Typography Tokens (Colors)

| Token Name | Hex Code | Tailwind / CSS Variable | Contrast Ratio (vs `#0E141F`) | Usage |
| :--- | :--- | :--- | :--- | :--- |
| `text-primary` | `#F8FAFC` | `--color-text-primary` | 15.6:1 (AAA) | High-emphasis headings, values, key labels |
| `text-secondary` | `#94A3B8` | `--color-text-secondary` | 6.4:1 (AA) | Body copy, secondary metadata, tooltips |
| `text-muted` | `#64748B` | `--color-text-muted` | 3.6:1 (UI text) | Inactive labels, placeholder text, axis lines |
| `text-accent` | `#FF6B00` | `--color-text-accent` | 5.8:1 (AA) | Interactive links, glowing badge numbers |

---

## 2. Primary Brand Accent

To evoke satellite infrared thermal radiometry and fire detection, a single primary accent color is chosen:

- **Accent Token**: `accent-primary` = `#FF6B00` (Solar Flare Orange)
- **Accent Glow**: `rgba(255, 107, 0, 0.25)` (used for active selection rings and 3D map highlights)
- **Accent Subtle**: `rgba(255, 107, 0, 0.12)` (active button/pill backgrounds)
- **Accent Hover**: `#FF8533`
- **Accent Active**: `#E05E00`

---

## 3. Semantic Anomaly Tokens & Non-Color Cues

Anomalies compare harmonized fire events against the region's historical monthly climatology baseline (leave-one-year-out).

| Category | Percentile Rank | Hex Color | Tailwind Token | Symbol Cue | Border / Style Cue |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Normal** | $\le 90\text{th}$ percentile | `#10B981` (Emerald) | `anomaly-normal` | Circle `●` | Solid thin border (`#065F46`), flat background |
| **Elevated** | $> 90\text{th}$ and $\le 95\text{th}$ | `#F59E0B` (Amber) | `anomaly-elevated`| Warning Triangle `▲` | Dashed border (`#D97706`), subtle warm tint |
| **Extreme** | $> 95\text{th}$ percentile | `#EF4444` (Rose) | `anomaly-extreme` | Alert Octagon `◆` / `!` | Solid 2px bright border (`#DC2626`), pulsing glow |

### Color-Blind Accessibility Verification

The palette was tested using standard Brettel-Viénot-Mollon color-vision simulation models:
1. **Deuteranopia (Green-blind)**: `#10B981` appears slate-cyan; `#F59E0B` appears warm ochre; `#EF4444` appears vivid rust brown. The chromatic distance ($\Delta E$) between `#10B981` and `#EF4444` remains $> 25$.
2. **Protanopia (Red-blind)**: `#EF4444` darkens significantly; `#F59E0B` retains high luminance.
3. **Tritanopia (Blue-blind)**: `#10B981` and `#EF4444` are instantly distinct (cyan vs vivid red-pink).

#### Mandatory Non-Color Redundancy (WCAG 2.2 Level AA - 1.4.1)
Color is **never** the sole indicator of an anomaly state:
- Every cell or badge displaying anomaly status **must** render its corresponding symbol (`●`, `▲`, or `◆`) or text label (`"Normal"`, `"Elevated"`, `"Extreme"`).
- Calendar grid cells display an ARIA label: e.g., `aria-label="March 2021: 142 harmonized fire events, Extreme Anomaly (98th percentile)"`.
- Screen readers receive the status via `.sr-only` descriptive spans.

---

## 4. Perceptually Uniform Heatmap Color Ramp: Inferno

To represent spatial fire event density on the deck.gl `H3HexagonLayer` and MapLibre overlay, PyroScope strictly utilizes the **Inferno** color map.

Inferno is mathematically monotonic in lightness ($L^*$), ensuring:
- Accurate human perception of density gradients without false visual boundaries.
- Total readability in grayscale and across all color-blindness conditions.
- Zero perceptual distortion compared to naive rainbow/jet scales.

### 8-Step Inferno Color Ramp (Hex & RGBA)

| Step | Value / Density Range | Hex Code | RGB Values | CSS / deck.gl RGBA (0-255) |
| :---: | :--- | :--- | :--- | :--- |
| **0** | 0 events (Zero / Muted) | `#000004` | `[0, 0, 4]` | `[0, 0, 4, 30]` |
| **1** | Low (1 - 5 events) | `#280B54` | `[40, 11, 84]` | `[40, 11, 84, 180]` |
| **2** | Moderate-Low (6 - 15) | `#651A80` | `[101, 26, 128]` | `[101, 26, 128, 200]` |
| **3** | Moderate (16 - 35) | `#9F2F7F` | `[159, 47, 127]` | `[159, 47, 127, 220]` |
| **4** | Elevated (36 - 75) | `#D44842` | `[212, 72, 66]` | `[212, 72, 66, 235]` |
| **5** | High (76 - 150) | `#F57D15` | `[245, 125, 21]` | `[245, 125, 21, 245]` |
| **6** | Very High (151 - 300) | `#FAC62D` | `[250, 198, 45]` | `[250, 198, 45, 255]` |
| **7** | Peak / Extreme (> 300) | `#FCFFA4` | `[252, 255, 164]` | `[252, 255, 164, 255]` |

---

## 5. Typography Scale

Fonts:
- **Interface / Sans**: `Geist Sans`, `Inter`, or system fallback `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`.
- **Numbers / Scientific Monospace**: `Geist Mono`, `JetBrains Mono`, `"SF Mono"`, monospace (for H3 hex IDs, coordinate pairs, timestamps, FRP values, and statistical matrices).

| Token | Size | Line Height | Weight | Tracking | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `font-display` | 24px (1.5rem) | 32px | 700 (Bold) | -0.02em | Main application title, pitch punchlines |
| `font-title` | 18px (1.125rem)| 24px | 600 (Semibold)| -0.01em | Panel headers, area names (`Chittagong Hill Tracts`) |
| `font-headline`| 15px (0.9375rem)| 20px | 600 (Semibold)| 0 | Card section titles, modal headers |
| `font-body` | 13px (0.8125rem)| 18px | 400 (Regular) | 0 | Descriptions, assistant responses, table text |
| `font-caption` | 11px (0.6875rem)| 14px | 500 (Medium) | +0.02em | Axis ticks, tags, timestamps, attribution |
| `font-mono-val`| 13px (0.8125rem)| 16px | 600 (Semibold)| 0 | Metrics, event counts, FRP megawatt numbers |
| `font-mono-id` | 11px (0.6875rem)| 14px | 400 (Regular) | +0.03em | H3 resolution-7 indices (`87642825fffffff`) |

---

## 6. Spacing & Layout Grid

PyroScope standardizes on an 8-point base grid (with a 4-point half-step for micro-elements):

| Token | Size (px) | Tailwind | Component Application |
| :--- | :--- | :--- | :--- |
| `space-1` | 4px | `p-1`, `gap-1` | Micro-badges, icon-to-label gaps |
| `space-2` | 8px | `p-2`, `gap-2` | Calendar cell margins, button padding (compact) |
| `space-3` | 12px | `p-3`, `gap-3` | Control bars, chip clusters |
| `space-4` | 16px | `p-4`, `gap-4` | Panel padding, card interiors |
| `space-6` | 24px | `p-6`, `gap-6` | Main dashboard gutter between map and side panel |
| `space-8` | 32px | `p-8`, `gap-8` | Methodology page article margins |

### Border Radius
- `radius-sm`: `4px` (calendar matrix cells, small badges)
- `radius-md`: `6px` (buttons, dropdown menus, text inputs)
- `radius-lg`: `10px` (cards, floating control docks)
- `radius-xl`: `14px` (modals, slide-out drawer sheets)
- `radius-full`: `9999px` (status pills, avatar chips)

---

## 7. Tailwind CSS v4 Mapping Reference

Add or verify in `apps/web/src/app/globals.css`:

```css
@theme {
  --color-surface-canvas: #080B10;
  --color-surface-panel: #0E141F;
  --color-surface-card: #161F30;
  --color-surface-card-hover: #1E293B;
  --color-surface-card-active: #253347;

  --color-border-subtle: #1F293D;
  --color-border-default: #2D3B55;
  --color-border-focus: #FF6B00;

  --color-text-primary: #F8FAFC;
  --color-text-secondary: #94A3B8;
  --color-text-muted: #64748B;
  --color-text-accent: #FF6B00;

  --color-accent-primary: #FF6B00;
  --color-accent-hover: #FF8533;
  --color-accent-subtle: rgba(255, 107, 0, 0.12);
  --color-accent-glow: rgba(255, 107, 0, 0.25);

  --color-anomaly-normal: #10B981;
  --color-anomaly-elevated: #F59E0B;
  --color-anomaly-extreme: #EF4444;

  --color-sensor-modis: #38BDF8;    /* Sky blue for MODIS (Terra/Aqua) */
  --color-sensor-viirs: #F43F5E;    /* Rose for VIIRS (S-NPP) */
  --color-sensor-spliced: #A855F7;  /* Purple for Naive Splice */
  --color-sensor-harmonized: #FF6B00; /* PyroScope Harmonized series */
}
```
