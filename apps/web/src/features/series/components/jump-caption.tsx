import * as React from "react";
import type { MethodologyJumpMetrics } from "../types";
import { cn } from "@/lib/utils";

export interface JumpCaptionProps {
  metrics?: MethodologyJumpMetrics | null;
  className?: string;
}

export function JumpCaption({ metrics, className }: JumpCaptionProps) {
  const jumpObj = (metrics as { jump_metrics?: MethodologyJumpMetrics })?.jump_metrics || metrics;
  if (!jumpObj || jumpObj.naive_ratio === undefined) return null;

  const naiveRatioFormatted = jumpObj.naive_ratio.toFixed(2);
  const harmonizedRatioFormatted = jumpObj.harmonized_ratio.toFixed(2);
  const reductionFormatted =
    jumpObj.jump_reduction_pct !== undefined
      ? Math.round(jumpObj.jump_reduction_pct)
      : Math.round(
          ((jumpObj.naive_ratio - jumpObj.harmonized_ratio) /
            (jumpObj.naive_ratio - 1.0)) *
            100
        );

  return (
    <div
      role="note"
      aria-label="Sensor splice jump analysis"
      data-testid="jump-caption"
      className={cn(
        "rounded-lg border border-[#2d3b55] bg-[#0e141f] p-3 text-xs text-[#f8fafc] shadow-sm space-y-1.5",
        className
      )}
    >
      <div className="flex items-center gap-2">
        <span className="flex h-2 w-2 rounded-full bg-[#ff6b00]" />
        <span className="font-semibold text-xs text-[#ff6b00]">
          The &ldquo;Hidden Jump&rdquo; Calibration Analysis:
        </span>
      </div>

      <p className="text-[#94a3b8] text-[11px] leading-relaxed">
        Without harmonization, annual fire counts in the 2012–2016 period appear{" "}
        <strong className="text-[#f59e0b] font-mono">
          {naiveRatioFormatted}× higher
        </strong>{" "}
        than the pre-2012 MODIS baseline due to VIIRS 375m sensor resolution.
        After quantile-mapping harmonization, the post-to-pre ratio is{" "}
        <strong className="text-[#ff6b00] font-mono">
          {harmonizedRatioFormatted}×
        </strong>{" "}
        ({reductionFormatted}% artificial discontinuity removed).
      </p>
    </div>
  );
}
