import * as React from "react";
import { cn } from "@/lib/utils";

export interface LimitationsProps {
  limitations?: string[];
  className?: string;
}

const FALLBACK_LIMITATIONS = [
  "Active-fire counts are not burned area. Harmonized counts are 'MODIS-equivalent fire events', not hectares.",
  "The calibration assumes the MODIS-VIIRS relationship observed in 2012-present also holds before 2012 (it cannot be tested there).",
  "MODIS is itself not homogeneous: Aqua joined Terra in mid-2002, and Terra/Aqua orbits have drifted. We report this as a limitation and test sensitivity if time allows.",
  "Cloud, smoke and underground fires are under-detected by both sensors.",
  "Harmonization quality is measured by agreement over the overlap period (leave-one-year-out CV), not by the absence of change; real trends can remain.",
  "Alerts and guidance are advisory, not an official warning system.",
];

export function Limitations({
  limitations = FALLBACK_LIMITATIONS,
  className,
}: LimitationsProps) {
  const items = limitations.length > 0 ? limitations : FALLBACK_LIMITATIONS;

  return (
    <div
      role="region"
      aria-label="Known scientific limitations and disclaimers"
      data-testid="limitations"
      className={cn(
        "rounded-xl border border-amber-500/30 bg-amber-950/15 p-4 text-xs text-[#f8fafc] shadow-sm space-y-3",
        className
      )}
    >
      <div className="flex items-center gap-2">
        <span className="text-base">⚠️</span>
        <div>
          <h4 className="font-semibold text-xs text-amber-300">
            Known Scientific Limitations & Transparency Disclaimers
          </h4>
          <p className="text-[10px] text-amber-200/70">
            Non-negotiable scientific honesty requirements for remote sensing data interpretation
          </p>
        </div>
      </div>

      <ul className="space-y-2 text-[11px] text-[#cbd5e1] leading-relaxed list-disc list-inside">
        {items.map((lim, idx) => (
          <li key={idx} className="marker:text-amber-400">
            {lim}
          </li>
        ))}
      </ul>
    </div>
  );
}
