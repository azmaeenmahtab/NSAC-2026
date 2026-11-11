"use client";

import * as React from "react";
import { useMeta } from "@/features/shell";
import { cn } from "@/lib/utils";

export interface AttributionProps {
  className?: string;
}

export function Attribution({ className }: AttributionProps) {
  const { data: metaResponse } = useMeta();
  const attributionText =
    metaResponse?.data?.attribution ||
    "We acknowledge the use of data and imagery from LANCE FIRMS operated by NASA ESDIS. Basemap © CARTO, © OpenStreetMap contributors. Boundaries: geoBoundaries (CC-BY 3.0 IGO / CC0).";

  return (
    <footer
      className={cn(
        "flex flex-col sm:flex-row items-center justify-between gap-2 border-t border-[#1f293d] bg-[#080b10] px-4 py-2 text-[10px] text-[#64748b]",
        className
      )}
    >
      <div className="flex items-center gap-1.5 flex-wrap">
        <span>{attributionText}</span>
      </div>
      <div className="flex items-center gap-3 shrink-0">
        <span>Team Singularity</span>
        <span>•</span>
        <span>NASA Space Apps Challenge 2026</span>
      </div>
    </footer>
  );
}
