"use client";

import React, { Suspense } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { AskPanel } from "@/features/ask";

export default function AskPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-[#080b10] text-[#f8fafc]">
          Loading Ask PyroScope...
        </div>
      }
    >
      <AppShell activeTab="ask">
        <div className="flex-1 overflow-hidden p-4 md:p-6 bg-[#080b10]">
          <div className="mx-auto h-[calc(100vh-6rem)] max-w-4xl">
            <AskPanel className="h-full" />
          </div>
        </div>
      </AppShell>
    </Suspense>
  );
}
