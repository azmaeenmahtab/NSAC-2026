import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { Tooltip } from "@/components/ui/tooltip";

export interface DataStatusBadgeProps {
  dataVersion?: string;
  asOf?: string;
  provisionalFrom?: string | null;
  className?: string;
}

export function DataStatusBadge({
  dataVersion = "loading...",
  asOf,
  provisionalFrom,
  className,
}: DataStatusBadgeProps) {
  return (
    <div
      className={`inline-flex items-center gap-2 flex-wrap ${className || ""}`}
      data-testid="data-status-badge"
    >
      <Badge variant="default" className="text-[11px] font-mono py-0.5">
        <span className="text-[#64748b]">v</span>
        <span className="text-[#f8fafc]">{dataVersion}</span>
        {asOf && (
          <>
            <span className="text-[#2d3b55] mx-1">|</span>
            <span className="text-[#94a3b8]">As of {asOf}</span>
          </>
        )}
      </Badge>

      {provisionalFrom && (
        <Tooltip
          content={`Near-Real-Time VIIRS data incorporated from ${provisionalFrom}. Subject to standard QA/QC recalibration.`}
        >
          <Badge
            variant="provisional"
            className="text-[11px] font-mono cursor-help"
            data-testid="provisional-badge"
          >
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping mr-0.5" />
            Provisional data included
          </Badge>
        </Tooltip>
      )}
    </div>
  );
}
