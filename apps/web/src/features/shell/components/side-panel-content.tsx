"use client";

import React from "react";
import { AreaSelector, AreaBreadcrumb, BBoxDraw, useViewState } from "@/features/areas";

export function SidePanelContent() {
  const { area, setArea } = useViewState();

  return (
    <div className="space-y-4">
      <AreaBreadcrumb currentAreaId={area} onAreaChange={setArea} />

      <div className="rounded-lg border border-[#1f293d] bg-[#161f30] p-3">
        <h4 className="font-semibold text-xs text-[#f8fafc] mb-2">
          Select Area of Interest
        </h4>
        <AreaSelector selectedId={area} onSelect={setArea} />
      </div>

      <BBoxDraw
        currentAreaId={area}
        onSelectBBox={setArea}
        onClear={() => setArea("PRESET-CHT")}
      />
    </div>
  );
}
