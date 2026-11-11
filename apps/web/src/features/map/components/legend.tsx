import * as React from "react";
import type { MetricType } from "@/features/areas";
import type { HeatmapStats } from "../types";
import { INFERNO_LEGEND_STEPS } from "@/lib/color/legend";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface MapLegendProps {
  stats?: HeatmapStats | null;
  metric?: MetricType;
  className?: string;
}

export function MapLegend({
  stats,
  metric = "harmonized",
  className,
}: MapLegendProps) {
  const unitLabel =
    metric === "harmonized"
      ? "MODIS-equivalent fire events per cell"
      : metric === "raw_modis"
      ? "Raw MODIS hot spots per cell"
      : "Raw VIIRS hot spots per cell";

  return (
    <div
      role="region"
      aria-label="Fire density scale legend"
      data-testid="map-legend"
      className={cn(
        "flex flex-col gap-1.5 rounded-lg border border-[#1f293d] bg-[#0e141f]/90 p-3 text-xs text-[#f8fafc] shadow-lg backdrop-blur-md max-w-xs",
        className
      )}
    >
      <div className="flex items-center justify-between font-semibold text-[11px] text-[#f8fafc]">
        <span>Spatial Fire Density</span>
        <span className="font-mono text-[10px] text-[#ff6b00]">Inferno Scale</span>
      </div>

      {/* 8-step Inferno gradient bar */}
      <div className="flex h-3 w-full rounded overflow-hidden border border-[#2d3b55]/60">
        {INFERNO_LEGEND_STEPS.map((step) => (
          <div
            key={step.index}
            style={{ backgroundColor: step.hex }}
            className="flex-1"
            title={`${step.label}: ${step.rangeLabel}`}
          />
        ))}
      </div>

      {/* Labels below color bar */}
      <div className="flex justify-between text-[10px] font-mono text-[#94a3b8]">
        <span>0</span>
        {stats && (
          <>
            <span>p50: {formatNumber(Math.round(stats.p50))}</span>
            <span className="text-[#ff6b00]">p95: {formatNumber(Math.round(stats.p95))}</span>
            <span>Max: {formatNumber(Math.round(stats.max))}</span>
          </>
        )}
        {!stats && <span>Peak</span>}
      </div>

      <div className="text-[10px] text-[#64748b] border-t border-[#1f293d]/50 pt-1 leading-tight">
        {unitLabel}
      </div>
    </div>
  );
}
