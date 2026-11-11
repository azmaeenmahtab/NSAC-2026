import * as React from "react";
import type { AskStyle } from "../types";
import { cn } from "@/lib/utils";

export interface StyleToggleProps {
  style: AskStyle;
  onChange: (style: AskStyle) => void;
  className?: string;
}

export function StyleToggle({
  style,
  onChange,
  className,
}: StyleToggleProps) {
  return (
    <div
      role="group"
      aria-label="Language style toggle"
      className={cn(
        "inline-flex items-center rounded-md border border-[#1f293d] bg-[#0e141f] p-0.5 text-[11px]",
        className
      )}
    >
      <button
        type="button"
        onClick={() => onChange("standard")}
        className={cn(
          "rounded px-2 py-0.5 font-medium transition-colors cursor-pointer",
          style === "standard"
            ? "bg-[#161f30] text-[#ff6b00] font-semibold shadow-xs"
            : "text-[#64748b] hover:text-[#94a3b8]"
        )}
      >
        Standard
      </button>
      <button
        type="button"
        onClick={() => onChange("plain")}
        className={cn(
          "rounded px-2 py-0.5 font-medium transition-colors cursor-pointer",
          style === "plain"
            ? "bg-[#161f30] text-[#ff6b00] font-semibold shadow-xs"
            : "text-[#64748b] hover:text-[#94a3b8]"
        )}
      >
        Plain Language
      </button>
    </div>
  );
}
