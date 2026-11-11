"use client";

import React, { Suspense } from "react";
import dynamic from "next/dynamic";
import { AppShell } from "@/components/layout/app-shell";
import { SidePanelContent } from "@/features/shell";

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

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-[#080b10] text-[#f8fafc]">
          Loading PyroScope...
        </div>
      }
    >
      <AppShell
        sidePanelTitle="Analytical Telemetry"
        sidePanelContent={<SidePanelContent />}
      >
        <FireMap />
      </AppShell>
    </Suspense>
  );
}
