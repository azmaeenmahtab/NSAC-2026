"use client";

import * as React from "react";
import { useMeta } from "@/features/shell";
import { cn } from "@/lib/utils";

export interface AttributionProps {
  className?: string;
}

export function Attribution({ className }: AttributionProps) {
  const { data: metaResponse } = useMeta();
  const [showNotice, setShowNotice] = React.useState(false);

  const attributionText =
    metaResponse?.data?.attribution ||
    "We acknowledge the use of data and imagery from NASA's FIRMS (EOSDIS), courtesy of NASA LANCE and UMD. Basemap © OpenStreetMap, © MapLibre. Boundaries: geoBoundaries (CC-BY 3.0 IGO / CC0).";

  return (
    <>
      <footer
        className={cn(
          "flex flex-col sm:flex-row items-center justify-between gap-2 border-t border-[#1f293d] bg-[#080b10] px-4 py-2 text-[10px] text-[#64748b] relative z-20",
          className
        )}
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span>{attributionText}</span>
          <button
            type="button"
            onClick={() => setShowNotice(true)}
            className="text-[#ff6b00] hover:underline font-medium cursor-pointer"
          >
            Safety Notice
          </button>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span>Team Singularity</span>
          <span>•</span>
          <span>NASA Space Apps Challenge 2026</span>
        </div>
      </footer>

      {showNotice && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="safety-notice-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4"
        >
          <div className="max-w-lg rounded-xl border border-[#2d3b55] bg-[#0e141f] p-5 shadow-2xl text-xs space-y-3">
            <div className="flex items-center justify-between border-b border-[#1f293d] pb-2">
              <h3 id="safety-notice-title" className="font-semibold text-white flex items-center gap-1.5">
                <span>⚠️</span>
                <span>Operational Safety & Scientific Research Notice</span>
              </h3>
              <button
                type="button"
                onClick={() => setShowNotice(false)}
                className="text-[#64748b] hover:text-white text-sm"
                aria-label="Close safety notice dialog"
              >
                ✕
              </button>
            </div>

            <p className="text-[#cbd5e1] leading-relaxed">
              <strong className="text-white">NOTICE: </strong>
              PyroScope is an open scientific research and decision-support platform designed for retrospective analysis, pattern discovery, and early season awareness. It is{" "}
              <strong className="text-[#ef4444]">NOT</strong> an operational tactical fire dispatch system or emergency evacuation service.
            </p>

            <p className="text-[#94a3b8] leading-relaxed">
              Active-fire detections are thermal hot spots; harmonized counts represent{" "}
              <strong className="text-white">MODIS-equivalent fire events</strong>, not burned area or hectares.
            </p>

            <p className="text-[#94a3b8] leading-relaxed">
              In the event of an active wildfire threat, immediately contact the{" "}
              <strong className="text-white">Bangladesh Fire Service and Civil Defence (emergency: 999 or 102)</strong> and the Ministry of Environment, Forest and Climate Change.
            </p>

            <div className="pt-2 text-right">
              <button
                type="button"
                onClick={() => setShowNotice(false)}
                className="px-4 py-1.5 rounded-lg bg-[#ff6b00] text-white font-medium hover:bg-[#e05e00] transition-colors"
              >
                Acknowledge & Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
