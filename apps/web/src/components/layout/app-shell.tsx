"use client";

import * as React from "react";
import { Header } from "./header";
import { Attribution } from "./attribution";
import { SidePanel } from "./side-panel";
import { useLanguage } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export interface AppShellProps {
  children?: React.ReactNode; // Primary map / canvas content
  sidePanelContent?: React.ReactNode;
  sidePanelTitle?: React.ReactNode;
  isSidePanelOpen?: boolean;
  onSidePanelClose?: () => void;
  className?: string;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

export function AppShell({
  children,
  sidePanelContent,
  sidePanelTitle,
  isSidePanelOpen = true,
  onSidePanelClose,
  className,
  activeTab,
  onTabChange,
}: AppShellProps) {
  const [isMobilePanelOpen, setIsMobilePanelOpen] = React.useState(false);
  const { isBangla } = useLanguage();

  return (
    <div className={cn("flex min-h-screen flex-col bg-[#080b10] text-[#f8fafc]", className)}>
      <Header activeTab={activeTab} onTabChange={onTabChange} />

      <div className="relative flex flex-1 overflow-hidden">
        {/* Main interactive visualization canvas / map area */}
        <main className="relative flex flex-1 flex-col overflow-hidden bg-[#080b10]">
          {children}

          {/* Floating trigger for mobile drawer if side panel content exists */}
          {sidePanelContent && (
            <div className="absolute bottom-4 right-4 z-30 md:hidden">
              <button
                type="button"
                onClick={() => setIsMobilePanelOpen(true)}
                className="flex items-center gap-1.5 rounded-full bg-[#ff6b00] px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-[#ff6b00]/30 active:scale-95 transition-transform cursor-pointer"
              >
                <span>{isBangla ? "📊 তথ্য ও এলাকা" : "📊 Analytics & Area"}</span>
              </button>
            </div>
          )}
        </main>

        {/* Analytical side panel */}
        {sidePanelContent && (
          <SidePanel
            title={sidePanelTitle}
            isOpen={isSidePanelOpen}
            onClose={onSidePanelClose}
            isMobileOpen={isMobilePanelOpen}
            onMobileClose={() => setIsMobilePanelOpen(false)}
          >
            {sidePanelContent}
          </SidePanel>
        )}
      </div>

      <Attribution />
    </div>
  );
}
