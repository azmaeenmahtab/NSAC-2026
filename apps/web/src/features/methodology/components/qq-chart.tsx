"use client";

import * as React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import type { QQPoint } from "../types";
import { Button } from "@/components/ui/button";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface QQChartProps {
  data?: QQPoint[];
  className?: string;
}

const DEFAULT_QQ: QQPoint[] = [
  { quantile: 0.05, modis: 5, viirs_raw: 15, viirs_harmonized: 5 },
  { quantile: 0.25, modis: 12, viirs_raw: 36, viirs_harmonized: 12 },
  { quantile: 0.5, modis: 28, viirs_raw: 84, viirs_harmonized: 28 },
  { quantile: 0.75, modis: 65, viirs_raw: 195, viirs_harmonized: 65 },
  { quantile: 0.9, modis: 120, viirs_raw: 360, viirs_harmonized: 120 },
  { quantile: 0.95, modis: 180, viirs_raw: 540, viirs_harmonized: 180 },
  { quantile: 0.99, modis: 240, viirs_raw: 720, viirs_harmonized: 240 },
];

export function QQChart({ data = DEFAULT_QQ, className }: QQChartProps) {
  const [showTable, setShowTable] = React.useState(false);

  // Format data for chart plotting (x = modis quantile value)
  const chartData = React.useMemo(() => {
    return data.map((pt) => ({
      ...pt,
      label: `p${Math.round(pt.quantile * 100)}`,
      oneToOne: pt.modis, // y = x reference
    }));
  }, [data]);

  return (
    <div
      role="region"
      aria-label="Quantile-Quantile empirical distribution plot"
      data-testid="qq-chart"
      className={cn(
        "rounded-xl border border-[#1f293d] bg-[#0e141f] p-4 text-xs text-[#f8fafc] shadow-sm space-y-3",
        className
      )}
    >
      <div className="flex items-center justify-between pb-2 border-b border-[#1f293d]/60">
        <div>
          <h3 className="text-sm font-semibold text-[#f8fafc]">
            Quantile-Quantile (Q-Q) Distribution Alignment
          </h3>
          <p className="text-[11px] text-[#94a3b8]">
            Comparing VIIRS against MODIS event counts before (3× mismatch) and after harmonization (1:1 alignment)
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowTable((v) => !v)}
          className="h-7 text-xs font-medium"
        >
          {showTable ? "Show Chart" : "View Data Table"}
        </Button>
      </div>

      {showTable ? (
        <div className="overflow-x-auto rounded border border-[#1f293d] bg-[#080b10] max-h-72">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-[#1f293d] text-[10px] text-[#64748b]">
                <th className="p-2">Percentile</th>
                <th className="p-2">MODIS Reference</th>
                <th className="p-2">Raw VIIRS</th>
                <th className="p-2">Harmonized VIIRS</th>
                <th className="p-2">Residual Bias</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1f293d]/40">
              {chartData.map((pt) => (
                <tr key={pt.label} className="hover:bg-[#161f30]/40">
                  <td className="p-2 text-[#94a3b8]">{pt.label}</td>
                  <td className="p-2 text-[#f8fafc] font-semibold">{formatNumber(pt.modis)}</td>
                  <td className="p-2 text-[#a855f7]">{formatNumber(pt.viirs_raw)}</td>
                  <td className="p-2 text-[#ff6b00] font-semibold">
                    {formatNumber(pt.viirs_harmonized)}
                  </td>
                  <td className="p-2 text-emerald-400">
                    {pt.viirs_harmonized - pt.modis === 0
                      ? "0.0"
                      : (pt.viirs_harmonized - pt.modis).toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="h-64 w-full" data-testid="recharts-qq-container">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
              <XAxis
                dataKey="modis"
                name="MODIS Events"
                stroke="#64748b"
                fontSize={10}
                label={{
                  value: "MODIS Empirical Quantile",
                  position: "insideBottom",
                  offset: -10,
                  fill: "#64748b",
                  fontSize: 10,
                }}
              />
              <YAxis
                stroke="#64748b"
                fontSize={10}
                label={{
                  value: "VIIRS Count",
                  angle: -90,
                  position: "insideLeft",
                  fill: "#64748b",
                  fontSize: 10,
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#080b10",
                  borderColor: "#2d3b55",
                  fontSize: "11px",
                  borderRadius: "6px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
              {/* 1:1 Identity Reference Line */}
              <Line
                type="monotone"
                dataKey="oneToOne"
                name="Ideal 1:1 Line (y = x)"
                stroke="#64748b"
                strokeDasharray="4 4"
                dot={false}
              />
              {/* Raw VIIRS */}
              <Line
                type="monotone"
                dataKey="viirs_raw"
                name="Raw VIIRS (Discontinuous)"
                stroke="#a855f7"
                strokeWidth={1.5}
                dot={{ r: 3, fill: "#a855f7" }}
              />
              {/* Harmonized VIIRS */}
              <Line
                type="monotone"
                dataKey="viirs_harmonized"
                name="Harmonized VIIRS (Calibrated)"
                stroke="#ff6b00"
                strokeWidth={2}
                dot={{ r: 4, fill: "#ff6b00" }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
