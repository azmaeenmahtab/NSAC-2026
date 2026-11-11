"use client";

import React, { useState } from "react";
import type { GuidanceItem } from "../types";

interface ChecklistProps {
  items: GuidanceItem[];
  emptyMessage?: string;
}

export function Checklist({
  items,
  emptyMessage = "No action items available for this selection.",
}: ChecklistProps) {
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());

  function toggleItem(id: string) {
    setCompletedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  if (items.length === 0) {
    return (
      <div className="py-6 text-center text-xs text-[#64748b]">
        {emptyMessage}
      </div>
    );
  }

  return (
    <ul className="space-y-3" role="list">
      {items.map((item) => {
        const isChecked = completedIds.has(item.id);
        return (
          <li
            key={item.id}
            data-testid={`guidance-item-${item.id}`}
            className={`p-3.5 rounded-lg border transition-all ${
              isChecked
                ? "bg-[#0b1322]/40 border-[#1a253a] opacity-60"
                : "bg-[#0e1626] border-[#1e293b] hover:border-[#2a3c5a]"
            }`}
          >
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id={`check-${item.id}`}
                checked={isChecked}
                onChange={() => toggleItem(item.id)}
                aria-label={`Mark task completed: ${item.text}`}
                className="mt-1 h-4 w-4 rounded border-[#334155] bg-[#162238] text-[#FF6B00] focus:ring-[#FF6B00] focus:ring-offset-0 cursor-pointer"
              />
              <div className="flex-1 space-y-1.5">
                <label
                  htmlFor={`check-${item.id}`}
                  className={`text-xs text-[#e2e8f0] font-normal leading-relaxed cursor-pointer select-none block ${
                    isChecked ? "line-through text-[#64748b]" : ""
                  }`}
                >
                  {/* Strict plain text rendering, no dangerouslySetInnerHTML */}
                  {item.text}
                </label>

                <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px]">
                  {item.source_title && item.source_url && (
                    <a
                      href={item.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#38bdf8] hover:text-[#7dd3fc] hover:underline flex items-center gap-1 font-medium"
                    >
                      <span>Source: {item.source_title}</span>
                      <span aria-hidden="true">↗</span>
                    </a>
                  )}

                  {!item.verified && (
                    <span
                      data-testid="unverified-label"
                      className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-[#ef4444]/15 text-[#f87171] border border-[#ef4444]/30"
                      title="This guidance item has not yet been field-verified by regional foresters"
                    >
                      not yet verified
                    </span>
                  )}
                </div>
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

