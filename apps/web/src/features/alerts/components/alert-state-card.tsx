"use client";

import React from "react";
import { useLanguage } from "@/lib/i18n";
import type { ActiveAlerts } from "../types";

interface AlertStateCardProps {
  areaId: string;
  areaName?: string;
  alerts?: ActiveAlerts;
  onSubscribeClick?: () => void;
}

export function AlertStateCard({
  areaId,
  areaName,
  alerts,
  onSubscribeClick,
}: AlertStateCardProps) {
  const { t, isBangla } = useLanguage();

  if (!alerts) return null;

  const hasActiveWarning =
    alerts.season_approaching ||
    alerts.above_normal ||
    alerts.current_month_class === "elevated" ||
    alerts.current_month_class === "extreme";

  return (
    <div
      data-testid="alert-state-card"
      className="bg-[#0e1626] border border-[#1e293b] rounded-xl p-4 space-y-3"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-[#f1f5f9] uppercase tracking-wider">
          {t.alerts.card_title}
        </h3>
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${
            hasActiveWarning
              ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
              : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
          }`}
        >
          {hasActiveWarning ? t.alerts.status_advisory : t.alerts.status_normal}
        </span>
      </div>

      <p className="text-xs text-[#94a3b8] leading-relaxed">
        {isBangla ? "নির্বাচিত এলাকা: " : "Area: "}
        <span className="text-white font-medium">{areaName || areaId}</span>
      </p>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="p-2.5 rounded-lg bg-[#141e30] border border-[#21304b]">
          <span className="text-[#64748b] block text-[11px]">
            {t.alerts.season_transition}
          </span>
          <span className="font-semibold text-white">
            {alerts.season_approaching ? t.alerts.approaching : t.alerts.stable}
          </span>
          {alerts.days_until_season !== null && alerts.days_until_season !== undefined && (
            <span className="block text-[10px] text-[#ff8533]">
              ~{alerts.days_until_season} {isBangla ? "দিন বাকি" : "days away"}
            </span>
          )}
        </div>

        <div className="p-2.5 rounded-lg bg-[#141e30] border border-[#21304b]">
          <span className="text-[#64748b] block text-[11px]">
            {t.alerts.anomaly_class}
          </span>
          <span
            className={`font-semibold capitalize ${
              alerts.current_month_class === "extreme"
                ? "text-red-400"
                : alerts.current_month_class === "elevated"
                  ? "text-amber-400"
                  : "text-slate-300"
            }`}
          >
            {isBangla
              ? alerts.current_month_class === "extreme"
                ? "চরম বিপদ"
                : alerts.current_month_class === "elevated"
                  ? "স্বাভাবিকের চেয়ে বেশি"
                  : "স্বাভাবিক"
              : alerts.current_month_class || "Normal"}
          </span>
          <span className="block text-[10px] text-[#64748b]">
            {t.alerts.historical_baseline}
          </span>
        </div>
      </div>

      {onSubscribeClick && (
        <button
          type="button"
          onClick={onSubscribeClick}
          className="w-full mt-2 py-2 px-3 rounded-lg text-xs font-medium bg-[#1a263d] hover:bg-[#233352] text-[#ff8533] hover:text-[#ff9955] border border-[#ff6b00]/30 transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
        >
          <span>✉</span>
          <span>{t.alerts.subscribe_btn}</span>
        </button>
      )}
    </div>
  );
}
