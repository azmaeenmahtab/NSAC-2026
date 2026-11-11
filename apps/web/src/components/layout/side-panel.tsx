"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Sheet } from "@/components/ui/sheet";

export interface SidePanelProps {
  title?: React.ReactNode;
  children: React.ReactNode;
  isOpen?: boolean;
  onClose?: () => void;
  className?: string;
  isMobileOpen?: boolean;
  onMobileClose?: () => void;
}

export function SidePanel({
  title,
  children,
  isOpen = true,
  onClose,
  className,
  isMobileOpen = false,
  onMobileClose,
}: SidePanelProps) {
  return (
    <>
      {/* Desktop / Tablet side panel */}
      <aside
        className={cn(
          "hidden md:flex flex-col border-l border-[#1f293d] bg-[#0e141f] transition-all duration-200 z-20 shrink-0",
          isOpen ? "w-96 lg:w-[420px]" : "w-0 overflow-hidden border-l-0",
          className
        )}
      >
        {isOpen && (
          <div className="flex h-full flex-col overflow-hidden">
            {title && (
              <div className="flex items-center justify-between border-b border-[#1f293d] px-4 py-3 shrink-0">
                <div className="font-semibold text-xs text-[#f8fafc]">
                  {title}
                </div>
                {onClose && (
                  <button
                    type="button"
                    onClick={onClose}
                    className="text-[#64748b] hover:text-[#f8fafc] text-xs p-1 rounded hover:bg-[#161f30] cursor-pointer"
                    aria-label="Close panel"
                  >
                    ✕
                  </button>
                )}
              </div>
            )}
            <div className="flex-1 overflow-y-auto p-4">{children}</div>
          </div>
        )}
      </aside>

      {/* Mobile bottom sheet */}
      <div className="md:hidden">
        <Sheet
          open={isMobileOpen}
          onOpenChange={(open) => !open && onMobileClose?.()}
          side="bottom"
        >
          {title && (
            <div className="flex items-center justify-between border-b border-[#1f293d] pb-2 mb-3">
              <div className="font-semibold text-xs text-[#f8fafc]">{title}</div>
              {onMobileClose && (
                <button
                  type="button"
                  onClick={onMobileClose}
                  className="text-[#64748b] hover:text-[#f8fafc] text-xs p-1"
                >
                  ✕
                </button>
              )}
            </div>
          )}
          <div className="max-h-[60vh] overflow-y-auto">{children}</div>
        </Sheet>
      </div>
    </>
  );
}
