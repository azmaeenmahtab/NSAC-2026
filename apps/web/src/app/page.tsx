"use client";

import React, { Suspense, useState } from "react";
import dynamic from "next/dynamic";
import { AppShell } from "@/components/layout/app-shell";
import { SidePanelContent } from "@/features/shell";
import { FireCalendar } from "@/features/calendar";
import { SeriesChart } from "@/features/series";
import { YearlyBars, YearlyTable, useYearlyStats } from "@/features/stats";
import { ActionPlanner } from "@/features/guidance";
import { AlertBanner, SubscribeForm, useActiveAlerts } from "@/features/alerts";
import { QueryBoundary } from "@/components/feedback/query-boundary";
import { useAreas, useViewState } from "@/features/areas";
import { useLanguage } from "@/lib/i18n";
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
  const { data: stats = [], isLoading, isError, error, refetch } = useYearlyStats(areaId);
  const [selectedYear, setSelectedYear] = React.useState<number | null>(null);

  return (
    <QueryBoundary
      isLoading={isLoading}
      isError={isError}
      error={error}
      data={stats}
      onRetry={() => refetch()}
    >
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
    </QueryBoundary>
  );
}

function MainContent() {
  const [viewMode, setViewMode] = useState<ViewMode>("map");
  const [showSubscribeModal, setShowSubscribeModal] = useState(false);
  const [showGuideBanner, setShowGuideBanner] = useState(true);
  const { area, setArea } = useViewState();
  const { data: areasEnvelope } = useAreas();
  const { t, isBangla } = useLanguage();

  React.useEffect(() => {
    const list = areasEnvelope?.data;
    if (!list || list.length === 0) return;
    if (!area.startsWith("bbox:") && !list.some((a) => a.id === area)) {
      setArea(list[0].id);
    }
  }, [area, areasEnvelope?.data, setArea]);

  const { data: activeAlerts } = useActiveAlerts(area);

  return (
    <AppShell
      sidePanelTitle={t.side_panel.title}
      sidePanelContent={<SidePanelContent />}
    >
      <div className="relative flex flex-1 flex-col h-full overflow-hidden">
        {/* Active Alert Banner */}
        <AlertBanner
          areaId={area}
          alerts={activeAlerts}
          onOpenSubscribe={() => setShowSubscribeModal(true)}
        />

        {/* Non-technical Welcome & Rural Fire Awareness Guide */}
        {showGuideBanner ? (
          <div className="z-10 bg-[#0e1626] border-b border-[#1e293b] px-4 py-3 text-xs text-[#cbd5e1] transition-all">
            <div className="max-w-7xl mx-auto space-y-2.5">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-base select-none">🌾🔥</span>
                  <span className="font-semibold text-white text-xs sm:text-sm">
                    {t.intro_guide.title}
                  </span>
                  <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] font-medium bg-[#ff6b00]/15 text-[#ff8533] border border-[#ff6b00]/30">
                    {t.intro_guide.badge}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowGuideBanner(false)}
                  className="text-[11px] text-[#94a3b8] hover:text-white px-2 py-0.5 rounded hover:bg-[#162238] transition-colors cursor-pointer"
                  title="Minimize intro guide"
                >
                  {t.intro_guide.hide_btn} ✕
                </button>
              </div>

              <p className="text-[11px] sm:text-xs text-[#94a3b8] leading-relaxed">
                {t.intro_guide.subtitle}
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 pt-1">
                <button
                  type="button"
                  onClick={() => setViewMode("map")}
                  className="text-left p-2.5 rounded-lg bg-[#141e30] border border-[#21304b] hover:border-[#ff6b00]/40 transition-colors cursor-pointer space-y-1 group"
                >
                  <p className="font-semibold text-white text-xs flex items-center justify-between">
                    <span>{t.intro_guide.card1_title}</span>
                    <span className="text-[10px] text-[#ff8533] group-hover:underline">
                      {isBangla ? "দেখুন →" : "View →"}
                    </span>
                  </p>
                  <p className="text-[11px] text-[#94a3b8] leading-snug">
                    {t.intro_guide.card1_desc}
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => setViewMode("calendar")}
                  className="text-left p-2.5 rounded-lg bg-[#141e30] border border-[#21304b] hover:border-[#ff6b00]/40 transition-colors cursor-pointer space-y-1 group"
                >
                  <p className="font-semibold text-white text-xs flex items-center justify-between">
                    <span>{t.intro_guide.card2_title}</span>
                    <span className="text-[10px] text-[#ff8533] group-hover:underline">
                      {isBangla ? "দেখুন →" : "View →"}
                    </span>
                  </p>
                  <p className="text-[11px] text-[#94a3b8] leading-snug">
                    {t.intro_guide.card2_desc}
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => setViewMode("planner")}
                  className="text-left p-2.5 rounded-lg bg-[#141e30] border border-[#21304b] hover:border-[#ff6b00]/40 transition-colors cursor-pointer space-y-1 group"
                >
                  <p className="font-semibold text-white text-xs flex items-center justify-between">
                    <span>{t.intro_guide.card3_title}</span>
                    <span className="text-[10px] text-[#ff8533] group-hover:underline">
                      {isBangla ? "চেকলিস্ট →" : "Checklist →"}
                    </span>
                  </p>
                  <p className="text-[11px] text-[#94a3b8] leading-snug">
                    {t.intro_guide.card3_desc}
                  </p>
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="z-10 bg-[#0e1626]/60 border-b border-[#1e293b] px-4 py-1.5 text-[11px] flex items-center justify-between">
            <span className="text-[#94a3b8] flex items-center gap-1.5">
              <span>🌾</span>
              <span>{t.intro_guide.emergency_tag}</span>
            </span>
            <button
              type="button"
              onClick={() => setShowGuideBanner(true)}
              className="text-[#ff8533] hover:underline font-medium cursor-pointer"
            >
              {t.intro_guide.show_btn} ℹ️
            </button>
          </div>
        )}

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
              title={t.view_modes.map_desc}
            >
              {t.view_modes.map}
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
              title={t.view_modes.calendar_desc}
            >
              {t.view_modes.calendar}
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
              title={t.view_modes.series_desc}
            >
              {t.view_modes.series}
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
              title={t.view_modes.stats_desc}
            >
              {t.view_modes.stats}
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
              title={t.view_modes.planner_desc}
            >
              {t.view_modes.planner}
            </button>
          </div>

          <div className="hidden lg:flex items-center gap-2 text-xs text-[#64748b]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#ff6b00]" />
            <span>{t.view_modes.baseline_tag}</span>
          </div>
        </div>

        {/* Viewports */}
        <div className="relative flex-1 overflow-auto bg-[#080b10]">
          {viewMode === "map" && <FireMap />}
          {viewMode === "calendar" && (
            <div className="max-w-7xl mx-auto p-4 sm:p-6">
              <FireCalendar />
            </div>
          )}
          {viewMode === "series" && (
            <div className="max-w-7xl mx-auto p-4 sm:p-6">
              <SeriesChart />
            </div>
          )}
          {viewMode === "stats" && (
            <div className="max-w-7xl mx-auto p-4 sm:p-6">
              <YearlyStatsView areaId={area} />
            </div>
          )}
          {viewMode === "planner" && (
            <div className="max-w-5xl mx-auto p-4 sm:p-6">
              <ActionPlanner areaId={area} />
            </div>
          )}
        </div>

        {/* Subscribe Modal Dialog */}
        {showSubscribeModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
            <div className="relative w-full max-w-md">
              <button
                type="button"
                onClick={() => setShowSubscribeModal(false)}
                className="absolute top-3 right-3 text-[#94a3b8] hover:text-white text-sm z-10 cursor-pointer"
                aria-label="Close dialog"
              >
                ✕
              </button>
              <SubscribeForm
                areaId={area}
                onSuccess={() =>
                  setTimeout(() => setShowSubscribeModal(false), 2500)
                }
              />
            </div>
          </div>
        )}
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
