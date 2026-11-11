"use client";

import React, { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { useViewState } from "@/features/areas";

interface DemoGuideProps {
  onSelectView?: (view: "map" | "calendar" | "series" | "stats" | "planner") => void;
}

const PITCH_STEPS = [
  {
    step: 1,
    title: "1. Spatial Hex Density (Map)",
    description:
      "Explore Bangladesh & Chittagong Hill Tracts (CHT). Zoom into the H3 resolution-7 hex grid showing harmonized fire event concentrations.",
    view: "map" as const,
    actionLabel: "View Hex Map",
  },
  {
    step: 2,
    title: "2. The Hidden Jump (2012)",
    description:
      "VIIRS launched in 2012 with 375m resolution (4× sharper than MODIS 1km), creating a false 3× spike in raw counts. PyroScope's quantile mapping restores continuity.",
    view: "series" as const,
    actionLabel: "Compare 3× Jump",
  },
  {
    step: 3,
    title: "3. FireCalendar & Anomalies",
    description:
      "Inspect 26 years of monthly fire history. Notice the April–June season band and the May 2020 extreme anomaly (>95th percentile).",
    view: "calendar" as const,
    actionLabel: "Open FireCalendar",
  },
  {
    step: 4,
    title: "4. Grounded Assistant & Action Plan",
    description:
      "Ask questions grounded in typed database tools; explore sourced wildland preparedness checklists tailored by fire season stage.",
    view: "planner" as const,
    actionLabel: "Open Action Planner",
  },
];

export function DemoGuide({ onSelectView }: DemoGuideProps) {
  const searchParams = useSearchParams();
  const { setArea } = useViewState();

  const isDemoParam = searchParams.get("demo") === "1";
  const [isOpen, setIsOpen] = useState(isDemoParam);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    if (isDemoParam) {
      setArea("PRESET-CHT");
    }
  }, [isDemoParam, setArea]);

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 left-4 z-40 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#161f30] hover:bg-[#1e293b] text-white border border-[#ff6b00]/50 text-xs font-medium shadow-xl transition-all cursor-pointer"
        title="Open interactive judge & presentation demo walk-through"
      >
        <span>🎯</span>
        <span>Presentation Guide</span>
      </button>
    );
  }

  const currentStep = PITCH_STEPS[currentStepIndex];

  function handleJump(view: "map" | "calendar" | "series" | "stats" | "planner") {
    setArea("PRESET-CHT");
    if (onSelectView) onSelectView(view);
  }

  return (
    <div
      role="complementary"
      aria-label="Presentation Demo Guide"
      data-testid="demo-guide-card"
      className="fixed bottom-4 left-4 z-40 max-w-sm rounded-xl border border-[#ff6b00]/60 bg-[#0e1626]/95 backdrop-blur-md p-4 shadow-2xl text-xs space-y-3 animate-in fade-in slide-in-from-bottom-2"
    >
      <div className="flex items-center justify-between border-b border-[#1e293b] pb-2">
        <div className="flex items-center gap-1.5">
          <span className="text-sm">🎯</span>
          <span className="font-semibold text-white tracking-wide">
            PyroScope Pitch Guide
          </span>
          <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-[#ff6b00]/20 text-[#ff8533] border border-[#ff6b00]/40">
            Step {currentStepIndex + 1}/4
          </span>
        </div>
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          className="text-[#64748b] hover:text-white text-xs p-1"
          aria-label="Minimize pitch guide"
        >
          ✕
        </button>
      </div>

      <div className="space-y-1.5">
        <h4 className="font-semibold text-white">{currentStep.title}</h4>
        <p className="text-[#94a3b8] text-[11px] leading-relaxed">
          {currentStep.description}
        </p>
      </div>

      <div className="flex items-center justify-between pt-1">
        <button
          type="button"
          onClick={() => handleJump(currentStep.view)}
          className="px-3 py-1 rounded bg-[#ff6b00] hover:bg-[#e05e00] text-white font-medium text-xs transition-colors shadow-xs"
        >
          {currentStep.actionLabel} →
        </button>

        <div className="flex items-center gap-1">
          <button
            type="button"
            disabled={currentStepIndex === 0}
            onClick={() => setCurrentStepIndex((prev) => Math.max(0, prev - 1))}
            className="p-1 rounded bg-[#162238] text-[#94a3b8] hover:text-white disabled:opacity-40"
            aria-label="Previous pitch step"
          >
            ←
          </button>
          <button
            type="button"
            disabled={currentStepIndex === PITCH_STEPS.length - 1}
            onClick={() => setCurrentStepIndex((prev) => Math.min(PITCH_STEPS.length - 1, prev + 1))}
            className="p-1 rounded bg-[#162238] text-[#94a3b8] hover:text-white disabled:opacity-40"
            aria-label="Next pitch step"
          >
            →
          </button>
        </div>
      </div>
    </div>
  );
}
