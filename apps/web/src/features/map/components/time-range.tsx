import * as React from "react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export interface TimeRangeProps {
  from: string; // YYYY-MM
  to: string; // YYYY-MM
  onChange: (from: string, to: string) => void;
  className?: string;
}

export function TimeRange({
  from,
  to,
  onChange,
  className,
}: TimeRangeProps) {
  const handleFromChange = (newFrom: string) => {
    if (newFrom && (!to || newFrom <= to)) {
      onChange(newFrom, to);
    }
  };

  const handleToChange = (newTo: string) => {
    if (newTo && (!from || from <= newTo)) {
      onChange(from, newTo);
    }
  };

  return (
    <div className={cn("inline-flex items-center gap-2 text-xs", className)}>
      <span className="text-[11px] text-[#94a3b8] font-medium hidden sm:inline">
        Period:
      </span>
      <div className="flex items-center gap-1">
        <Input
          type="month"
          value={from}
          onChange={(e) => handleFromChange(e.target.value)}
          className="h-8 w-32 bg-[#080b10] text-xs font-mono"
          aria-label="Start month"
        />
        <span className="text-[#64748b]">→</span>
        <Input
          type="month"
          value={to}
          onChange={(e) => handleToChange(e.target.value)}
          className="h-8 w-32 bg-[#080b10] text-xs font-mono"
          aria-label="End month"
        />
      </div>
    </div>
  );
}
