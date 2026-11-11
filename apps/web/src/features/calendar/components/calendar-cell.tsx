import * as React from "react";
import type { CalendarCell as CalendarCellType } from "../types";
import { ANOMALY_CONFIGS } from "@/lib/color/legend";
import { getInfernoRgba, normalizeClipped } from "@/lib/color/scales";
import { formatMonthFull, formatPercentile } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface CalendarCellProps {
  cell: CalendarCellType;
  p95Baseline: number;
  isSeasonMonth?: boolean;
  isSelected?: boolean;
  onClick: (cell: CalendarCellType) => void;
  className?: string;
}

export function CalendarCell({
  cell,
  p95Baseline,
  isSeasonMonth = false,
  isSelected = false,
  onClick,
  className,
}: CalendarCellProps) {
  const anomalyConfig = ANOMALY_CONFIGS[cell.class] || ANOMALY_CONFIGS.normal;

  // Background color from normalized Inferno ramp
  const t = normalizeClipped(cell.value, Math.max(1, p95Baseline));
  const [r, g, b] = getInfernoRgba(t, 200);
  const bgColor = `rgba(${r}, ${g}, ${b}, 0.65)`;

  const monthName = formatMonthFull(cell.month);
  const ariaLabel = `${monthName} ${cell.year}, ${Math.round(cell.value)} events, ${cell.class} anomaly (${formatPercentile(cell.percentile_rank)})${cell.provisional ? ", provisional data" : ""}`;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick(cell);
    }
  };

  return (
    <td
      tabIndex={0}
      role="gridcell"
      aria-label={ariaLabel}
      aria-selected={isSelected}
      onClick={() => onClick(cell)}
      onKeyDown={handleKeyDown}
      style={{ backgroundColor: bgColor }}
      className={cn(
        "relative h-10 w-12 cursor-pointer p-1 text-center font-mono text-xs transition-all outline-hidden select-none",
        "focus-visible:ring-2 focus-visible:ring-[#ff6b00] focus-visible:z-20",
        // Season month ambient highlight
        isSeasonMonth && "ring-1 ring-[rgba(255,107,0,0.2)]",
        // Anomaly non-color border cues
        cell.class === "normal" && "border border-[#1f293d]/60",
        cell.class === "elevated" && "border-2 border-dashed border-[#f59e0b] shadow-[0_0_8px_rgba(245,158,11,0.2)]",
        cell.class === "extreme" && "border-2 border-solid border-[#ef4444] shadow-[0_0_12px_rgba(239,68,68,0.35)] animate-pulse",
        // Selected highlight
        isSelected && "ring-2 ring-white z-10",
        // Provisional hatched pattern
        cell.provisional && "bg-[repeating-linear-gradient(45deg,transparent,transparent_3px,rgba(245,158,11,0.2)_3px,rgba(245,158,11,0.2)_6px)]",
        className
      )}
    >
      <div className="flex flex-col items-center justify-center h-full">
        {/* Value */}
        <span
          className={cn(
            "text-[11px] font-semibold leading-tight",
            cell.class === "extreme" ? "text-white font-bold" : "text-[#f8fafc]"
          )}
        >
          {Math.round(cell.value)}
        </span>

        {/* Non-color anomaly symbol */}
        <div className="flex items-center gap-0.5 mt-0.5">
          <span
            className={cn("text-[9px] leading-none", anomalyConfig.textColor)}
            title={`${anomalyConfig.label} anomaly`}
          >
            {anomalyConfig.symbol}
          </span>
          {cell.provisional && (
            <span
              className="text-[8px] text-amber-400 font-bold leading-none"
              title="Provisional NRT detection"
            >
              *
            </span>
          )}
        </div>
      </div>
    </td>
  );
}
