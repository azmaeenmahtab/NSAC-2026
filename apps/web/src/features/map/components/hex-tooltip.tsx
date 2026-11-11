import * as React from "react";
import type { HeatmapCell } from "../types";
import type { MetricType } from "@/features/areas";
import { formatNumber, formatFrp } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface HexTooltipProps {
  cell: HeatmapCell | null;
  x: number;
  y: number;
  metric?: MetricType;
  className?: string;
}

export function HexTooltip({
  cell,
  x,
  y,
  metric = "harmonized",
  className,
}: HexTooltipProps) {
  if (!cell) return null;

  const unitLabel =
    metric === "harmonized"
      ? "MODIS-equiv events"
      : metric === "raw_modis"
      ? "Raw MODIS detections"
      : "Raw VIIRS detections";

  return (
    <div
      role="tooltip"
      data-testid="hex-tooltip"
      style={{ left: x + 12, top: y + 12 }}
      className={cn(
        "pointer-events-none fixed z-50 flex flex-col gap-1 rounded-md border border-[#2d3b55] bg-[#080b10]/95 px-3 py-2 text-xs text-[#f8fafc] shadow-xl backdrop-blur-xs",
        className
      )}
    >
      <div className="flex items-center justify-between gap-3 border-b border-[#1f293d] pb-1 font-mono text-[11px] text-[#94a3b8]">
        <span>H3: {cell.h3}</span>
      </div>

      <div className="flex items-center gap-2 pt-0.5">
        <span className="font-semibold text-sm text-[#ff6b00]">
          {formatNumber(cell.value)}
        </span>
        <span className="text-[11px] text-[#94a3b8]">{unitLabel}</span>
      </div>

      {cell.frp_mw !== undefined && cell.frp_mw !== null && (
        <div className="text-[11px] text-[#64748b] font-mono">
          Radiative Power: <span className="text-[#f8fafc]">{formatFrp(cell.frp_mw)}</span>
        </div>
      )}
    </div>
  );
}
