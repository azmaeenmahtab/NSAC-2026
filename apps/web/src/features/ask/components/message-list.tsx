import * as React from "react";
import type { ChatMessage, AreaCandidate } from "../types";
import { AnswerCard } from "./answer-card";
import { cn } from "@/lib/utils";

export interface MessageListProps {
  messages: ChatMessage[];
  onSelectCandidate?: (candidate: AreaCandidate) => void;
  onRetry?: () => void;
  className?: string;
}

export function MessageList({
  messages,
  onSelectCandidate,
  onRetry,
  className,
}: MessageListProps) {
  const bottomRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (typeof bottomRef.current?.scrollIntoView === "function") {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center p-8 text-center text-xs text-[#64748b] min-h-64",
          className
        )}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#161f30] text-xl mb-3 border border-[#1f293d]">
          🔥
        </div>
        <h4 className="font-semibold text-sm text-[#f8fafc] mb-1">
          Ask PyroScope Analytics
        </h4>
        <p className="max-w-md text-[11px] text-[#94a3b8] leading-relaxed">
          Ask questions about fire seasonality, historic anomalies, or multi-year
          comparisons across Bangladesh districts. All responses are verified against
          the calibrated 2000–present Harmonized dataset.
        </p>
      </div>
    );
  }

  return (
    <div
      role="feed"
      aria-label="Conversation stream"
      className={cn("flex flex-col gap-4 overflow-y-auto p-4", className)}
    >
      {messages.map((msg) => {
        if (msg.role === "user") {
          return (
            <div
              key={msg.id}
              className="flex justify-end"
              data-testid="user-message"
            >
              <div className="max-w-[85%] rounded-2xl rounded-tr-xs bg-[#ff6b00]/15 border border-[#ff6b00]/40 px-4 py-2.5 text-xs text-[#f8fafc] shadow-xs">
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          );
        }

        return (
          <div key={msg.id} className="flex justify-start">
            <div className="max-w-[95%] w-full">
              <AnswerCard
                message={msg}
                onSelectCandidate={onSelectCandidate}
                onRetry={onRetry}
              />
            </div>
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
