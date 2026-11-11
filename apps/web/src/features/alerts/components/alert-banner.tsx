"use client";

import React, { useState } from "react";
import type { ActiveAlerts } from "../types";

interface AlertBannerProps {
  areaId: string;
  areaName?: string;
  alerts?: ActiveAlerts;
  onOpenSubscribe?: () => void;
}

export function AlertBanner({
  areaId,
  areaName,
  alerts,
  onOpenSubscribe,
}: AlertBannerProps) {
  const [dismissed, setDismissed] = useState(false);
  const [notifGranted, setNotifGranted] = useState(
    typeof window !== "undefined" && "Notification" in window
      ? Notification.permission === "granted"
      : false
  );

  if (dismissed || !alerts) return null;

  const isSeasonApproaching = alerts.season_approaching;
  const isAboveNormal =
    alerts.above_normal ||
    alerts.current_month_class === "elevated" ||
    alerts.current_month_class === "extreme";

  if (!isSeasonApproaching && !isAboveNormal) {
    return null;
  }

  const isExtreme = alerts.current_month_class === "extreme";
  const bgStyle = isExtreme
    ? "bg-red-950/80 border-red-700/60 text-red-200"
    : "bg-amber-950/80 border-amber-600/60 text-amber-200";

  async function requestNotificationPermission() {
    if (typeof window !== "undefined" && "Notification" in window) {
      const permission = await Notification.requestPermission();
      setNotifGranted(permission === "granted");
    }
  }

  return (
    <aside
      role="alert"
      data-testid="alert-banner"
      className={`relative z-30 px-4 py-3 border-b backdrop-blur-md transition-all ${bgStyle}`}
    >
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <span className="text-lg leading-none mt-0.5 select-none" aria-hidden="true">
            {isExtreme ? "🚨" : "⚠️"}
          </span>
          <div className="space-y-0.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold text-xs tracking-wide uppercase text-white">
                {isExtreme
                  ? "Extreme Anomaly Warning"
                  : isSeasonApproaching
                    ? "Fire Season Approaching"
                    : "Elevated Burning Advisory"}
              </span>
              <span className="text-xs text-white/80 font-medium">
                — {areaName || areaId}
              </span>
              {alerts.days_until_season !== null &&
                alerts.days_until_season !== undefined && (
                  <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-white/20 text-white">
                    {alerts.days_until_season} days until historical season onset
                  </span>
                )}
            </div>

            <p className="text-xs text-white/90 leading-snug">
              {alerts.reason ||
                "Seasonal analysis indicates dry transition conditions and heightened fire probability."}{" "}
              <span className="opacity-75 italic">
                (Advisory notice: provisional data as of{" "}
                {alerts.provisional_as_of || "latest satellite pass"})
              </span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto shrink-0">
          {!notifGranted && typeof window !== "undefined" && "Notification" in window && (
            <button
              type="button"
              onClick={requestNotificationPermission}
              className="text-xs px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-white border border-white/20 transition-colors"
            >
              🔔 Enable Notifications
            </button>
          )}

          {onOpenSubscribe && (
            <button
              type="button"
              onClick={onOpenSubscribe}
              className="text-xs px-3 py-1 rounded bg-white text-black font-semibold hover:bg-white/90 transition-colors shadow-xs"
            >
              Subscribe to Alerts
            </button>
          )}

          <button
            type="button"
            onClick={() => setDismissed(true)}
            aria-label="Dismiss alert banner"
            className="text-white/60 hover:text-white text-sm p-1 ml-1"
          >
            ✕
          </button>
        </div>
      </div>
    </aside>
  );
}

