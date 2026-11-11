import * as React from "react";
import type { CalendarCell, MonthClimatology } from "../types";
import { ANOMALY_CONFIGS } from "@/lib/color/legend";
import { formatMonthFull, formatNumber, formatPercentile } from "@/lib/format";
import { Sheet, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export interface MonthDetailDrawerProps {
  cell: CalendarCell | null;
  climatology?: MonthClimatology | null;
  open: boolean;
  onClose: () => void;
}

export function MonthDetailDrawer({
  cell,
  climatology,
  open,
  onClose,
}: MonthDetailDrawerProps) {
  if (!cell) return null;

  const monthName = formatMonthFull(cell.month);
  const anomaly = ANOMALY_CONFIGS[cell.class] || ANOMALY_CONFIGS.normal;

  return (
    <Sheet open={open} onOpenChange={(isOpen) => !isOpen && onClose()} side="right">
      <SheetHeader className="pb-3 border-b border-[#1f293d]">
        <div className="flex items-center justify-between">
          <SheetTitle className="text-base font-bold text-[#f8fafc]">
            {monthName} {cell.year}
          </SheetTitle>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-7 text-xs">
            ✕
          </Button>
        </div>
      </SheetHeader>

      <div className="mt-4 space-y-4 text-xs text-[#94a3b8]">
        {/* Status Badge */}
        <div
          className={`flex items-center justify-between rounded-lg border p-3 ${anomaly.bgTint} ${anomaly.borderColor}`}
        >
          <div className="flex items-center gap-2">
            <span className={`text-base font-bold ${anomaly.textColor}`}>
              {anomaly.symbol}
            </span>
            <div>
              <div className="font-semibold text-xs text-[#f8fafc]">
                {anomaly.label} Anomaly
              </div>
              <div className="text-[11px] text-[#94a3b8]">
                {formatPercentile(cell.percentile_rank)} historical percentile
              </div>
            </div>
          </div>
          <Badge variant={cell.class === "extreme" ? "extreme" : cell.class === "elevated" ? "elevated" : "normal"}>
            {anomaly.label}
          </Badge>
        </div>

        {/* Primary Metric */}
        <div className="rounded-lg border border-[#1f293d] bg-[#161f30] p-4 text-center">
          <div className="text-[11px] text-[#94a3b8]">Harmonized Fire Events</div>
          <div className="text-3xl font-bold font-mono text-[#ff6b00] mt-1">
            {formatNumber(cell.value)}
          </div>
          <div className="text-[10px] text-[#64748b] mt-1">
            MODIS-equivalent calibrated physical events
          </div>
          {cell.provisional && (
            <Badge variant="provisional" className="mt-2 text-[10px]">
              Provisional NRT data
            </Badge>
          )}
        </div>

        {/* Historical Climatology Reference */}
        {climatology && (
          <div className="rounded-lg border border-[#1f293d] bg-[#080b10] p-3 space-y-2">
            <div className="font-semibold text-xs text-[#f8fafc] border-b border-[#1f293d] pb-1">
              Historical {monthName} Baseline
            </div>
            <div className="grid grid-cols-2 gap-2 font-mono text-xs pt-1">
              <div>
                <span className="text-[#64748b]">Mean:</span>{" "}
                <span className="text-[#f8fafc]">{formatNumber(Math.round(climatology.mean))}</span>
              </div>
              <div>
                <span className="text-[#64748b]">Median (p50):</span>{" "}
                <span className="text-[#f8fafc]">{formatNumber(Math.round(climatology.p50))}</span>
              </div>
              <div>
                <span className="text-[#64748b]">Elevated (p90):</span>{" "}
                <span className="text-[#f59e0b]">{formatNumber(Math.round(climatology.p90))}</span>
              </div>
              <div>
                <span className="text-[#64748b]">Extreme (p95):</span>{" "}
                <span className="text-[#ef4444]">{formatNumber(Math.round(climatology.p95))}</span>
              </div>
            </div>
          </div>
        )}

        {/* Explanatory Context */}
        <div className="text-[11px] text-[#64748b] leading-relaxed">
          Anomalies are evaluated using a leave-one-year-out historical climatology baseline.
          Activity exceeding the 95th percentile represents an extreme deviation requiring heightened operational vigilance.
        </div>
      </div>
    </Sheet>
  );
}

