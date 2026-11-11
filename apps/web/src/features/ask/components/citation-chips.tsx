import * as React from "react";
import type { Citation } from "../types";
import { useViewState } from "@/features/areas";
import { cn } from "@/lib/utils";

export interface CitationChipsProps {
  citations: Citation[];
  className?: string;
}

export function CitationChips({ citations, className }: CitationChipsProps) {
  const { setArea, setDateRange } = useViewState();

  if (!citations || citations.length === 0) return null;

  return (
    <div
      role="region"
      aria-label="Data citations"
      data-testid="citation-chips"
      className={cn("flex flex-wrap items-center gap-1.5 pt-1", className)}
    >
      <span className="text-[10px] font-mono text-[#64748b]">Sources:</span>
      {citations.map((c, idx) => {
        const yearText =
          c.years && c.years.length > 0
            ? c.years.length === 1
              ? `year ${c.years[0]}`
              : `years ${Math.min(...c.years)} to ${Math.max(...c.years)}`
            : null;

        const areaText = c.areaId ? `area ${c.areaId}` : null;
        const details = [c.dataVersion, yearText, areaText].filter(Boolean).join(", ");
        const chipLabel = `Data ${details}`;

        const handleClick = () => {
          if (c.areaId) {
            setArea(c.areaId);
          }
          if (c.years && c.years.length > 0) {
            const minYear = Math.min(...c.years);
            const maxYear = Math.max(...c.years);
            setDateRange(`${minYear}-01`, `${maxYear}-12`);
          }
        };

        return (
          <button
            key={`${c.tool}-${idx}`}
            type="button"
            onClick={handleClick}
            title="Click to apply cited area and years to active view"
            aria-label={`Inspect source: ${chipLabel}`}
            className="inline-flex items-center gap-1 rounded bg-[#161f30] px-2 py-0.5 text-[10px] font-mono text-[#94a3b8] border border-[#2d3b55] hover:border-[#ff6b00]/60 hover:text-[#ff6b00] transition-colors cursor-pointer"
          >
            <span>📎</span>
            <span>{chipLabel}</span>
          </button>
        );
      })}
    </div>
  );
}

