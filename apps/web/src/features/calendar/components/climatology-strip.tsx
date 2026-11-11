import * as React from "react";
import type { MonthClimatology } from "../types";
import { formatMonthShort, formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface ClimatologyStripProps {
  climatology: MonthClimatology[];
  className?: string;
}

export function ClimatologyStrip({
  climatology,
  className,
}: ClimatologyStripProps) {
  const maxMean = React.useMemo(() => {
    return Math.max(...climatology.map((c) => c.mean), 1);
  }, [climatology]);

  // Map by month 1..12
  const monthMap = React.useMemo(() => {
    const map = new Map<number, MonthClimatology>();
    for (const c of climatology) {
      map.set(c.month, c);
    }
    return map;
  }, [climatology]);

  return (
    <div
      role="region"
      aria-label="Monthly historical baseline climatology"
      data-testid="climatology-strip"
      className={cn(
        "rounded-lg border border-[#1f293d] bg-[#0e141f] p-3 text-xs",
        className
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-xs text-[#f8fafc]">
          Historical Monthly Climatology Baseline
        </span>
        <span className="text-[10px] text-[#64748b] font-mono">
          Mean with p90 / p95 thresholds
        </span>
      </div>

      <div className="grid grid-cols-12 gap-1 text-center font-mono">
        {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => {
          const item = monthMap.get(month);
          const mean = item?.mean || 0;
          const p90 = item?.p90 || 0;
          const p95 = item?.p95 || 0;
          const heightPct = Math.round((mean / maxMean) * 100);

          return (
            <div
              key={month}
              className="flex flex-col items-center gap-1 group relative cursor-help"
              title={`${formatMonthShort(month)} Baseline: Mean ${formatNumber(Math.round(mean))}, p90 ${formatNumber(Math.round(p90))}, p95 ${formatNumber(Math.round(p95))}`}
            >
              {/* Bar visualization */}
              <div className="relative flex h-14 w-full items-end justify-center rounded bg-[#161f30] p-0.5">
                {/* Mean bar */}
                <div
                  style={{ height: `${Math.max(4, heightPct)}%` }}
                  className="w-full rounded-xs bg-[#ff6b00]/70 group-hover:bg-[#ff6b00] transition-colors"
                />

                {/* p90 tick indicator */}
                {maxMean > 0 && p90 > 0 && (
                  <div
                    style={{ bottom: `${Math.min(95, (p90 / (maxMean * 1.5)) * 100)}%` }}
                    className="absolute left-0 right-0 h-0.5 bg-[#f59e0b]/80"
                  />
                )}

                {/* p95 tick indicator */}
                {maxMean > 0 && p95 > 0 && (
                  <div
                    style={{ bottom: `${Math.min(98, (p95 / (maxMean * 1.5)) * 100)}%` }}
                    className="absolute left-0 right-0 h-0.5 bg-[#ef4444]"
                  />
                )}
              </div>

              {/* Mean numeric value */}
              <span className="text-[10px] text-[#94a3b8] group-hover:text-[#f8fafc]">
                {Math.round(mean)}
              </span>

              {/* Month label */}
              <span className="text-[10px] font-semibold text-[#64748b]">
                {formatMonthShort(month)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
