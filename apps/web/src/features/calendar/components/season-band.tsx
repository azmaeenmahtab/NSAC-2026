import * as React from "react";
import type { FireSeason } from "../types";
import { formatMonthShort } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface SeasonBandProps {
  season?: FireSeason | null;
  className?: string;
}

export function isMonthInSeason(month: number, season?: FireSeason | null): boolean {
  if (!season) return false;
  const { start_month, end_month } = season;
  if (start_month <= end_month) {
    return month >= start_month && month <= end_month;
  }
  return month >= start_month || month <= end_month;
}

export function SeasonBand({ season, className }: SeasonBandProps) {
  if (!season) return null;

  const sharePct = Math.round(season.share_of_annual * 100);
  const startName = formatMonthShort(season.start_month);
  const endName = formatMonthShort(season.end_month);
  const peakName = formatMonthShort(season.peak_month);

  return (
    <div
      role="region"
      aria-label="Active fire season bracket"
      data-testid="season-band"
      className={cn(
        "flex items-center justify-between rounded-md border border-[#ff6b00]/30 bg-[rgba(255,107,0,0.08)] px-3 py-1.5 text-xs text-[#f8fafc]",
        className
      )}
    >
      <div className="flex items-center gap-2">
        <span className="flex h-2 w-2 rounded-full bg-[#ff6b00] animate-pulse" />
        <span className="font-semibold text-xs text-[#ff6b00]">
          Burning Season Bracket:
        </span>
        <span className="font-mono text-xs text-[#f8fafc]">
          {startName} – {endName}
        </span>
        <span className="rounded bg-[#161f30] px-1.5 py-0.2 text-[10px] font-mono text-[#ff8533] border border-[#2d3b55]">
          {sharePct}% of annual fires
        </span>
      </div>

      <div className="flex items-center gap-1.5 text-[11px] text-[#94a3b8]">
        <span>Peak activity:</span>
        <span className="font-semibold text-[#f8fafc] font-mono">
          ★ {peakName}
        </span>
      </div>
    </div>
  );
}
