import * as React from "react";
import { cn } from "@/lib/utils";

export interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title = "No data available",
  description = "No fire activity or records found for the selected area and time range.",
  icon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      role="status"
      className={cn(
        "flex min-h-[160px] flex-col items-center justify-center rounded-lg border border-dashed border-[#1f293d] bg-[#0e141f]/50 p-6 text-center",
        className
      )}
    >
      {icon ? (
        <div className="mb-3 text-[#64748b]">{icon}</div>
      ) : (
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-[#161f30] text-[#94a3b8] text-sm font-mono">
          ∅
        </div>
      )}
      <h4 className="text-xs font-semibold text-[#f8fafc]">{title}</h4>
      <p className="mt-1 max-w-xs text-[11px] text-[#94a3b8]">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
