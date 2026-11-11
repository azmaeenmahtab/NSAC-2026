import * as React from "react";
import type { JumpMetrics as JumpMetricsType } from "../types";
import { cn } from "@/lib/utils";

export interface JumpMetricsProps {
  metrics?: JumpMetricsType | null;
  className?: string;
}

export function JumpMetrics({ metrics, className }: JumpMetricsProps) {
  if (!metrics || metrics.naive_ratio === undefined || metrics.harmonized_ratio === undefined) {
    return null;
  }

  const naive = metrics.naive_ratio.toFixed(2);
  const harmonized = metrics.harmonized_ratio.toFixed(2);
  const pctReduction = Math.round(
    ((metrics.naive_ratio - metrics.harmonized_ratio) / (metrics.naive_ratio - 1.0)) * 100
  );

  return (
    <div
      role="region"
      aria-label="Structural sensor jump evaluation"
      data-testid="jump-metrics"
      className={cn(
        "rounded-xl border border-[#2d3b55] bg-[#0e141f] p-4 text-xs text-[#f8fafc] shadow-sm space-y-3",
        className
      )}
    >
      <div className="flex items-center gap-2">
        <span className="flex h-2 w-2 rounded-full bg-[#ff6b00]" />
        <h4 className="font-semibold text-xs text-[#ff6b00]">
          The Sensor Splice Discontinuity (&ldquo;Hidden Jump&rdquo;)
        </h4>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="rounded-lg border border-[#1f293d] bg-[#161f30] p-3">
          <div className="text-[10px] text-[#64748b]">Naive Spliced Ratio (Post / Pre 2012)</div>
          <div className="text-xl font-mono font-bold text-[#f59e0b] mt-1">
            {naive}×
          </div>
          <div className="text-[10px] text-[#94a3b8] mt-0.5">
            Artificial spike due to 375m sensor
          </div>
        </div>

        <div className="rounded-lg border border-[#1f293d] bg-[#161f30] p-3">
          <div className="text-[10px] text-[#64748b]">Harmonized Ratio (Post / Pre 2012)</div>
          <div className="text-xl font-mono font-bold text-[#ff6b00] mt-1">
            {harmonized}×
          </div>
          <div className="text-[10px] text-[#94a3b8] mt-0.5">
            Calibrated MODIS-equivalent baseline
          </div>
        </div>

        <div className="rounded-lg border border-[#1f293d] bg-[#161f30] p-3">
          <div className="text-[10px] text-[#64748b]">Sensor Discontinuity Removed</div>
          <div className="text-xl font-mono font-bold text-emerald-400 mt-1">
            {isNaN(pctReduction) ? "100" : pctReduction}%
          </div>
          <div className="text-[10px] text-[#94a3b8] mt-0.5">
            Empirical bias eliminated
          </div>
        </div>
      </div>

      <p className="text-[11px] text-[#94a3b8] leading-relaxed border-t border-[#1f293d]/50 pt-2 italic">
        Note: These metrics describe the empirical relationship in the data and do not prove the absence of real fire trends.
      </p>
    </div>
  );
}
