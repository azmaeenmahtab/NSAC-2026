import * as React from "react";
import type { ToolCallLog } from "../types";
import { cn } from "@/lib/utils";

export interface ToolTimelineProps {
  toolCalls: ToolCallLog[];
  className?: string;
}

export function ToolTimeline({ toolCalls, className }: ToolTimelineProps) {
  const [expandedIndex, setExpandedIndex] = React.useState<number | null>(null);

  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <div
      role="region"
      aria-label="Tool execution timeline"
      data-testid="tool-timeline"
      className={cn(
        "rounded-md border border-[#1f293d]/80 bg-[#080b10]/90 p-2 text-xs",
        className
      )}
    >
      <div className="flex items-center justify-between pb-1.5 border-b border-[#1f293d]/50 mb-1.5">
        <span className="text-[10px] font-mono font-semibold text-[#64748b] uppercase tracking-wider">
          Typed Tool Execution ({toolCalls.length})
        </span>
        <span className="text-[10px] text-[#64748b]">
          Total {Math.round(toolCalls.reduce((sum, t) => sum + t.durationMs, 0))} ms
        </span>
      </div>

      <div className="space-y-1.5">
        {toolCalls.map((tc, idx) => {
          const isExpanded = expandedIndex === idx;

          return (
            <div
              key={`${tc.name}-${idx}`}
              className="rounded border border-[#1f293d]/60 bg-[#0e141f] p-1.5 font-mono text-[11px]"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  <span className="font-semibold text-emerald-300">{tc.name}()</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-[#64748b]">
                    {Math.round(tc.durationMs)} ms
                  </span>
                  <button
                    type="button"
                    onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                    className="text-[10px] text-[#ff6b00] hover:underline cursor-pointer"
                    aria-label={`Toggle arguments for ${tc.name}`}
                  >
                    {isExpanded ? "Hide args" : "View args"}
                  </button>
                </div>
              </div>

              {isExpanded && (
                <pre className="mt-1.5 overflow-x-auto rounded bg-[#080b10] p-1.5 text-[10px] text-[#94a3b8]">
                  {JSON.stringify(tc.args, null, 2)}
                </pre>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
