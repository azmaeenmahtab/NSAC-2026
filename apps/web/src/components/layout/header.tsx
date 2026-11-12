"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMeta } from "@/features/shell";
import { DataStatusBadge } from "@/features/shell";
import { useLanguage } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export interface HeaderProps {
  className?: string;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

export function Header({ className, activeTab, onTabChange }: HeaderProps) {
  const pathname = usePathname();
  const { data: metaResponse } = useMeta();
  const meta = metaResponse?.data;
  const { language, setLanguage, t } = useLanguage();

  const navItems = [
    { href: "/", label: t.header.nav_map_calendar, tab: "mission-control" },
    { href: "/hidden-jump", label: t.header.nav_hidden_jump, tab: "hidden-jump" },
    { href: "/ask", label: t.header.nav_ask, tab: "ask" },
    { href: "/methodology", label: t.header.nav_methodology, tab: "methodology" },
  ];

  return (
    <header
      className={cn(
        "sticky top-0 z-40 flex h-14 w-full items-center justify-between border-b border-[#1f293d] bg-[#0e141f]/95 px-4 backdrop-blur-md",
        className
      )}
    >
      {/* Brand logo & tagline */}
      <div className="flex items-center gap-3">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[#ff6b00]/15 border border-[#ff6b00]/40 group-hover:border-[#ff6b00] transition-colors">
            <span className="text-[#ff6b00] text-sm font-bold">🔥</span>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5 leading-none">
              <span className="font-bold text-sm tracking-tight text-[#f8fafc]">
                {t.header.brand_title}
              </span>
              <span className="text-[10px] font-mono rounded bg-[#161f30] px-1 py-0.2 text-[#ff6b00] border border-[#2d3b55]">
                {t.header.brand_badge}
              </span>
            </div>
            <span className="text-[10px] text-[#64748b] leading-tight">
              {t.header.brand_tagline}
            </span>
          </div>
        </Link>
      </div>

      {/* Center Nav tabs */}
      <nav className="hidden md:flex items-center gap-1 rounded-lg bg-[#080b10] p-1 border border-[#1f293d]">
        {navItems.map((item) => {
          const isActive =
            activeTab !== undefined
              ? activeTab === item.tab
              : pathname === item.href;

          return onTabChange ? (
            <button
              key={item.tab}
              type="button"
              onClick={() => onTabChange(item.tab)}
              className={cn(
                "rounded-md px-3 py-1 text-xs font-medium transition-colors cursor-pointer",
                isActive
                  ? "bg-[#161f30] text-[#f8fafc] border border-[#2d3b55] shadow-xs"
                  : "text-[#94a3b8] hover:text-[#f8fafc] hover:bg-[#161f30]/40"
              )}
            >
              {item.label}
            </button>
          ) : (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-md px-3 py-1 text-xs font-medium transition-colors",
                isActive
                  ? "bg-[#161f30] text-[#f8fafc] border border-[#2d3b55] shadow-xs"
                  : "text-[#94a3b8] hover:text-[#f8fafc] hover:bg-[#161f30]/40"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Right side controls: Language switcher toggle & Metadata badge */}
      <div className="flex items-center gap-2.5">
        {/* Language Toggle */}
        <div
          role="group"
          aria-label="Language selector"
          className="flex items-center rounded-lg bg-[#080b10] p-0.5 border border-[#1f293d]"
        >
          <button
            type="button"
            onClick={() => setLanguage("en")}
            className={cn(
              "px-2 py-0.5 rounded text-xs font-medium transition-all cursor-pointer",
              language === "en"
                ? "bg-[#ff6b00] text-white font-semibold shadow-xs"
                : "text-[#94a3b8] hover:text-[#f8fafc]"
            )}
            title="Switch to English"
          >
            EN
          </button>
          <button
            type="button"
            onClick={() => setLanguage("bn")}
            className={cn(
              "px-2 py-0.5 rounded text-xs font-medium transition-all cursor-pointer",
              language === "bn"
                ? "bg-[#ff6b00] text-white font-semibold shadow-xs"
                : "text-[#94a3b8] hover:text-[#f8fafc]"
            )}
            title="বাংলায় দেখুন"
          >
            বাংলা
          </button>
        </div>

        <DataStatusBadge
          dataVersion={meta?.dataVersion}
          asOf={meta?.asOf}
          provisionalFrom={meta?.provisionalFrom}
        />
      </div>
    </header>
  );
}
