import React from "react";
import { cn } from "@/lib/utils";
import type { GuidanceStage } from "../types";

interface StageBadgeProps {
  stage: GuidanceStage;
  className?: string;
}

const STAGE_CONFIGS: Record<
  GuidanceStage,
  { label: string; bg: string; text: string; border: string; desc: string }
> = {
  pre_season: {
    label: "Pre-Season Readiness",
    bg: "bg-[#f59e0b]/15",
    text: "text-[#f59e0b]",
    border: "border-[#f59e0b]/40",
    desc: "Preparation, fuel reduction and community alert drills",
  },
  in_season: {
    label: "In Season Active",
    bg: "bg-[#ef4444]/15",
    text: "text-[#ef4444]",
    border: "border-[#ef4444]/40",
    desc: "Peak historical fire window, rapid response stand-by",
  },
  post_season: {
    label: "Post-Season Recovery",
    bg: "bg-[#0ea5e9]/15",
    text: "text-[#38bdf8]",
    border: "border-[#0ea5e9]/40",
    desc: "Post-burn erosion prevention and ecosystem restoration",
  },
  extreme: {
    label: "Extreme Fire Threat",
    bg: "bg-[#a855f7]/20",
    text: "text-[#c084fc]",
    border: "border-[#a855f7]/50",
    desc: "Anomalous burning exceeding historical 95th percentile",
  },
  off_season: {
    label: "Off Season Baseline",
    bg: "bg-[#1e293b]/60",
    text: "text-[#94a3b8]",
    border: "border-[#334155]",
    desc: "Routine monitoring and fire buffer maintenance",
  },
};

export function StageBadge({ stage, className }: StageBadgeProps) {
  const config = STAGE_CONFIGS[stage] || STAGE_CONFIGS.off_season;

  return (
    <span
      data-testid="stage-badge"
      className={cn(
        "inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border tracking-wide",
        config.bg,
        config.text,
        config.border,
        className
      )}
      title={config.desc}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5" />
      {config.label}
    </span>
  );
}

