import * as React from "react";
import type { CalendarCell, MonthClimatology } from "../types";
import { ANOMALY_CONFIGS } from "@/lib/color/legend";
import { formatMonthFull, formatNumber, formatPercentile } from "@/lib/format";
import { Sheet, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useLanguage } from "@/lib/i18n";

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
  const { t, isBangla } = useLanguage();
  if (!cell) return null;

  const monthName = formatMonthFull(cell.month);
  const anomaly = ANOMALY_CONFIGS[cell.class] || ANOMALY_CONFIGS.normal;

  const statusDesc =
    cell.class === "extreme"
      ? isBangla
        ? t.calendar.drawer_extreme_desc
        : "Severe Danger: Top 5% highest fire month in 25 years"
      : cell.class === "elevated"
        ? isBangla
          ? t.calendar.drawer_elevated_desc
          : "Elevated Warning: Significantly more burning than normal"
        : isBangla
          ? t.calendar.drawer_normal_desc
          : "Normal: Within typical expected seasonal levels";

  const adviceText =
    cell.class === "extreme"
      ? isBangla
        ? t.calendar.drawer_advice_extreme
        : t.calendar.drawer_advice_extreme
      : cell.class === "elevated"
        ? isBangla
          ? t.calendar.drawer_advice_elevated
          : t.calendar.drawer_advice_elevated
        : isBangla
          ? t.calendar.drawer_advice_normal
          : t.calendar.drawer_advice_normal;

  return (
    <Sheet open={open} onOpenChange={(isOpen) => !isOpen && onClose()} side="right">
      <SheetHeader className="pb-3 border-b border-[#1f293d]">
        <div className="flex items-center justify-between">
          <SheetTitle className="text-base font-bold text-[#f8fafc]">
            {monthName} {cell.year}
          </SheetTitle>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-7 text-xs cursor-pointer">
            ✕
          </Button>
        </div>
      </SheetHeader>

      <div className="mt-4 space-y-4 text-xs text-[#94a3b8]">
        {/* Status Badge Card */}
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
              <div className="text-[11px] text-[#cbd5e1] font-medium mt-0.5">
                {statusDesc}
              </div>
              <div className="text-[10px] text-[#94a3b8]">
                {formatPercentile(cell.percentile_rank)} {isBangla ? "ঐতিহাসিক পার্সেন্টাইল" : "historical percentile"}
              </div>
            </div>
          </div>
          <Badge
            variant={
              cell.class === "extreme"
                ? "extreme"
                : cell.class === "elevated"
                  ? "elevated"
                  : "normal"
            }
          >
            {isBangla
              ? cell.class === "extreme"
                ? "চরম বিপদ"
                : cell.class === "elevated"
                  ? "বেশি ঝুঁকি"
                  : "স্বাভাবিক"
              : anomaly.label}
          </Badge>
        </div>

        {/* Primary Metric: Total Fires Detected */}
        <div className="rounded-lg border border-[#1f293d] bg-[#161f30] p-4 text-center">
          <div className="text-[11px] font-medium text-[#cbd5e1]">
            {isBangla ? t.calendar.drawer_total_fires : "Total Fires Detected"}
          </div>
          <div className="text-3xl font-bold font-mono text-[#ff6b00] mt-1">
            {formatNumber(cell.value)}
          </div>
          <div className="text-[10px] text-[#94a3b8] mt-1">
            {isBangla ? t.calendar.drawer_total_desc : "Physical fire hot spots recorded in this area for this month"}
          </div>
          {cell.provisional && (
            <Badge variant="provisional" className="mt-2 text-[10px]">
              {isBangla ? t.calendar.provisional : "Provisional NRT data"}
            </Badge>
          )}
        </div>

        {/* Historical Climatology Reference: Typical vs High Danger */}
        {climatology && (
          <div className="rounded-lg border border-[#1f293d] bg-[#080b10] p-3 space-y-2">
            <div className="flex items-center justify-between font-semibold text-xs text-[#f8fafc] border-b border-[#1f293d] pb-1.5">
              <span>Historical {monthName} Baseline</span>
              <span className="text-[10px] text-[#ff8533] font-normal">
                {isBangla ? "২৫ বছরের তুলনা" : "25-Yr Comparison"}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 font-mono text-xs pt-1">
              <div className="p-1.5 rounded bg-[#141e30] border border-[#21304b]">
                <span className="text-[#64748b] block text-[10px] font-sans">
                  {isBangla ? t.calendar.drawer_mean : "Normal Average (Mean):"}
                </span>
                <span className="text-[#f8fafc] font-bold">
                  {formatNumber(Math.round(climatology.mean))}
                </span>
              </div>
              <div className="p-1.5 rounded bg-[#141e30] border border-[#21304b]">
                <span className="text-[#64748b] block text-[10px] font-sans">
                  {isBangla ? t.calendar.drawer_median : "Typical Median (p50):"}
                </span>
                <span className="text-[#f8fafc] font-bold">
                  {formatNumber(Math.round(climatology.p50))}
                </span>
              </div>
              <div className="p-1.5 rounded bg-[#141e30] border border-[#21304b]">
                <span className="text-[#f59e0b] block text-[10px] font-sans">
                  {isBangla ? t.calendar.drawer_warning_level : "High Warning (p90):"}
                </span>
                <span className="text-[#f59e0b] font-bold">
                  {formatNumber(Math.round(climatology.p90))}
                </span>
              </div>
              <div className="p-1.5 rounded bg-[#141e30] border border-[#21304b]">
                <span className="text-[#ef4444] block text-[10px] font-sans">
                  {isBangla ? t.calendar.drawer_extreme_level : "Severe Danger (p95):"}
                </span>
                <span className="text-[#ef4444] font-bold">
                  {formatNumber(Math.round(climatology.p95))}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Practical Rural Field Safety Advice Box */}
        <div className="rounded-lg border border-[#ff6b00]/30 bg-[#141e30] p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 font-semibold text-xs text-[#ff8533]">
            <span>🛡️</span>
            <span>{t.calendar.drawer_advice_title}</span>
          </div>
          <p className="text-[11px] text-[#cbd5e1] leading-relaxed">
            {adviceText}
          </p>
          <div className="pt-1 text-[11px] text-amber-300 font-medium flex items-center gap-1.5 border-t border-[#21304b]">
            <span>🚨</span>
            <span>
              {isBangla
                ? "জরুরি ফায়ার সার্ভিস হেল্পলাইন: ৯৯৯ অথবা ১০২"
                : "Emergency Fire Service Helpline: Call 999 or 102"}
            </span>
          </div>
        </div>
      </div>
    </Sheet>
  );
}
