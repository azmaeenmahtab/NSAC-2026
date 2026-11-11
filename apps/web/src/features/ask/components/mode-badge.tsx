import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface ModeBadgeProps {
  mode: "live" | "replay";
  className?: string;
}

export function ModeBadge({ mode, className }: ModeBadgeProps) {
  const isLive = mode === "live";

  return (
    <Badge
      variant="outline"
      data-testid="mode-badge"
      className={cn(
        "flex items-center gap-1.5 px-2 py-0.5 text-[10px] font-mono tracking-tight transition-colors",
        isLive
          ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
          : "border-purple-500/40 bg-purple-500/10 text-purple-300",
        className
      )}
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          isLive ? "bg-emerald-400 animate-pulse" : "bg-purple-400"
        )}
      />
      <span>{isLive ? "Live model" : "Scripted replay (offline demo)"}</span>
    </Badge>
  );
}
