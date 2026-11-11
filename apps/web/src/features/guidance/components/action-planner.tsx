"use client";

import React, { useState } from "react";
import { formatMonthFull } from "@/lib/format";
import { useGuidance } from "../api/use-guidance";
import { StageBadge } from "./stage-badge";
import { Checklist } from "./checklist";
import { GuidanceDisclaimer } from "./guidance-disclaimer";
import type { ActionPlannerProps, AudienceFilter } from "../types";

export function ActionPlanner({
  areaId,
  areaName,
  month = new Date().getMonth() + 1,
  stage = "in_season",
}: ActionPlannerProps) {
  const [activeAudience, setActiveAudience] = useState<AudienceFilter>("all");
  const { data: guidanceItems = [], isLoading, error } = useGuidance(areaId, month);

  const filteredItems = guidanceItems.filter((item) => {
    if (activeAudience === "all") return true;
    return item.audience.toLowerCase().includes(activeAudience);
  });

  const monthName = formatMonthFull(month);

  function handlePrint() {
    if (typeof window !== "undefined") {
      window.print();
    }
  }

  return (
    <section
      data-testid="action-planner"
      aria-label="Wildland Action Planner"
      className="bg-[#0e1626]/90 border border-[#1e293b] rounded-xl p-4 sm:p-6 space-y-5 print:border-none print:p-0 print:bg-white print:text-black"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1e293b] pb-4 print:border-black">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5 flex-wrap">
            <h2 className="text-base font-semibold text-[#f1f5f9] tracking-tight print:text-black">
              Wildland Action Planner
            </h2>
            <StageBadge stage={stage} />
          </div>
          <p className="text-xs text-[#94a3b8] print:text-gray-700">
            Preparedness protocol for{" "}
            <span className="text-[#FF6B00] font-medium">{monthName}</span>
            {areaName ? ` in ${areaName}` : ` (${areaId})`}
          </p>
        </div>

        <button
          type="button"
          onClick={handlePrint}
          className="self-start sm:self-auto inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#162238] hover:bg-[#1f2e4a] text-[#cbd5e1] hover:text-white border border-[#2b3d5c] transition-colors print:hidden"
          title="Print or export checklist to PDF"
        >
          <span aria-hidden="true">🖨</span>
          <span>Printable Checklist</span>
        </button>
      </div>

      <div className="flex items-center gap-2 overflow-x-auto pb-1 print:hidden">
        {(
          [
            { id: "all", label: "All Audiences" },
            { id: "community", label: "Community" },
            { id: "land_manager", label: "Land Managers" },
            { id: "responder", label: "Responders" },
          ] as const
        ).map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveAudience(tab.id)}
            className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
              activeAudience === tab.id
                ? "bg-[#FF6B00] text-white"
                : "bg-[#161f30] text-[#94a3b8] hover:text-white hover:bg-[#1e293b]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {isLoading && (
        <div className="py-8 text-center text-xs text-[#94a3b8] animate-pulse">
          Loading preparedness action checklist...
        </div>
      )}

      {error && (
        <div className="py-4 px-3 rounded bg-red-950/30 border border-red-800/40 text-xs text-red-300">
          Failed to load action checklist for this area.
        </div>
      )}

      {!isLoading && !error && (
        <Checklist
          items={filteredItems}
          emptyMessage={`No specific ${activeAudience !== "all" ? activeAudience : ""} actions found for this period.`}
        />
      )}

      <GuidanceDisclaimer />
    </section>
  );
}
