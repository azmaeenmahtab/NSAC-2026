import React from "react";
import { cn } from "@/lib/utils";

interface GuidanceDisclaimerProps {
  className?: string;
}

export function GuidanceDisclaimer({ className }: GuidanceDisclaimerProps) {
  return (
    <div
      role="note"
      aria-label="Advisory disclaimer"
      className={cn(
        "rounded-lg p-3 bg-[#111c30]/70 border border-[#233554] text-xs text-[#94a3b8] leading-relaxed",
        className
      )}
    >
      <div className="flex items-start gap-2">
        <span className="text-[#f59e0b] font-semibold select-none">⚠</span>
        <p>
          <strong className="text-[#f1f5f9] font-medium">Advisory Notice: </strong>
          Alerts, fire season stages, and action guidance are advisory, not an official warning system.
          Preparedness action items are sourced from regional forest agencies and wildland manuals for situational awareness.
          In emergency situations, always defer to official Bangladesh Forest Department or local disaster authority directives.
        </p>
      </div>
    </div>
  );
}

