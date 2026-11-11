"use client";

import React, { Suspense } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { SidePanelContent } from "@/features/shell";
import { SeriesChart } from "@/features/series";

export default function HiddenJumpPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-[#080b10] text-[#f8fafc]">
          Loading Hidden Jump Analysis...
        </div>
      }
    >
      <AppShell
        activeTab="hidden-jump"
        sidePanelTitle="Analytical Telemetry"
        sidePanelContent={<SidePanelContent />}
      >
        <div className="flex-1 overflow-auto bg-[#080b10] p-4 sm:p-6">
          <div className="max-w-6xl mx-auto space-y-4">
            <SeriesChart />
          </div>
        </div>
      </AppShell>
    </Suspense>
  );
}

