"use client";

import React, { useState } from "react";
import { Copy, LocateFixed, Mail, Phone, ShieldAlert } from "lucide-react";
import { useNearbyStations } from "../api/use-nearby-stations";
import { buildMailtoHref, buildTelHref } from "../lib/contact-links";
import { useLanguage } from "@/lib/i18n";
import type { ThreatLevel } from "../types";

interface NearbyStationsPanelProps {
  areaId: string;
}

const RISK_BADGE_STYLES: Record<ThreatLevel, string> = {
  LOW: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
  MODERATE: "bg-amber-500/15 text-amber-300 border-amber-500/40",
  HIGH: "bg-orange-500/20 text-orange-300 border-orange-500/50",
  CRITICAL: "bg-red-500/20 text-red-300 border-red-500/50",
};

export function NearbyStationsPanel({ areaId }: NearbyStationsPanelProps) {
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [locating, setLocating] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const { t, isBangla } = useLanguage();

  const { data, isLoading, isError } = useNearbyStations({
    areaId,
    lat: coords?.lat,
    lon: coords?.lon,
    limit: 4,
  });

  function handleUseMyLocation() {
    setGeoError(null);
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setGeoError(
        isBangla
          ? "ব্রাউজারে লোকেশন সুবিধা পাওয়া যায়নি। নির্বাচিত এলাকার স্টেশন দেখানো হচ্ছে।"
          : "Location access is unavailable in this browser. Using selected map area."
      );
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({
          lat: Number(pos.coords.latitude.toFixed(5)),
          lon: Number(pos.coords.longitude.toFixed(5)),
        });
        setLocating(false);
      },
      () => {
        setGeoError(
          isBangla
            ? "লোকেশন অনুমতি পাওয়া যায়নি। মানচিত্রে নির্বাচিত এলাকার স্টেশন দেখানো হচ্ছে।"
            : "Location permission denied. Showing stations for selected map area."
        );
        setLocating(false);
      },
      { enableHighAccuracy: false, timeout: 8000 }
    );
  }

  async function handleCopyReport(stationId: string, subject: string, body: string) {
    try {
      await navigator.clipboard.writeText(`Subject: ${subject}\n\n${body}`);
      setCopiedId(stationId);
      setTimeout(() => setCopiedId((prev) => (prev === stationId ? null : prev)), 2000);
    } catch {
      setGeoError(isBangla ? "রিপোর্ট টেক্সট কপি করা যায়নি।" : "Could not copy report text to clipboard.");
    }
  }

  const gpsBtnLabel = locating
    ? isBangla
      ? t.stations.locating
      : "Locating..."
    : coords
      ? isBangla
        ? t.stations.refresh_gps
        : "Refresh GPS"
      : isBangla
        ? t.stations.use_gps
        : "Use My Location";

  return (
    <div
      data-testid="nearby-stations-panel"
      className="bg-[#0e1626] border border-[#1e293b] rounded-xl p-4 space-y-3"
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <ShieldAlert className="h-4 w-4 text-[#ff6b00]" />
          <h3 className="text-xs font-semibold text-[#f1f5f9] uppercase tracking-wider">
            {t.stations.title}
          </h3>
        </div>
        <button
          type="button"
          onClick={handleUseMyLocation}
          disabled={locating}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium bg-[#1a263d] hover:bg-[#233352] text-[#38bdf8] border border-[#38bdf8]/30 cursor-pointer disabled:opacity-50"
        >
          <LocateFixed className="h-3 w-3" />
          <span>{gpsBtnLabel}</span>
        </button>
      </div>

      {geoError && (
        <p role="status" className="text-[11px] text-amber-300 bg-amber-950/30 border border-amber-500/30 rounded-md px-2.5 py-1.5">
          {geoError}
        </p>
      )}

      {data && (
        <div className="rounded-lg bg-[#141e30] border border-[#21304b] p-2.5 space-y-1">
          <div className="flex items-center justify-between gap-2">
            <span className="text-[11px] text-[#94a3b8]">
              {data.location_source === "gps"
                ? isBangla
                  ? `আপনার জিপিএস অবস্থান অনুযায়ী (${data.center_lat.toFixed(3)}, ${data.center_lon.toFixed(3)})`
                  : `Using your GPS (${data.center_lat.toFixed(3)}, ${data.center_lon.toFixed(3)})`
                : data.location_source === "area_fallback_outside_bd"
                  ? isBangla
                    ? `জিপিএস বাংলাদেশের বাইরে; ${data.area_name}-এর স্টেশন দেখানো হচ্ছে`
                    : `GPS outside Bangladesh; showing ${data.area_name}`
                  : isBangla
                    ? `${data.area_name}-এর নিকটবর্তী ফায়ার স্টেশন`
                    : `Showing stations near ${data.area_name}`}
            </span>
            <span
              data-testid="threat-level-badge"
              className={`px-2 py-0.5 rounded border text-[10px] font-bold ${RISK_BADGE_STYLES[data.threat.level]}`}
            >
              {data.threat.level} {isBangla ? t.stations.risk_level : "RISK"}
            </span>
          </div>
          <p className="text-[11px] text-[#cbd5e1] leading-snug">{data.threat.explanation}</p>
        </div>
      )}

      {isLoading && (
        <p className="text-xs text-[#94a3b8]">
          {isBangla ? "নিকটতম ফায়ার স্টেশন খোঁজা হচ্ছে..." : "Finding closest fire stations..."}
        </p>
      )}
      {isError && (
        <p className="text-xs text-red-400">
          {isBangla ? "ফায়ার স্টেশনের তথ্য লোড করা যায়নি।" : "Unable to load nearby fire stations right now."}
        </p>
      )}

      {data && data.stations.length > 0 && (
        <div className="space-y-2">
          {data.stations.map((st) => (
            <div
              key={st.station_id}
              data-testid="station-card"
              className="rounded-lg bg-[#141e30] border border-[#21304b] p-2.5 space-y-2"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-xs font-semibold text-white leading-snug">{st.name}</p>
                  <p className="text-[11px] text-[#94a3b8]">
                    {st.district_name} {isBangla ? "জেলা" : "District"}
                  </p>
                </div>
                <span className="shrink-0 rounded bg-[#0e1626] px-2 py-0.5 text-[11px] font-medium text-[#ff8533] border border-[#ff6b00]/30">
                  {st.distance_km.toFixed(1)} {isBangla ? "কিমি" : "km"}
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-1.5">
                <a
                  href={buildTelHref(st.dial_number)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-semibold bg-[#ff6b00] hover:bg-[#e05e00] text-white transition-colors"
                >
                  <Phone className="h-3 w-3" />
                  <span>
                    {isBangla ? `কল ${st.dial_number}` : `Call ${st.dial_number}`}
                  </span>
                </a>
                <a
                  href={buildTelHref(st.national_emergency)}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium bg-[#1a263d] hover:bg-[#233352] text-[#e2e8f0] border border-[#334155]"
                >
                  <span>
                    {isBangla ? `জরুরি ${st.national_emergency}` : `Emergency ${st.national_emergency}`}
                  </span>
                </a>
                <a
                  href={buildMailtoHref(st.email, st.email_subject, st.email_body)}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium bg-[#1a263d] hover:bg-[#233352] text-[#38bdf8] border border-[#38bdf8]/30"
                >
                  <Mail className="h-3 w-3" />
                  <span>{isBangla ? t.stations.email_btn : "Email Report"}</span>
                </a>
                <button
                  type="button"
                  onClick={() => handleCopyReport(st.station_id, st.email_subject, st.email_body)}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium bg-[#0e1626] hover:bg-[#1e293b] text-[#94a3b8] border border-[#334155] cursor-pointer"
                >
                  <Copy className="h-3 w-3" />
                  <span>
                    {copiedId === st.station_id
                      ? isBangla
                        ? t.stations.copied
                        : "Copied!"
                      : isBangla
                        ? t.stations.copy_btn
                        : "Copy"}
                  </span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Emergency Callout */}
      <div className="pt-1 text-[11px] text-[#ff8533] flex items-center gap-1.5 border-t border-[#1e293b]">
        <span>🚨</span>
        <span className="font-medium">
          {isBangla
            ? "জরুরি হেল্পলাইন: যেকোনো ফোন থেকে ৯৯৯ বা ১০২ নম্বরে বিনামূল্যে কল করুন।"
            : "Free emergency helpline: Call 999 or 102 from any phone."}
        </span>
      </div>
    </div>
  );
}
