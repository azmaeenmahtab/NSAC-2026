"use client";

import * as React from "react";
import { useMeta } from "@/features/shell";
import { useLanguage } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export interface AttributionProps {
  className?: string;
}

export function Attribution({ className }: AttributionProps) {
  const { data: metaResponse } = useMeta();
  const { t, isBangla } = useLanguage();
  const [showNotice, setShowNotice] = React.useState(false);

  const attributionText =
    metaResponse?.data?.attribution ||
    "We acknowledge the use of data and imagery from NASA's FIRMS (EOSDIS), courtesy of NASA LANCE and UMD. Basemap © OpenStreetMap, © MapLibre. Boundaries: geoBoundaries (CC-BY 3.0 IGO / CC0).";

  return (
    <>
      <footer
        className={cn(
          "flex flex-col sm:flex-row items-center justify-between gap-2 border-t border-[#1f293d] bg-[#080b10] px-4 py-2 text-[10px] text-[#64748b] relative z-20",
          className
        )}
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span>{attributionText}</span>
          <button
            type="button"
            onClick={() => setShowNotice(true)}
            className="text-[#ff6b00] hover:underline font-medium cursor-pointer"
          >
            {t.attribution.safety_notice}
          </button>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span className="font-medium text-[#94a3b8]">
            {t.attribution.team}
          </span>
          <span>•</span>
          <span>
            {isBangla ? "নাসা স্পেস অ্যাপস চ্যালেঞ্জ ২০২৬" : "NASA Space Apps Challenge 2026"}
          </span>
        </div>
      </footer>

      {showNotice && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="safety-notice-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4"
        >
          <div className="max-w-lg rounded-xl border border-[#2d3b55] bg-[#0e141f] p-5 shadow-2xl text-xs space-y-3">
            <div className="flex items-center justify-between border-b border-[#1f293d] pb-2">
              <h3 id="safety-notice-title" className="font-semibold text-white flex items-center gap-1.5">
                <span>⚠️</span>
                <span>{t.attribution.safety_title}</span>
              </h3>
              <button
                type="button"
                onClick={() => setShowNotice(false)}
                className="text-[#64748b] hover:text-white text-sm"
                aria-label="Close safety notice dialog"
              >
                ✕
              </button>
            </div>

            <p className="text-[#cbd5e1] leading-relaxed">
              <strong className="text-white">
                {isBangla ? "বিজ্ঞপ্তি: " : "NOTICE: "}
              </strong>
              {t.attribution.notice_lead}{" "}
              {t.attribution.notice_body1}
            </p>

            <div className="p-3 rounded-lg bg-red-950/30 border border-red-800/40 text-red-200 space-y-1">
              <p className="font-medium">
                {t.attribution.notice_body2}
              </p>
              <p className="font-bold text-sm text-red-300">
                🚨 {t.attribution.notice_emergency}
              </p>
            </div>

            <div className="pt-2 text-right">
              <button
                type="button"
                onClick={() => setShowNotice(false)}
                className="px-4 py-1.5 rounded-lg bg-[#ff6b00] text-white font-medium hover:bg-[#e05e00] transition-colors cursor-pointer"
              >
                {t.attribution.close_btn}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
