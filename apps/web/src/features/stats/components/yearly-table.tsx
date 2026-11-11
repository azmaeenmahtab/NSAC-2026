"use client";

import React, { useState } from "react";
import { formatMonthFull, formatNumber } from "@/lib/format";
import { RankBadge } from "./rank-badge";
import type { YearlyStatRow, SortField, SortDirection } from "../types";

interface YearlyTableProps {
  data: YearlyStatRow[];
  selectedYear?: number | null;
  onSelectYear?: (year: number) => void;
}

export function YearlyTable({ data, selectedYear, onSelectYear }: YearlyTableProps) {
  const [sortField, setSortField] = useState<SortField>("year");
  const [sortDir, setSortDir] = useState<SortDirection>("desc");

  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir(field === "rank" ? "asc" : "desc");
    }
  }

  const sortedData = [...data].sort((a, b) => {
    let aVal = 0;
    let bVal = 0;

    switch (sortField) {
      case "year":
        aVal = a.year;
        bVal = b.year;
        break;
      case "harmonized_total":
        aVal = a.harmonized_total ?? a.total_events ?? 0;
        bVal = b.harmonized_total ?? b.total_events ?? 0;
        break;
      case "frp_sum":
        aVal = a.frp_sum ?? a.total_frp_mw ?? 0;
        bVal = b.frp_sum ?? b.total_frp_mw ?? 0;
        break;
      case "rank":
        aVal = a.rank;
        bVal = b.rank;
        break;
      case "vs_mean_pct":
        aVal = a.vs_mean_pct;
        bVal = b.vs_mean_pct;
        break;
      case "peak_month":
        aVal = a.peak_month;
        bVal = b.peak_month;
        break;
    }

    return sortDir === "asc" ? aVal - bVal : bVal - aVal;
  });

  return (
    <div className="bg-[#0e1626]/80 border border-[#1e293b] rounded-xl overflow-hidden">
      <div className="p-4 border-b border-[#1e293b] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-[#f1f5f9] tracking-wide">
            Historical Annual Statistics
          </h3>
          <p className="text-xs text-[#94a3b8]">
            Calibrated harmonized activity table (sorted by {sortField}{" "}
            {sortDir === "asc" ? "↑" : "↓"})
          </p>
        </div>
        <div className="text-xs text-[#64748b]">
          Units:{" "}
          <span className="text-[#FF6B00] font-medium">
            MODIS-equivalent fire events
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left">
          <thead className="bg-[#121b2f] text-[#94a3b8] uppercase tracking-wider border-b border-[#1e293b]">
            <tr>
              <th scope="col" className="py-3 px-4">
                <button
                  type="button"
                  onClick={() => handleSort("year")}
                  className="font-medium hover:text-white flex items-center gap-1"
                >
                  Year {sortField === "year" ? (sortDir === "asc" ? "▲" : "▼") : ""}
                </button>
              </th>
              <th scope="col" className="py-3 px-4">
                <button
                  type="button"
                  onClick={() => handleSort("harmonized_total")}
                  className="font-medium hover:text-white flex items-center gap-1"
                >
                  Total Events{" "}
                  {sortField === "harmonized_total"
                    ? sortDir === "asc"
                      ? "▲"
                      : "▼"
                    : ""}
                </button>
              </th>
              <th scope="col" className="py-3 px-4">
                <button
                  type="button"
                  onClick={() => handleSort("frp_sum")}
                  className="font-medium hover:text-white flex items-center gap-1"
                >
                  FRP Sum (MW){" "}
                  {sortField === "frp_sum" ? (sortDir === "asc" ? "▲" : "▼") : ""}
                </button>
              </th>
              <th scope="col" className="py-3 px-4">
                <button
                  type="button"
                  onClick={() => handleSort("rank")}
                  className="font-medium hover:text-white flex items-center gap-1"
                >
                  Rank {sortField === "rank" ? (sortDir === "asc" ? "▲" : "▼") : ""}
                </button>
              </th>
              <th scope="col" className="py-3 px-4">
                <button
                  type="button"
                  onClick={() => handleSort("vs_mean_pct")}
                  className="font-medium hover:text-white flex items-center gap-1"
                >
                  Vs Mean (%){" "}
                  {sortField === "vs_mean_pct"
                    ? sortDir === "asc"
                      ? "▲"
                      : "▼"
                    : ""}
                </button>
              </th>
              <th scope="col" className="py-3 px-4">
                <button
                  type="button"
                  onClick={() => handleSort("peak_month")}
                  className="font-medium hover:text-white flex items-center gap-1"
                >
                  Peak Month{" "}
                  {sortField === "peak_month"
                    ? sortDir === "asc"
                      ? "▲"
                      : "▼"
                    : ""}
                </button>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#161f30]">
            {sortedData.map((row) => {
              const isSelected = selectedYear === row.year;
              const totalVal = row.harmonized_total ?? row.total_events ?? 0;
              const frpVal = row.frp_sum ?? row.total_frp_mw ?? 0;
              return (
                <tr
                  key={`yearly-${row.year}`}
                  onClick={() => onSelectYear && onSelectYear(row.year)}
                  className={`hover:bg-[#1a253a]/60 cursor-pointer transition-colors ${
                    isSelected ? "bg-[#1f2e4a] font-medium" : ""
                  }`}
                >
                  <td className="py-2.5 px-4 text-[#f1f5f9] font-medium">
                    {row.year}
                  </td>
                  <td className="py-2.5 px-4 text-[#FF6B00] tabular-nums font-medium">
                    {formatNumber(totalVal)}
                  </td>
                  <td className="py-2.5 px-4 text-[#cbd5e1] tabular-nums">
                    {formatNumber(frpVal, 1)}
                  </td>
                  <td className="py-2.5 px-4">
                    <RankBadge rank={row.rank} />
                  </td>
                  <td className="py-2.5 px-4 tabular-nums">
                    <span
                      className={
                        row.vs_mean_pct >= 0 ? "text-[#ef4444]" : "text-[#10b981]"
                      }
                    >
                      {row.vs_mean_pct >= 0 ? "+" : ""}
                      {row.vs_mean_pct.toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-[#94a3b8]">
                    {formatMonthFull(row.peak_month)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

