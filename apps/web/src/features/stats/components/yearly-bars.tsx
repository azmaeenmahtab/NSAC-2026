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
import type { YearlyStatRow } from "../types";

interface YearlyBarsProps {
  data: YearlyStatRow[];
  selectedYear?: number | null;
  onSelectYear?: (year: number) => void;
}

export function YearlyBars({ data, selectedYear, onSelectYear }: YearlyBarsProps) {
  const [showTable, setShowTable] = useState(false);

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
          className="self-start sm:self-auto text-xs text-[#94a3b8] hover:text-[#f1f5f9] px-2.5 py-1 rounded bg-[#161f30] border border-[#23324d] transition-colors"
          aria-expanded={showTable}
        >
          {showTable ? "Hide accessible table" : "Show accessible table"}
        </button>
      </div>

      {/* 3-Stat Summary Cards */}
      {data.length > 0 && (
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="p-2 rounded-lg bg-[#141e30] border border-[#21304b]">
            <span className="text-[10px] text-[#64748b] uppercase font-mono block">Timeline</span>
            <span className="text-sm font-bold text-white font-mono">{data.length} Years</span>
          </div>
          <div className="p-2 rounded-lg bg-[#141e30] border border-[#21304b]">
            <span className="text-[10px] text-[#64748b] uppercase font-mono block">Peak Year</span>
            <span className="text-sm font-bold text-[#ef4444] font-mono">
              {peakYearRow?.year || "—"}
            </span>
          </div>
          <div className="p-2 rounded-lg bg-[#141e30] border border-[#21304b]">
            <span className="text-[10px] text-[#64748b] uppercase font-mono block">Average / Yr</span>
            <span className="text-sm font-bold text-[#ff8533] font-mono">
              {formatNumber(avgAnnualEvents)}
            </span>
          </div>
        </div>
      )}

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
                    <p className="text-[#94a3b8]">Historical Rank: #{row.rank}</p>
                    <p
                      className={
                        row.vs_mean_pct >= 0 ? "text-[#ef4444]" : "text-[#10b981]"
                      }
                    >
                      {row.vs_mean_pct >= 0 ? "+" : ""}
                      {row.vs_mean_pct.toFixed(1)}% vs historical mean
                    </p>
                  </div>
                );
              }}
            />
            <Bar
              dataKey={(d: YearlyStatRow) => d.harmonized_total ?? d.total_events ?? 0}
              radius={[4, 4, 0, 0]}
              onClick={(entry) => {
                const row = entry as unknown as { year?: number; payload?: { year?: number } };
                const yr = row?.year ?? row?.payload?.year;
                if (yr && onSelectYear) onSelectYear(yr);
              }}
              className="cursor-pointer"
            >
              {chartData.map((entry) => {
                const isSelected = selectedYear === entry.year;
                return (
                  <Cell
                    key={`bar-${entry.year}`}
                    fill={isSelected ? "#FF6B00" : "#3b82f6"}
                    fillOpacity={isSelected ? 1.0 : 0.75}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {showTable && (
        <div className="mt-4 border-t border-[#1e293b] pt-3 overflow-x-auto">
          <table className="w-full text-xs text-left text-[#cbd5e1]">
            <caption className="sr-only">Annual fire totals by year</caption>
            <thead className="text-[#64748b] uppercase border-b border-[#1e293b]">
              <tr>
                <th scope="col" className="py-2 px-3">Year</th>
                <th scope="col" className="py-2 px-3">Harmonized Total</th>
                <th scope="col" className="py-2 px-3">Rank</th>
                <th scope="col" className="py-2 px-3">Vs Mean</th>
              </tr>
            </thead>
            <tbody>
              {chartData.map((row) => (
                <tr key={`acc-bar-${row.year}`} className="border-b border-[#161f30]">
                  <td className="py-2 px-3 font-medium text-white">{row.year}</td>
                  <td className="py-2 px-3">
                    {formatNumber(row.harmonized_total ?? row.total_events ?? 0)}
                  </td>
                  <td className="py-2 px-3">#{row.rank}</td>
                  <td className="py-2 px-3">
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
