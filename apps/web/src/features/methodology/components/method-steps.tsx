import * as React from "react";
import { cn } from "@/lib/utils";

export interface MethodStepsProps {
  className?: string;
}

const STEPS = [
  {
    step: "01",
    title: "FIRMS Satellite Ingest",
    summary: "Raw MODIS (1km) & VIIRS S-NPP (375m) archive and NRT CSV detections are ingested, filtered by confidence (nominal/high), and deduplicated.",
    icon: "🛰️",
  },
  {
    step: "02",
    title: "ST-DBSCAN Fire Events",
    summary: "Continuous physical burning events are clustered across space (ε = 2,700m) and time (ε = 24h), collapsing multiple satellite overpasses into distinct fire events.",
    icon: "🔥",
  },
  {
    step: "03",
    title: "H3 Hexagonal Indexing",
    summary: "Events are partitioned into Uber H3 spatial hexagons (resolutions 5, 6, 7) and aggregated into monthly regional and cell count tables.",
    icon: "⬡",
  },
  {
    step: "04",
    title: "Quantile-Mapping Calibration",
    summary: "Over the 2012–present overlap window, VIIRS distributions are calibrated to MODIS equivalents using circular 3-month empirical quantile mapping.",
    icon: "⚖️",
  },
  {
    step: "05",
    title: "Burning Activity Calendar",
    summary: "25-year consistent climatological baselines, monthly anomalies (normal, elevated, extreme), and seasonal brackets are computed and stored in Parquet.",
    icon: "📅",
  },
] as const;

export function MethodSteps({ className }: MethodStepsProps) {
  return (
    <div
      role="region"
      aria-label="Harmonization pipeline process flow"
      data-testid="method-steps"
      className={cn("space-y-4", className)}
    >
      <div>
        <h3 className="text-sm font-semibold text-[#f8fafc]">
          End-to-End Harmonization Pipeline
        </h3>
        <p className="text-xs text-[#94a3b8]">
          Five-stage reproducible transformation from raw NASA hot spots to calibrated climatology
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {STEPS.map((s, idx) => (
          <div
            key={s.step}
            className="relative flex flex-col justify-between rounded-lg border border-[#1f293d] bg-[#0e141f] p-3 text-xs shadow-xs group hover:border-[#ff6b00]/60 transition-colors"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] text-[#ff6b00] font-bold">
                  STEP {s.step}
                </span>
                <span className="text-base">{s.icon}</span>
              </div>
              <h4 className="font-semibold text-xs text-[#f8fafc] mb-1.5">
                {s.title}
              </h4>
              <p className="text-[11px] text-[#94a3b8] leading-relaxed">
                {s.summary}
              </p>
            </div>

            {idx < STEPS.length - 1 && (
              <div className="hidden md:block absolute -right-2 top-1/2 -translate-y-1/2 z-10 text-[#64748b]">
                →
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
