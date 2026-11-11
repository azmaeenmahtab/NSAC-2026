import * as React from "react";
import type { ChatMessage, AreaCandidate } from "../types";
import { ModeBadge } from "./mode-badge";
import { ToolTimeline } from "./tool-timeline";
import { CitationChips } from "./citation-chips";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface AnswerCardProps {
  message: ChatMessage;
  onSelectCandidate?: (candidate: AreaCandidate) => void;
  onRetry?: () => void;
  className?: string;
}

export function AnswerCard({
  message,
  onSelectCandidate,
  onRetry,
  className,
}: AnswerCardProps) {
  // Pending Skeleton State
  if (message.isPending) {
    return (
      <div
        className={cn(
          "rounded-xl border border-[#1f293d] bg-[#0e141f] p-4 text-xs text-[#94a3b8] space-y-3",
          className
        )}
        data-testid="answer-card-pending"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[#ff6b00] animate-pulse" />
            <span className="font-semibold text-xs text-[#ff6b00]">
              Consulting Grounded Engine...
            </span>
          </div>
          <Skeleton className="h-4 w-20" />
        </div>
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-12 w-full rounded-md" />
      </div>
    );
  }

  // Error State
  if (message.error) {
    return (
      <div
        className={cn(
          "rounded-xl border border-red-500/30 bg-red-950/20 p-4 text-xs text-red-200 space-y-3",
          className
        )}
        data-testid="answer-card-error"
      >
        <div className="flex items-center justify-between">
          <span className="font-semibold text-xs text-red-400">
            {message.isRateLimited ? "Query Rate Limit" : "Assistant Error"}
          </span>
          {message.isRateLimited && message.retryAfterSeconds && (
            <span className="font-mono text-[11px] text-amber-400">
              Cooldown: {message.retryAfterSeconds}s
            </span>
          )}
        </div>

        <p className="whitespace-pre-wrap leading-relaxed">{message.error}</p>

        {!message.isRateLimited && onRetry && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="h-7 text-xs border-red-500/40 text-red-300 hover:bg-red-950/40"
          >
            Retry Query
          </Button>
        )}
      </div>
    );
  }

  const response = message.response;
  const candidates = response?.candidates || [];

  return (
    <div
      className={cn(
        "rounded-xl border border-[#1f293d] bg-[#0e141f] p-4 text-xs text-[#f8fafc] shadow-sm space-y-3",
        className
      )}
      data-testid="answer-card"
    >
      {/* Header: Persona identity + Mode Badge */}
      <div className="flex items-center justify-between pb-2 border-b border-[#1f293d]/50">
        <div className="flex items-center gap-2">
          <div className="flex h-5 w-5 items-center justify-center rounded bg-[#ff6b00]/20 text-[10px]">
            🔥
          </div>
          <span className="font-semibold text-xs text-[#f8fafc]">
            PyroScope Assistant
          </span>
        </div>

        {response?.mode && <ModeBadge mode={response.mode} />}
      </div>

      {/* Answer Body: Literal plain text with line breaks to prevent HTML/XSS */}
      <div className="text-[13px] text-[#e2e8f0] leading-relaxed whitespace-pre-wrap font-sans">
        {message.content}
      </div>

      {/* Clarification candidate buttons if ambiguous area detected */}
      {candidates.length > 0 && (
        <div className="rounded-lg border border-[#2d3b55] bg-[#161f30] p-2.5 space-y-2">
          <span className="text-[11px] font-semibold text-[#ff6b00]">
            Did you mean one of these areas?
          </span>
          <div className="flex flex-wrap gap-1.5">
            {candidates.map((cand) => (
              <Button
                key={cand.id}
                variant="outline"
                size="sm"
                onClick={() => onSelectCandidate?.(cand)}
                className="h-7 text-xs font-mono"
              >
                📍 {cand.name} ({cand.id})
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Tool Timeline */}
      {response?.toolCalls && response.toolCalls.length > 0 && (
        <ToolTimeline toolCalls={response.toolCalls} />
      )}

      {/* Citation Chips */}
      {response?.citations && response.citations.length > 0 && (
        <CitationChips citations={response.citations} />
      )}
    </div>
  );
}

