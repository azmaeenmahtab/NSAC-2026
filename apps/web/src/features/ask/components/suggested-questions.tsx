import * as React from "react";
import { cn } from "@/lib/utils";

export interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
  className?: string;
}

const SUGGESTIONS = [
  "When does fire season usually start here?",
  "Was last year unusual?",
  "Compare 2019 and 2023",
] as const;

export function SuggestedQuestions({
  onSelect,
  className,
}: SuggestedQuestionsProps) {
  return (
    <div
      role="region"
      aria-label="Suggested questions"
      data-testid="suggested-questions"
      className={cn("flex flex-wrap items-center gap-1.5", className)}
    >
      <span className="text-[11px] font-mono text-[#64748b]">Suggested:</span>
      {SUGGESTIONS.map((q) => (
        <button
          key={q}
          type="button"
          onClick={() => onSelect(q)}
          className="rounded-full border border-[#1f293d] bg-[#161f30]/80 px-2.5 py-1 text-xs text-[#94a3b8] transition-colors hover:border-[#ff6b00]/60 hover:text-[#f8fafc] cursor-pointer"
        >
          {q}
        </button>
      ))}
    </div>
  );
}

