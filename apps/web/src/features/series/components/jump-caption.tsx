import * as React from "react";
import { useLanguage } from "@/lib/i18n";
import type { MethodologyJumpMetrics } from "../types";
import { cn } from "@/lib/utils";

export interface JumpCaptionProps {
  metrics?: MethodologyJumpMetrics | null;
  className?: string;
}

export function JumpCaption({ metrics, className }: JumpCaptionProps) {
  const { t, isBangla } = useLanguage();
  const jumpObj = (metrics as { jump_metrics?: MethodologyJumpMetrics })?.jump_metrics || metrics;
  if (!jumpObj || jumpObj.naive_ratio === undefined) return null;

  const naiveRatioFormatted = jumpObj.naive_ratio.toFixed(2);
  const harmonizedRatioFormatted = jumpObj.harmonized_ratio.toFixed(2);
  const reductionFormatted =
    jumpObj.jump_reduction_pct !== undefined
      ? Math.round(jumpObj.jump_reduction_pct)
      : Math.round(
          ((jumpObj.naive_ratio - jumpObj.harmonized_ratio) /
            (jumpObj.naive_ratio - 1.0)) *
            100
        );

  return (
    <div
      role="note"
      aria-label="Sensor splice jump analysis"
      data-testid="jump-caption"
      className={cn(
        "rounded-lg border border-[#2d3b55] bg-[#0e141f] p-3 text-xs text-[#f8fafc] shadow-sm space-y-2",
        className
      )}
    >
      <div className="flex items-center gap-2">
        <span className="flex h-2 w-2 rounded-full bg-[#ff6b00]" />
        <span className="font-semibold text-xs text-[#ff6b00]">
          {isBangla ? t.jump.caption_title : "The \u201cHidden Jump\u201d Calibration Analysis:"}
        </span>
      </div>

      <p className="text-[#cbd5e1] text-[11px] sm:text-xs leading-relaxed">
        {isBangla ? (
          <>
            সমন্বয় ছাড়া ২০১২-২০১৬ সালে আগুনের সংখ্যা পুরোনো হিসাবের চেয়ে{" "}
            <strong className="text-[#f59e0b] font-mono">
              {naiveRatioFormatted}× বেশি
            </strong>{" "}
            মনে হতো, কারণ নতুন স্যাটেলাইটের ক্যামেরা ৪ গুণ বেশি স্পষ্ট। কিন্তু পাইরোস্কোপের তথ্য সামঞ্জস্যের পর এই অনুপাত স্বাভাবিক{" "}
            <strong className="text-[#ff6b00] font-mono">
              {harmonizedRatioFormatted}×
            </strong>{" "}
            ({reductionFormatted}% কৃত্রিম ভুল সংশোধন করা হয়েছে)।
          </>
        ) : (
          <>
            Without harmonization, annual fire counts in the 2012–2016 period appear{" "}
            <strong className="text-[#f59e0b] font-mono">
              {naiveRatioFormatted}× higher
            </strong>{" "}
            than the pre-2012 MODIS baseline due to VIIRS 375m sensor resolution.
            After quantile-mapping harmonization, the post-to-pre ratio is{" "}
            <strong className="text-[#ff6b00] font-mono">
              {harmonizedRatioFormatted}×
            </strong>{" "}
            ({reductionFormatted}% artificial discontinuity removed).
          </>
        )}
      </p>

      {/* Everyday plain-language explanation for non-technical users */}
      <div className="p-2.5 rounded bg-[#141e30] border border-[#21304b] text-[11px] text-[#94a3b8] leading-snug">
        <strong className="text-white">
          {isBangla ? "💡 সহজ কথায় অর্থ: " : "💡 What this means in plain words: "}
        </strong>
        {isBangla ? (
          <span>
            ২০১২ সালে বাংলাদেশে হঠাৎ আগুন তিন গুণ বেড়ে যায়নি। নাসা নতুন ও শক্তিশালী ক্যামেরা পাঠায় যা ছোট ছোট আগুনও দেখতে পায়। পাইরোস্কোপ এই হিসাব ঠিক করে যাতে ২৫ বছরের প্রকৃত সত্য চিত্র দেখা যায়।
          </span>
        ) : (
          <span>
            Fires did not suddenly triple in 2012. NASA launched a 4× sharper camera that detected smaller farm fires. PyroScope fixes this false jump so communities get honest 25-year fire trends.
          </span>
        )}
      </div>
    </div>
  );
}
