import { interpolateInferno } from "d3-scale-chromatic";
import { rgb } from "d3-color";

export interface AnomalyConfig {
  label: string;
  symbol: string;
  textColor: string;
  bgTint: string;
  borderColor: string;
  hex: string;
}

export const ANOMALY_CONFIGS: Record<string, AnomalyConfig> = {
  normal: {
    label: "Normal",
    symbol: "●",
    textColor: "text-[#94a3b8]",
    bgTint: "bg-[#161f30]/40",
    borderColor: "border-[#1f293d]",
    hex: "#94a3b8",
  },
  elevated: {
    label: "Elevated",
    symbol: "▲",
    textColor: "text-[#f59e0b]",
    bgTint: "bg-[#f59e0b]/10",
    borderColor: "border-[#f59e0b]/40",
    hex: "#f59e0b",
  },
  extreme: {
    label: "Extreme",
    symbol: "◆",
    textColor: "text-[#ef4444]",
    bgTint: "bg-[#ef4444]/15",
    borderColor: "border-[#ef4444]/50",
    hex: "#ef4444",
  },
};

export interface LegendStep {
  index: number;
  t: number;
  hex: string;
  label: string;
  rangeLabel: string;
}

const STEP_COUNT = 8;
export const INFERNO_LEGEND_STEPS: LegendStep[] = Array.from(
  { length: STEP_COUNT },
  (_, index) => {
    const t = index / (STEP_COUNT - 1);
    const c = rgb(interpolateInferno(t));
    const hex = c.formatHex
      ? c.formatHex()
      : `#${Math.round(c.r).toString(16).padStart(2, "0")}${Math.round(c.g).toString(16).padStart(2, "0")}${Math.round(c.b).toString(16).padStart(2, "0")}`;
    const pct = Math.round(t * 100);
    return {
      index,
      t,
      hex,
      label: `Step ${index + 1}`,
      rangeLabel: `${pct}% of p95 baseline`,
    };
  }
);
