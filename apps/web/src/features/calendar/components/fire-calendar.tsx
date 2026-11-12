"use client";

import * as React from "react";
import { useCalendar } from "../api/use-calendar";
import type { CalendarCell as CalendarCellType } from "../types";
import { SeasonBand, isMonthInSeason } from "./season-band";
import { CalendarCell } from "./calendar-cell";
import { ClimatologyStrip } from "./climatology-strip";
import { MonthDetailDrawer } from "./month-detail-drawer";
import { QueryBoundary } from "@/components/feedback/query-boundary";
import { useViewState } from "@/features/areas";
import { useLanguage } from "@/lib/i18n";
import { formatMonthShort, formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

export function FireCalendar({ className }: { className?: string }) {
  const { area } = useViewState();
  const { data: calendarEnvelope, isLoading, isError, error, refetch } = useCalendar(area);
  const { t, isBangla } = useLanguage();

  const [selectedCell, setSelectedCell] = React.useState<CalendarCellType | null>(null);
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const data = calendarEnvelope?.data;
  const grid = React.useMemo(() => data?.grid || [], [data?.grid]);
  const climatology = React.useMemo(() => data?.climatology || [], [data?.climatology]);
  const season = data?.season;

  // Climatology lookup map by month
  const climatologyMap = React.useMemo(() => {
    const map = new Map<number, (typeof climatology)[0]>();
    for (const c of climatology) {
      map.set(c.month, c);
    }
    return map;
  }, [climatology]);

  // Overall p95 baseline for color scaling
  const p95Baseline = React.useMemo(() => {
    if (climatology.length === 0) return 50;
    return Math.max(...climatology.map((c) => c.p95), 10);
  }, [climatology]);

  // Group grid into year -> month -> cell
  const yearRows = React.useMemo(() => {
    const yearsMap = new Map<number, Map<number, CalendarCellType>>();
    for (const cell of grid) {
      if (!yearsMap.has(cell.year)) {
        yearsMap.set(cell.year, new Map());
      }
      yearsMap.get(cell.year)!.set(cell.month, cell);
    }
    // Sort years descending (latest year at top)
    const sortedYears = Array.from(yearsMap.keys()).sort((a, b) => b - a);
    return sortedYears.map((year) => ({
      year,
      months: yearsMap.get(year)!,
      annualTotal: Array.from(yearsMap.get(year)!.values()).reduce(
        (sum, c) => sum + c.value,
        0
      ),
    }));
  }, [grid]);

  const handleCellClick = (cell: CalendarCellType) => {
    setSelectedCell(cell);
    setDrawerOpen(true);
  };

  return (
    <QueryBoundary
      isLoading={isLoading}
      isError={isError}
      error={error}
      onRetry={refetch}
      isEmpty={grid.length === 0}
    >
      <div
        className={cn("flex flex-col gap-4 p-4 text-[#f8fafc]", className)}
        data-testid="fire-calendar"
      >
        {/* Season Bracket Header */}
        <SeasonBand season={season} />

        {/* Plain-Language Explainer Card */}
        <div className="rounded-lg border border-[#1f293d] bg-[#0e1626] p-3 text-xs text-[#cbd5e1] space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 font-semibold text-white">
              <span>📅</span>
              <span>{t.calendar.explainer_title}</span>
            </div>
            <span className="text-[10px] text-[#ff8533] hidden sm:inline">
              {t.calendar.click_hint}
            </span>
          </div>
          <p className="text-[11px] text-[#94a3b8] leading-relaxed">
            {t.calendar.explainer_text}
          </p>
        </div>

        {/* Compact Legend Bar */}
        <div className="flex items-center gap-3 text-[11px] text-[#94a3b8] px-1 flex-wrap">
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-xs bg-[#10b981]/50" />
            <span>{isBangla ? `${t.calendar.normal} (Normal)` : "Normal"}</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-xs bg-[#f59e0b]/50" />
            <span>{isBangla ? `${t.calendar.elevated} (Elevated)` : "Elevated"}</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-xs bg-[#ef4444] text-white text-[7px] flex items-center justify-center font-bold">
              ◆
            </span>
            <span>{isBangla ? `${t.calendar.extreme} (Extreme)` : "Extreme"}</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="text-[#38bdf8] font-bold text-xs leading-none">*</span>
            <span>{isBangla ? `${t.calendar.provisional} (Provisional)` : "Provisional"}</span>
          </span>
        </div>

        {/* 2D Matrix Grid */}
        <div className="overflow-x-auto rounded-lg border border-[#1f293d] bg-[#0e141f] p-2">
          <table
            className="w-full border-collapse text-left"
            role="grid"
            aria-label="Burning Activity Calendar grid"
          >
            <thead>
              <tr className="border-b border-[#1f293d] text-[11px] font-mono text-[#64748b]">
                <th className="py-2 px-3 font-semibold text-[#94a3b8] w-16">
                  {isBangla ? t.calendar.year : "Year"}
                </th>
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => {
                  const inSeason = isMonthInSeason(m, season);
                  const isPeak = season?.peak_month === m;
                  return (
                    <th
                      key={m}
                      className={cn(
                        "py-2 px-1 text-center font-semibold w-12",
                        inSeason ? "text-[#ff6b00] bg-[#ff6b00]/5" : "text-[#94a3b8]"
                      )}
                    >
                      <div>{formatMonthShort(m)}</div>
                      {isPeak && <div className="text-[9px] text-[#ff8533]">★</div>}
                    </th>
                  );
                })}
                <th className="py-2 px-3 text-right font-semibold text-[#94a3b8] w-20">
                  {isBangla ? t.calendar.total : "Total"}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1f293d]/40">
              {yearRows.map(({ year, months, annualTotal }) => (
                <tr key={year} className="hover:bg-[#161f30]/40 transition-colors">
                  <th
                    scope="row"
                    className="py-1 px-3 font-mono text-xs font-semibold text-[#94a3b8]"
                  >
                    {year}
                  </th>
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => {
                    const cell = months.get(month);
                    if (!cell) {
                      return (
                        <td
                          key={month}
                          className="h-10 w-12 border border-[#1f293d]/30 bg-[#080b10] text-center text-[#64748b] text-[10px]"
                        >
                          —
                        </td>
                      );
                    }
                    return (
                      <CalendarCell
                        key={month}
                        cell={cell}
                        p95Baseline={p95Baseline}
                        isSeasonMonth={isMonthInSeason(month, season)}
                        isSelected={
                          selectedCell?.year === cell.year &&
                          selectedCell?.month === cell.month
                        }
                        onClick={handleCellClick}
                      />
                    );
                  })}
                  <td className="py-1 px-3 text-right font-mono text-xs font-semibold text-[#ff8533]">
                    {formatNumber(Math.round(annualTotal))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Climatology Strip */}
        <ClimatologyStrip climatology={climatology} />

        {/* Selected Month Detail Drawer */}
        <MonthDetailDrawer
          cell={selectedCell}
          climatology={selectedCell ? climatologyMap.get(selectedCell.month) : null}
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
        />
      </div>
    </QueryBoundary>
  );
}
