import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export interface ErrorStateProps {
  title?: string;
  message?: string;
  code?: string;
  requestId?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Telemetry failure",
  message = "Failed to fetch analytical data from the PyroScope API.",
  code,
  requestId,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex min-h-[160px] flex-col items-center justify-center rounded-lg border border-[#dc2626]/40 bg-[#ef4444]/10 p-6 text-center",
        className
      )}
    >
      <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-[#ef4444]/20 text-[#ef4444] font-bold text-xs">
        !
      </div>
      <h4 className="text-xs font-semibold text-[#f8fafc]">{title}</h4>
      <p className="mt-1 max-w-sm text-[11px] text-[#94a3b8]">{message}</p>
      {(code || requestId) && (
        <div className="mt-2 text-[10px] text-[#64748b] font-mono">
          {code && <span>Code: {code} </span>}
          {requestId && <span>(req: {requestId})</span>}
        </div>
      )}
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="mt-3 text-xs border-[#2d3b55] hover:border-[#ff6b00]"
        >
          Retry request
        </Button>
      )}
    </div>
  );
}
