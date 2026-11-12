"use client";

import React, { useState } from "react";
import { AreaSelector, AreaBreadcrumb, BBoxDraw, useViewState } from "@/features/areas";
import { AlertStateCard, SubscribeForm, useActiveAlerts } from "@/features/alerts";
import { NearbyStationsPanel } from "@/features/stations";

export function SidePanelContent() {
  const { area, setArea } = useViewState();
  const { data: alerts } = useActiveAlerts(area);
  const [showSubscribe, setShowSubscribe] = useState(false);

  return (
    <div className="space-y-4">
      <AreaBreadcrumb currentAreaId={area} onAreaChange={setArea} />

      <div className="rounded-lg border border-[#1f293d] bg-[#161f30] p-3">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-semibold text-xs text-[#f8fafc]">
            Select Region
          </h4>
          <span className="text-[10px] text-[#ff6b00] font-mono">64 Districts</span>
        </div>
        <AreaSelector selectedId={area} onSelect={setArea} />
      </div>

      <BBoxDraw
        currentAreaId={area}
        onSelectBBox={setArea}
        onClear={() => setArea("PRESET-CHT")}
      />

      <AlertStateCard
        areaId={area}
        alerts={alerts}
        onSubscribeClick={() => setShowSubscribe(!showSubscribe)}
      />

      {showSubscribe && (
        <div className="pt-2">
          <SubscribeForm
            areaId={area}
            onSuccess={() => setTimeout(() => setShowSubscribe(false), 3000)}
          />
        </div>
      )}

      <NearbyStationsPanel areaId={area} />
    </div>
  );
}
