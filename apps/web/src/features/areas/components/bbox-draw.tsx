"use client";

import * as React from "react";
import { formatBBox, parseBBox, calculateBBoxAreaKm2, type BoundingBox } from "../lib/bbox";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export interface BBoxDrawProps {
  currentAreaId: string;
  onSelectBBox: (bboxStr: string) => void;
  onClear: () => void;
  className?: string;
}

export function BBoxDraw({
  currentAreaId,
  onSelectBBox,
  onClear,
  className,
}: BBoxDrawProps) {
  const currentBBox = React.useMemo(() => {
    return parseBBox(currentAreaId);
  }, [currentAreaId]);

  const [west, setWest] = React.useState(currentBBox ? String(currentBBox[0]) : "91.8");
  const [south, setSouth] = React.useState(currentBBox ? String(currentBBox[1]) : "21.5");
  const [east, setEast] = React.useState(currentBBox ? String(currentBBox[2]) : "92.8");
  const [north, setNorth] = React.useState(currentBBox ? String(currentBBox[3]) : "23.8");

  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const w = parseFloat(west);
    const s = parseFloat(south);
    const eCoord = parseFloat(east);
    const n = parseFloat(north);

    if (isNaN(w) || isNaN(s) || isNaN(eCoord) || isNaN(n)) {
      setErrorMessage("All bounding box coordinates must be valid floating point numbers.");
      return;
    }

    if (w >= eCoord) {
      setErrorMessage("West longitude must be strictly less than East longitude.");
      return;
    }

    if (s >= n) {
      setErrorMessage("South latitude must be strictly less than North latitude.");
      return;
    }

    if (w < -180 || eCoord > 180 || s < -90 || n > 90) {
      setErrorMessage("Coordinates out of range (-180..180 lon, -90..90 lat).");
      return;
    }

    if (eCoord - w > 6.0 || n - s > 6.0) {
      setErrorMessage("Bounding box too large: maximum span is 6.0° in longitude and latitude.");
      return;
    }

    const bbox: BoundingBox = [w, s, eCoord, n];
    onSelectBBox(formatBBox(bbox));
  };

  const parsedActiveBBox = parseBBox(currentAreaId);
  const areaKm2 = parsedActiveBBox ? calculateBBoxAreaKm2(parsedActiveBBox) : null;

  return (
    <div
      className={cn(
        "rounded-lg border border-[#1f293d] bg-[#0e141f] p-3 text-xs space-y-3",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="font-semibold text-xs text-[#f8fafc]">
          Custom Bounding Box
        </span>
        {currentAreaId.startsWith("bbox:") && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClear}
            className="h-6 text-[11px] text-[#ff6b00]"
          >
            Clear custom box
          </Button>
        )}
      </div>

      <form onSubmit={handleApply} className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label htmlFor="bbox-west" className="text-[10px] text-[#64748b]">
              West (min Lon)
            </label>
            <Input
              id="bbox-west"
              value={west}
              onChange={(e) => setWest(e.target.value)}
              className="h-7 text-xs font-mono"
            />
          </div>
          <div>
            <label htmlFor="bbox-east" className="text-[10px] text-[#64748b]">
              East (max Lon)
            </label>
            <Input
              id="bbox-east"
              value={east}
              onChange={(e) => setEast(e.target.value)}
              className="h-7 text-xs font-mono"
            />
          </div>
          <div>
            <label htmlFor="bbox-south" className="text-[10px] text-[#64748b]">
              South (min Lat)
            </label>
            <Input
              id="bbox-south"
              value={south}
              onChange={(e) => setSouth(e.target.value)}
              className="h-7 text-xs font-mono"
            />
          </div>
          <div>
            <label htmlFor="bbox-north" className="text-[10px] text-[#64748b]">
              North (max Lat)
            </label>
            <Input
              id="bbox-north"
              value={north}
              onChange={(e) => setNorth(e.target.value)}
              className="h-7 text-xs font-mono"
            />
          </div>
        </div>

        {errorMessage && (
          <div className="text-[11px] text-[#ef4444] bg-[#ef4444]/10 p-1.5 rounded border border-[#ef4444]/30">
            {errorMessage}
          </div>
        )}

        {areaKm2 !== null && (
          <div className="text-[10px] text-[#94a3b8] font-mono">
            Selected box footprint: ~{Math.round(areaKm2).toLocaleString()} km²
          </div>
        )}

        <Button type="submit" variant="accent" size="sm" className="w-full h-7 text-xs">
          Apply Bounding Box
        </Button>
      </form>
    </div>
  );
}
