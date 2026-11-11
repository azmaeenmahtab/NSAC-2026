"use client";

import React, { Suspense } from "react";
import dynamic from "next/dynamic";
import { AppShell } from "@/components/layout/app-shell";
import { SidePanelContent } from "@/features/shell";
import { FireCalendar } from "@/features/calendar";
import { SeriesChart } from "@/features/series";
import { YearlyBars, YearlyTable, useYearlyStats } from "@/features/stats";
import { ActionPlanner } from "@/features/guidance";
import { useViewState } from "@/features/areas";
import { cn } from "@/lib/utils";

const FireMap = dynamic(() => import("@/features/map").then((m) => m.FireMap), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center p-6 text-center">
      <div className="max-w-md space-y-2 rounded-xl border border-[#1f293d] bg-[#0e141f] p-8">
        <div className="text-2xl animate-pulse">🔥</div>
        <h2 className="text-sm font-semibold text-[#f8fafc]">
          Initializing Hex Map Viewport...
        </h2>
      </div>
    </div>
  ),
});

type ViewMode = "map" | "calendar" | "series" | "stats" | "planner";

function YearlyStatsView({ areaId }: { areaId: string }) {
  const { data: stats = [], isLoading, error } = useYearlyStats(areaId);
  const [selectedYear, setSelectedYear] = React.useState<number | null>(null);

  if (isLoading) {
    return (
      <div className="py-12 text-center text-xs text-[#94a3b8] animate-pulse">
        Loading historical annual statistics...
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-6 px-4 rounded-xl bg-red-950/30 border border-red-800/40 text-xs text-red-300">
        Failed to load annual statistics for this area.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <YearlyBars
        data={stats}
        selectedYear={selectedYear}
        onSelectYear={setSelectedYear}
      />
      <YearlyTable
        data={stats}
        selectedYear={selectedYear}
        onSelectYear={setSelectedYear}
      />
    </div>
  );
}

function MainContent() {
  const [viewMode, setViewMode] = React.useState<ViewMode>("map");
  const { area } = useViewState();

  return (
    <AppShell
      sidePanelTitle="Analytical Telemetry"
      sidePanelContent={<SidePanelContent />}
    >
      <div className="relative flex flex-1 flex-col h-full overflow-hidden">
        {/* View Switcher Segmented Control Bar */}
        <div className="z-20 flex items-center justify-between border-b border-[#1f293d] bg-[#0e141f]/90 px-4 py-2 backdrop-blur-md">
          <div className="flex items-center gap-1 rounded-lg bg-[#080b10] p-1 border border-[#1f293d] overflow-x-auto">
            <button
              type="button"
              onClick={() => setViewMode("map")}
              className={cn(
                "rounded px-3 py-1 text-xs font-medium transition-colors cursor-pointer whitespace-nowrap",
                viewMode === "map"
                  ? "bg-[#ff6b00] text-white font-semibold shadow-xs"
                  : "text-[#94a3b8] hover:text-[#f8fafc]"
              )}
            >
              🗺️ Hex Map
            </button>
            <button
              type="button"
              onClick={() => setViewMode("calendar")}
              className={cn(
                "rounded px-3 py-1 text-xs font-medium transition-colors cursor-pointer whitespace-nowrap",
                viewMode === "calendar"
                  ? "bg-[#ff6b00] text-white font-semibold shadow-xs"
                  : "text-[#94a3b8] hover:text-[#f8fafc]"
              )}
            >
              📅 FireCalendar
            </button>
            <button
              type="button"
              onClick={() => setViewMode("series")}
              className={cn(
                "rounded px-3 py-1 text-xs font-medium transition-colors cursor-pointer whitespace-nowrap",
                viewMode === "series"
                  ? "bg-[#ff6b00] text-white font-semibold shadow-xs"
                  : "text-[#94a3b8] hover:text-[#f8fafc]"
              )}
            >
              📈 The Hidden Jump
            </button>
            <button
              type="button"
              onClick={() => setViewMode("stats")}
              className={cn(
                "rounded px-3 py-1 text-xs font-medium transition-colors cursor-pointer whitespace-nowrap",
                viewMode === "stats"
                  ? "bg-[#ff6b00] text-white font-semibold shadow-xs"
                  : "text-[#94a3b8] hover:text-[#f8fafc]"
              )}
            >
              📊 Annual Stats
            </button>
            <button
              type="button"
              onClick={() => setViewMode("planner")}
              className={cn(
                "rounded px-3 py-1 text-xs font-medium transition-colors cursor-pointer whitespace-nowrap",
                viewMode === "planner"
                  ? "bg-[#ff6b00] text-white font-semibold shadow-xs"
                  : "text-[#94a3b8] hover:text-[#f8fafc]"
              )}
            >
              🛡️ Action Planner
            </button>
          </div>

          <div className="hidden lg:flex items-center gap-2 text-xs text-[#64748b]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#ff6b00]" />
            <span>Harmonized 2000–Present Active Fire Baseline</span>
          </div>
        </div>

        {/* Viewports */}
        <div className="relative flex-1 overflow-auto bg-[#080b10]">
          {viewMode === "map" && <FireMap />}
          {viewMode === "calendar" && (
            <div className="max-w-7xl mx-auto p-4">
              <FireCalendar />
            </div>
          )}
          {viewMode === "series" && (
            <div className="max-w-7xl mx-auto p-4">
              <SeriesChart />
            </div>
          )}
          {viewMode === "stats" && (
            <div className="max-w-7xl mx-auto p-4">
              <YearlyStatsView areaId={area} />
            </div>
          )}
          {viewMode === "planner" && (
            <div className="max-w-5xl mx-auto p-4">
              <ActionPlanner areaId={area} />
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-[#080b10] text-[#f8fafc]">
          Loading PyroScope...
        </div>
      }
    >
      <MainContent />
    </Suspense>
  );
}
