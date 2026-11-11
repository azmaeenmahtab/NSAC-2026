import * as React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface MapControlsProps {
  is3d: boolean;
  onToggle3d: () => void;
  onResetView: () => void;
  res: number;
  cellCount?: number;
  className?: string;
}

export function MapControls({
  is3d,
  onToggle3d,
  onResetView,
  res,
  cellCount,
  className,
}: MapControlsProps) {
  return (
    <div
      role="toolbar"
      aria-label="Map viewport controls"
      data-testid="map-controls"
      className={cn(
        "flex items-center gap-2 rounded-lg border border-[#1f293d] bg-[#0e141f]/90 p-1.5 shadow-lg backdrop-blur-md",
        className
      )}
    >
      <Button
        variant={is3d ? "accent" : "outline"}
        size="sm"
        onClick={onToggle3d}
        className="h-7 text-xs font-mono"
        aria-pressed={is3d}
      >
        {is3d ? "3D Extruded" : "2D Flat"}
      </Button>

      <Button
        variant="ghost"
        size="sm"
        onClick={onResetView}
        className="h-7 text-xs"
        title="Reset map camera"
      >
        Reset View
      </Button>

      <div className="h-4 w-px bg-[#1f293d]" />

      <Badge variant="outline" className="text-[10px] font-mono py-0 text-[#94a3b8]">
        H3 r{res}
      </Badge>

      {cellCount !== undefined && (
        <span className="text-[10px] font-mono text-[#64748b] hidden sm:inline">
          {cellCount.toLocaleString()} cells
        </span>
      )}
    </div>
  );
}
