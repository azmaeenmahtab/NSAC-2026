"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function Tooltip({ content, children, className }: TooltipProps) {
  const [isVisible, setIsVisible] = React.useState(false);

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div
          role="tooltip"
          className={cn(
            "absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 whitespace-nowrap rounded bg-[#080b10] px-2.5 py-1 text-[11px] text-[#f8fafc] border border-[#2d3b55] shadow-lg pointer-events-none",
            className
          )}
        >
          {content}
        </div>
      )}
    </div>
  );
}
