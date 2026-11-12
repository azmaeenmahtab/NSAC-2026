"use client";

import React, { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { formatNumber } from "@/lib/format";
import { useLanguage } from "@/lib/i18n";
import type { YearlyStatRow } from "../types";

interface YearlyBarsProps {
  data: YearlyStatRow[];
  selectedYear?: number | null;
  onSelectYear?: (year: number) => void;
}

export function YearlyBars({ data, selectedYear, onSelectYear }: YearlyBarsProps) {
  const [showTable, setShowTable] = useState(false);
  const { isBangla } = useLanguage();

  // Sort chronologically for chart display
  const chartData = [...data].sort((a, b) => a.year - b.year);

  const peakYearRow = React.useMemo(() => {
    if (!data.length) return null;
    return [...data].reduce((max, r) => {
      const val = r.harmonized_total ?? r.total_events ?? 0;
      const maxVal = max.harmonized_total ?? max.total_events ?? 0;
      return val > maxVal ? r : max;
    }, data[0]);
  }, [data]);

  const avgAnnualEvents = React.useMemo(() => {
    if (!data.length) return 0;
    const sum = data.reduce((acc, r) => acc + (r.harmonized_total ?? r.total_events ?? 0), 0);
    return Math.round(sum / data.length);
  }, [data]);

  return (
    <div className="bg-[#0e1626]/80 border border-[#1e293b] rounded-xl p-4 sm:p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-[#f1f5f9] tracking-wide">
            Annual Burning Totals (2000–Present)
          </h3>
          <p className="text-xs text-[#94a3b8]">
            Harmonized annual activity in{" "}
            <span className="text-[#FF6B00] font-medium">
              MODIS-equivalent fire events
            </span>
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowTable(!showTable)}
          className="self-start sm:self-auto text-xs text-[#94a3b8] hover:text-[#f1f5f9] px-2.5 py-1 rounded bg-[#161f30] border border-[#23324d] transition-colors cursor-pointer"
          aria-expanded={showTable}
        >
          {showTable ? "Hide accessible table" : "Show accessible table"}
        </button>
      </div>

      {/* 3-Stat Summary Cards */}
      {data.length > 0 && (
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="p-2 rounded-lg bg-[#141e30] border border-[#21304b]">
            <span className="text-[10px] text-[#64748b] uppercase font-mono block">
              {isBangla ? "সময়কাল" : "Timeline"}
            </span>
            <span className="text-sm font-bold text-white font-mono">
              {data.length} {isBangla ? "বছর" : "Years"}
            </span>
          </div>
          <div className="p-2 rounded-lg bg-[#141e30] border border-[#21304b]">
            <span className="text-[10px] text-[#64748b] uppercase font-mono block">
              {isBangla ? "সর্বোচ্চ বছর" : "Peak Year"}
            </span>
            <span className="text-sm font-bold text-[#ef4444] font-mono">
              {peakYearRow?.year || "—"}
            </span>
          </div>
          <div className="p-2 rounded-lg bg-[#141e30] border border-[#21304b]">
            <span className="text-[10px] text-[#64748b] uppercase font-mono block">
              {isBangla ? "বাৎসরিক গড়" : "Average / Yr"}
            </span>
            <span className="text-sm font-bold text-[#ff8533] font-mono">
              {formatNumber(avgAnnualEvents)}
            </span>
          </div>
        </div>
      )}

      {/* Plain Language Explainer */}
      <div className="rounded-lg bg-[#141e30] border border-[#21304b] p-2.5 text-[11px] text-[#94a3b8]">
        <strong className="text-white">
          {isBangla ? "💡 কীভাবে পড়বেন: " : "💡 How to Read: "}
        </strong>
        {isBangla
          ? "এই চার্টে প্রতিটি স্তম্ভ নির্দেশ করে ওই বছরে মোট কতগুলো আগুনের ঘটনা ঘটেছে। উঁচু স্তম্ভ মানে সেই বছরে বেশি আগুন লেগেছিল। লাল রঙের চিহ্নিত স্তম্ভটি ছিল সবচেয়ে ভয়াবহ বছর।"
          : "Each bar shows the total fire events in that year across the selected region. Taller bars indicate unusually dry, high-fire years."}
      </div>

      <div className="h-56 w-full" aria-label="Annual fire activity bar chart">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <XAxis
              dataKey="year"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: "#1e293b" }}
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: "#1e293b" }}
              tickFormatter={(v: number) => formatNumber(v)}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const row = payload[0].payload as YearlyStatRow;
                const val = row.harmonized_total ?? row.total_events ?? 0;
                return (
                  <div className="bg-[#0b1322] border border-[#22314d] px-3 py-2 rounded-lg shadow-xl text-xs space-y-1">
                    <p className="font-semibold text-white">{row.year}</p>
                    <p className="text-[#FF6B00]">
                      {formatNumber(val)} MODIS-equivalent fire events
                    </p>
                    <p className="text-[#94a3b8]">
                      {isBangla ? `ঐতিহাসিক অবস্থান: #${row.rank}` : `Historical Rank: #${row.rank}`}
                    </p>
                    <p
                      className={
                        row.vs_mean_pct >= 0 ? "text-[#ef4444]" : "text-[#10b981]"
                      }
                    >
                      {row.vs_mean_pct >= 0 ? "+" : ""}
                      {row.vs_mean_pct.toFixed(1)}%{" "}
                      {isBangla ? "গড়ের চেয়ে" : "vs historical mean"}
                    </p>
                  </div>
                );
              }}
            />
            <Bar
              dataKey="harmonized_total"
              radius={[4, 4, 0, 0]}
              onClick={(entry) => onSelectYear && onSelectYear((entry as unknown as YearlyStatRow).year)}
              cursor="pointer"
            >
              {chartData.map((entry) => {
                const isSelected = selectedYear === entry.year;
                const isPeak = peakYearRow?.year === entry.year;
                const fillColor = isSelected
                  ? "#ff8533"
                  : isPeak
                    ? "#ef4444"
                    : "#ff6b00";
                return (
                  <Cell
                    key={entry.year}
                    fill={fillColor}
                    fillOpacity={isSelected ? 1 : isPeak ? 0.95 : 0.75}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Accessible Table Fallback */}
      {showTable && (
        <div className="pt-2 overflow-x-auto">
          <table
            className="w-full text-left text-xs border border-[#1e293b] rounded-lg"
            aria-label="Accessible yearly fire activity table"
          >
            <thead className="bg-[#141e30] text-[#94a3b8] uppercase font-mono text-[10px]">
              <tr>
                <th className="p-2 border-b border-[#1e293b]">Year</th>
                <th className="p-2 border-b border-[#1e293b]">Events</th>
                <th className="p-2 border-b border-[#1e293b]">Peak Month</th>
                <th className="p-2 border-b border-[#1e293b]">Rank</th>
                <th className="p-2 border-b border-[#1e293b]">vs Mean</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b]">
              {chartData.map((row) => (
                <tr
                  key={row.year}
                  className={`hover:bg-[#162238] transition-colors cursor-pointer ${
                    selectedYear === row.year ? "bg-[#1c2942]" : ""
                  }`}
                  onClick={() => onSelectYear && onSelectYear(row.year)}
                >
                  <td className="p-2 font-mono font-semibold text-white">{row.year}</td>
                  <td className="p-2 font-mono text-[#ff8533]">
                    {formatNumber(row.harmonized_total ?? row.total_events ?? 0)}
                  </td>
                  <td className="p-2 text-[#cbd5e1]">{row.peak_month ?? "—"}</td>
                  <td className="p-2 text-[#94a3b8]">#{row.rank}</td>
                  <td
                    className={`p-2 font-mono ${
                      row.vs_mean_pct >= 0 ? "text-[#ef4444]" : "text-[#10b981]"
                    }`}
                  >
                    {row.vs_mean_pct >= 0 ? "+" : ""}
                    {row.vs_mean_pct.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
