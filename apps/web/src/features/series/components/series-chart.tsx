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
} from "recharts";
import { useSeries, useMethodologyJump } from "../api/use-series";
import type { SeriesVisibility } from "../types";
import { SeriesToggles } from "./series-toggles";
import { OverlapMarker } from "./overlap-marker";
import { JumpCaption } from "./jump-caption";
import { QueryBoundary } from "@/components/feedback/query-boundary";
import { Button } from "@/components/ui/button";
import { useViewState } from "@/features/areas";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

export function SeriesChart({ className }: { className?: string }) {
  const { area, from, to } = useViewState();
  const { data: seriesEnvelope, isLoading, isError, error, refetch } = useSeries({ area, from, to });
  const { data: jumpEnvelope } = useMethodologyJump();

  const [visibility, setVisibility] = React.useState<SeriesVisibility>({
    raw_modis: true,
    raw_viirs: true,
    naive_splice: true,
    harmonized: true,
  });
  const [storyStep, setStoryStep] = React.useState(0);
  const [showTable, setShowTable] = React.useState(false);

  const series = React.useMemo(() => seriesEnvelope?.data || [], [seriesEnvelope?.data]);
  const jumpMetrics = jumpEnvelope?.data;

  // Format chart data with date string "YYYY-MM"
  const chartData = React.useMemo(() => {
    return series.map((pt) => ({
      ...pt,
      date: `${pt.year}-${String(pt.month).padStart(2, "0")}`,
    }));
  }, [series]);

  return (
    <QueryBoundary
      isLoading={isLoading}
      isError={isError}
      error={error}
      onRetry={refetch}
      isEmpty={series.length === 0}
    >
      <div
        className={cn("flex flex-col gap-4 p-4 text-[#f8fafc]", className)}
        data-testid="series-chart"
      >
        {/* Jump Analysis Banner */}
        <JumpCaption metrics={jumpMetrics} />

        {/* Toggles & Story Stepper */}
        <SeriesToggles
          visibility={visibility}
          onChange={setVisibility}
          storyStep={storyStep}
          onStoryStepChange={setStoryStep}
        />

        {/* Chart Viewport */}
        <div className="rounded-lg border border-[#1f293d] bg-[#0e141f] p-4 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-[#1f293d]/50 mb-4">
            <div>
              <h3 className="font-semibold text-sm text-[#f8fafc]">
                Long-Term Fire Activity Time Series (2000 – Present)
              </h3>
              <p className="text-[11px] text-[#94a3b8]">
                Monthly physical fire event count comparison across sensors
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowTable((v) => !v)}
              className="h-7 text-xs"
            >
              {showTable ? "Show Chart" : "View Data Table"}
            </Button>
          </div>

          {showTable ? (
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-[#1f293d] text-[#64748b]">
                    <th className="p-2">Period</th>
                    <th className="p-2">Harmonized</th>
                    <th className="p-2">Naive Splice</th>
                    <th className="p-2">Raw VIIRS</th>
                    <th className="p-2">Raw MODIS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1f293d]/40">
                  {chartData.map((pt) => (
                    <tr key={pt.date} className="hover:bg-[#161f30]/40">
                      <td className="p-2 text-[#94a3b8]">{pt.date}</td>
                      <td className="p-2 text-[#ff6b00] font-semibold">
                        {formatNumber(Math.round(pt.harmonized))}
                      </td>
                      <td className="p-2 text-[#f59e0b]">
                        {formatNumber(Math.round(pt.naive_splice))}
                      </td>
                      <td className="p-2 text-[#a855f7]">
                        {pt.raw_viirs !== null ? formatNumber(Math.round(pt.raw_viirs!)) : "—"}
                      </td>
                      <td className="p-2 text-[#f97316]">
                        {pt.raw_modis !== null ? formatNumber(Math.round(pt.raw_modis!)) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="h-80 w-full" data-testid="recharts-container">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
                  <XAxis
                    dataKey="date"
                    stroke="#64748b"
                    fontSize={10}
                    tickFormatter={(val: string) => (val.endsWith("-01") ? val.slice(0, 4) : "")}
                  />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#080b10",
                      borderColor: "#2d3b55",
                      fontSize: "11px",
                      borderRadius: "6px",
                    }}
                  />
                  <OverlapMarker />
                  {visibility.raw_modis && (
                    <Line
                      type="monotone"
                      dataKey="raw_modis"
                      name="Raw MODIS"
                      stroke="#f97316"
                      strokeWidth={1.5}
                      dot={false}
                    />
                  )}
                  {visibility.raw_viirs && (
                    <Line
                      type="monotone"
                      dataKey="raw_viirs"
                      name="Raw VIIRS"
                      stroke="#a855f7"
                      strokeWidth={1.5}
                      dot={false}
                    />
                  )}
                  {visibility.naive_splice && (
                    <Line
                      type="monotone"
                      dataKey="naive_splice"
                      name="Naive Splice"
                      stroke="#f59e0b"
                      strokeWidth={2}
                      strokeDasharray="4 4"
                      dot={false}
                    />
                  )}
                  {visibility.harmonized && (
                    <Line
                      type="monotone"
                      dataKey="harmonized"
                      name="Harmonized (PyroScope)"
                      stroke="#ff6b00"
                      strokeWidth={2.5}
                      dot={false}
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
    </QueryBoundary>
  );
}
