import * as React from "react";
import type { MetricType } from "@/features/areas";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { cn } from "@/lib/utils";

export interface MetricToggleProps {
  value: MetricType;
  onChange: (metric: MetricType) => void;
  className?: string;
}

export function MetricToggle({
  value,
  onChange,
  className,
}: MetricToggleProps) {
  return (
    <div className={cn("inline-flex items-center gap-1.5", className)}>
      <span className="text-[11px] text-[#94a3b8] font-medium hidden sm:inline">
        Metric:
      </span>
      <ToggleGroup
        value={value}
        onValueChange={(val) => onChange(val as MetricType)}
      >
        <ToggleGroupItem value="harmonized" title="Calibrated MODIS-equivalent">
          Harmonized
        </ToggleGroupItem>
        <ToggleGroupItem value="raw_modis" title="Uncalibrated Terra + Aqua">
          Raw MODIS
        </ToggleGroupItem>
        <ToggleGroupItem value="raw_viirs" title="Uncalibrated S-NPP">
          Raw VIIRS
        </ToggleGroupItem>
      </ToggleGroup>
    </div>
  );
}
