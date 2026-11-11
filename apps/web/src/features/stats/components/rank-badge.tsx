import React from "react";
import { cn } from "@/lib/utils";

interface RankBadgeProps {
  rank: number;
  totalYears?: number;
  className?: string;
}

export function RankBadge({ rank, className }: RankBadgeProps) {
  let badgeStyle = "bg-[#1e293b]/70 text-[#94a3b8] border-[#334155]";
  let label = `#${rank}`;

  if (rank === 1) {
    badgeStyle = "bg-[#ef4444]/20 text-[#ef4444] border-[#ef4444]/50 font-bold";
    label = "#1 Peak";
  } else if (rank === 2) {
    badgeStyle = "bg-[#f97316]/20 text-[#f97316] border-[#f97316]/50 font-semibold";
  } else if (rank === 3) {
    badgeStyle = "bg-[#f59e0b]/20 text-[#f59e0b] border-[#f59e0b]/50 font-medium";
  }

  return (
    <span
      data-testid="rank-badge"
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs border tracking-tight tabular-nums",
        badgeStyle,
        className
      )}
      title={`Historical rank #${rank}`}
    >
      {label}
    </span>
  );
}

