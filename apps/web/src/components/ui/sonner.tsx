"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  variant?: "default" | "destructive" | "success";
}

export function Toaster({ toasts }: { toasts?: ToastMessage[] }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            "pointer-events-auto rounded-lg border p-4 shadow-xl transition-all",
            toast.variant === "destructive"
              ? "border-[#dc2626] bg-[#ef4444]/15 text-[#f8fafc]"
              : toast.variant === "success"
              ? "border-[#065f46] bg-[#10b981]/15 text-[#f8fafc]"
              : "border-[#2d3b55] bg-[#0e141f] text-[#f8fafc]"
          )}
        >
          <div className="font-semibold text-xs">{toast.title}</div>
          {toast.description && (
            <div className="text-[11px] text-[#94a3b8] mt-1">
              {toast.description}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
