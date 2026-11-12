"use client";

import * as React from "react";
import { useConversation } from "../hooks/use-conversation";
import { StyleToggle } from "./style-toggle";
import { SuggestedQuestions } from "./suggested-questions";
import { MessageList } from "./message-list";
import { Button } from "@/components/ui/button";
import { useViewState } from "@/features/areas";
import { useLanguage } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export interface AskPanelProps {
  className?: string;
}

export function AskPanel({ className }: AskPanelProps) {
  const { area, setArea } = useViewState();
  const { t, isBangla } = useLanguage();
  const {
    messages,
    input,
    setInput,
    style,
    setStyle,
    isSubmitting,
    cooldown,
    sendMessage,
    retryLast,
    clearConversation,
  } = useConversation();

  const isOverLimit = input.length > 500;
  const isInputEmpty = input.trim().length === 0;

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (isOverLimit || isInputEmpty || isSubmitting || cooldown !== null) return;
    sendMessage();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div
      className={cn(
        "flex flex-col h-full rounded-xl border border-[#1f293d] bg-[#080b10] shadow-sm overflow-hidden",
        className
      )}
      data-testid="ask-panel"
    >
      {/* Panel Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1f293d] bg-[#0e141f] px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-base">🔥</span>
          <div>
            <h3 className="font-semibold text-xs text-[#f8fafc]">
              {isBangla ? `${t.ask.title} (Ask Assistant)` : "Ask PyroScope Assistant"}
            </h3>
            <p className="text-[10px] text-[#94a3b8]">
              {isBangla ? t.ask.subtitle : "Answers grounded in verified NASA satellite data"} • {isBangla ? "অঞ্চল" : "Active Region"}:{" "}
              <strong className="text-[#ff6b00] font-mono">{area}</strong>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <StyleToggle style={style} onChange={setStyle} />
          {messages.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearConversation}
              className="h-7 text-xs text-[#64748b] hover:text-[#f8fafc]"
            >
              {isBangla ? t.ask.clear : "Clear"}
            </Button>
          )}
        </div>
      </div>

      {/* Suggested Questions banner */}
      <div className="border-b border-[#1f293d]/50 bg-[#0e141f]/40 px-4 py-2">
        <SuggestedQuestions onSelect={(q) => sendMessage(q)} />
      </div>

      {/* Messages Viewport */}
      <div className="flex-1 overflow-y-auto">
        <MessageList
          messages={messages}
          onSelectCandidate={(cand) => {
            setArea(cand.id);
            sendMessage(
              isBangla
                ? `${cand.name} এলাকার আগুনের ইতিহাস ও মৌসুম সম্পর্কে বলুন`
                : `Tell me about fire activity in ${cand.name}`
            );
          }}
          onRetry={retryLast}
        />
      </div>

      {/* Input Composer */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-[#1f293d] bg-[#0e141f] p-3"
      >
        <div className="relative rounded-lg border border-[#1f293d] bg-[#080b10] focus-within:border-[#ff6b00]/60 transition-colors">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSubmitting || cooldown !== null}
            placeholder={
              cooldown !== null
                ? isBangla
                  ? `অনুরোধের সীমা শেষ। অপেক্ষা করুন ${cooldown} সেকেন্ড...`
                  : `Rate limited. Available in ${cooldown}s...`
                : isBangla
                  ? t.ask.placeholder
                  : "Ask about fire seasonality, anomalies, or year comparisons..."
            }
            rows={2}
            aria-label="Ask assistant question"
            className="w-full resize-none bg-transparent p-2.5 text-xs text-[#f8fafc] placeholder-[#64748b] outline-hidden"
          />

          <div className="flex items-center justify-between border-t border-[#1f293d]/40 px-2.5 py-1.5 text-[11px]">
            <span
              className={cn(
                "font-mono text-[10px]",
                isOverLimit
                  ? "text-red-400 font-bold"
                  : input.length > 450
                  ? "text-amber-400"
                  : "text-[#64748b]"
              )}
            >
              {input.length} / 500 {isBangla ? "অক্ষর" : "characters"}
            </span>

            <div className="flex items-center gap-2">
              <span className="hidden sm:inline text-[10px] text-[#64748b]">
                {isBangla ? "↵ পাঠাতে, shift+↵ নতুন লাইনে" : "↵ to send, shift+↵ for newline"}
              </span>
              <Button
                type="submit"
                size="sm"
                disabled={isOverLimit || isInputEmpty || isSubmitting || cooldown !== null}
                className="h-7 px-3 text-xs font-semibold bg-[#ff6b00] hover:bg-[#ff8533] text-white cursor-pointer"
              >
                {isSubmitting ? (isBangla ? "পাঠানো হচ্ছে..." : "Sending...") : "Ask"}
              </Button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
