import * as React from "react";
import type { SeriesVisibility } from "../types";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface SeriesTogglesProps {
  visibility: SeriesVisibility;
  onChange: (visibility: SeriesVisibility) => void;
  storyStep: number; // 0 = custom/all, 1 = raw only, 2 = naive splice, 3 = harmonized
  onStoryStepChange: (step: number) => void;
  className?: string;
}

export function SeriesToggles({
  visibility,
  onChange,
  storyStep,
  onStoryStepChange,
  className,
}: SeriesTogglesProps) {
  const toggleKey = (key: keyof SeriesVisibility) => {
    onStoryStepChange(0); // custom
    onChange({ ...visibility, [key]: !visibility[key] });
  };

  const handleStoryClick = () => {
    const nextStep = (storyStep % 3) + 1;
    onStoryStepChange(nextStep);

    if (nextStep === 1) {
      // Step 1: Raw observations only
      onChange({ raw_modis: true, raw_viirs: true, naive_splice: false, harmonized: false });
    } else if (nextStep === 2) {
      // Step 2: The Naive Splice (3x jump)
      onChange({ raw_modis: false, raw_viirs: false, naive_splice: true, harmonized: false });
    } else {
      // Step 3: Harmonized vs Naive
      onChange({ raw_modis: false, raw_viirs: false, naive_splice: true, harmonized: true });
    }
  };

  return (
    <div className={cn("flex flex-wrap items-center justify-between gap-3 text-xs", className)}>
      {/* Individual Series Toggles */}
      <div className="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          onClick={() => toggleKey("harmonized")}
          className={cn(
            "flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-medium border transition-colors cursor-pointer",
            visibility.harmonized
              ? "border-[#ff6b00] bg-[#ff6b00]/15 text-[#ff6b00]"
              : "border-[#1f293d] bg-[#161f30] text-[#64748b]"
          )}
        >
          <span className="h-2 w-2 rounded-full bg-[#ff6b00]" />
          Harmonized (PyroScope)
        </button>

        <button
          type="button"
          onClick={() => toggleKey("naive_splice")}
          className={cn(
            "flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-medium border transition-colors cursor-pointer",
            visibility.naive_splice
              ? "border-[#f59e0b] bg-[#f59e0b]/15 text-[#f59e0b]"
              : "border-[#1f293d] bg-[#161f30] text-[#64748b]"
          )}
        >
          <span className="h-2 w-2 rounded-full bg-[#f59e0b]" />
          Naive Splice
        </button>

        <button
          type="button"
          onClick={() => toggleKey("raw_viirs")}
          className={cn(
            "flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-medium border transition-colors cursor-pointer",
            visibility.raw_viirs
              ? "border-[#a855f7] bg-[#a855f7]/15 text-[#a855f7]"
              : "border-[#1f293d] bg-[#161f30] text-[#64748b]"
          )}
        >
          <span className="h-2 w-2 rounded-full bg-[#a855f7]" />
          Raw VIIRS
        </button>

        <button
          type="button"
          onClick={() => toggleKey("raw_modis")}
          className={cn(
            "flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-medium border transition-colors cursor-pointer",
            visibility.raw_modis
              ? "border-[#f97316] bg-[#f97316]/15 text-[#f97316]"
              : "border-[#1f293d] bg-[#161f30] text-[#64748b]"
          )}
        >
          <span className="h-2 w-2 rounded-full bg-[#f97316]" />
          Raw MODIS
        </button>
      </div>

      {/* Story Mode Stepper */}
      <div className="flex items-center gap-2">
        <Button
          variant={storyStep > 0 ? "accent" : "outline"}
          size="sm"
          onClick={handleStoryClick}
          className="h-7 text-xs font-semibold"
        >
          {storyStep === 1
            ? "Story: 1. Raw Mismatch →"
            : storyStep === 2
            ? "Story: 2. Naive 3× Jump →"
            : storyStep === 3
            ? "Story: 3. Harmonized ✨"
            : "▶ Step through Story"}
        </Button>

        {storyStep > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              onStoryStepChange(0);
              onChange({ raw_modis: true, raw_viirs: true, naive_splice: true, harmonized: true });
            }}
            className="h-7 text-[11px] text-[#94a3b8]"
          >
            Show All
          </Button>
        )}
      </div>
    </div>
  );
}
