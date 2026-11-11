"use client";

import React, { useMemo, useState, useCallback, useEffect } from "react";
import { Map, NavigationControl, useControl } from "react-map-gl/maplibre";
import { MapboxOverlay, type MapboxOverlayProps } from "@deck.gl/mapbox";
import type { PickingInfo } from "@deck.gl/core";
import { useViewState, useAreas } from "@/features/areas";
import { useHeatmap } from "../api/use-heatmap";
import { useMapViewport } from "../hooks/use-map-viewport";
import { createH3HexagonLayer } from "../lib/layer";
import { HexTooltip } from "./hex-tooltip";
import { MapLegend } from "./legend";
import { MapControls } from "./map-controls";
import { MetricToggle } from "./metric-toggle";
import { TimeRange } from "./time-range";
import type { HeatmapCell } from "../types";
import { env } from "@/lib/env";
import "maplibre-gl/dist/maplibre-gl.css";

function DeckGLOverlay(props: MapboxOverlayProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

export function FireMap() {
  const { area, from, to, metric, cell: selectedCell, setMetric, setDateRange, setCell } = useViewState();
  const { data: areasData } = useAreas();
  const { viewport, setViewport, res, fitToBBox, resetView } = useMapViewport(area);

  const [is3d, setIs3d] = useState(true);
  const [hovered, setHovered] = useState<{
    cell: HeatmapCell;
    x: number;
    y: number;
  } | null>(null);

  // Auto-fit bounds when area changes
  useEffect(() => {
    if (area.startsWith("bbox:")) {
      fitToBBox(area);
    } else {
      const areaItem = areasData?.data?.find((a) => a.id === area);
      if (areaItem?.bbox) {
        fitToBBox(`bbox:${areaItem.bbox.join(",")}`);
      }
    }
  }, [area, areasData, fitToBBox]);

  const { data: heatmapEnvelope, isLoading, error } = useHeatmap({
    area,
    from,
    to,
    metric,
    res,
  });

  const heatmap = heatmapEnvelope?.data;
  const cells = useMemo(() => heatmap?.cells || [], [heatmap?.cells]);
  const stats = heatmap?.stats;

  const handleHover = useCallback((info: PickingInfo<HeatmapCell>) => {
    if (info.object) {
      setHovered({ cell: info.object, x: info.x, y: info.y });
    } else {
      setHovered(null);
    }
  }, []);

  const handleClick = useCallback(
    (info: PickingInfo<HeatmapCell>) => {
      if (info.object) {
        setCell(info.object.h3);
      }
    },
    [setCell]
  );

  const layers = useMemo(() => {
    return [
      createH3HexagonLayer({
        data: cells,
        p95: stats?.p95 || 50,
        is3d,
        selectedCell,
        onHover: handleHover,
        onClick: handleClick,
      }),
    ];
  }, [cells, stats?.p95, is3d, selectedCell, handleHover, handleClick]);

  return (
    <div className="relative flex flex-1 flex-col h-full w-full overflow-hidden bg-[#080b10]">
      {/* Top Filter and Controls Bar */}
      <div className="z-30 flex flex-wrap items-center justify-between gap-2 border-b border-[#1f293d] bg-[#0e141f]/90 px-4 py-2 backdrop-blur-md">
        <div className="flex items-center gap-3 flex-wrap">
          <MetricToggle value={metric} onChange={setMetric} />
          <TimeRange from={from} to={to} onChange={setDateRange} />
        </div>
        <MapControls
          is3d={is3d}
          onToggle3d={() => setIs3d((v) => !v)}
          onResetView={resetView}
          res={res}
          cellCount={cells.length}
        />
      </div>

      {/* Accessible Text Summary */}
      <div className="sr-only" aria-live="polite">
        Fire map for area {area}, period {from} to {to}. Showing {cells.length} cells.
        {stats && ` Peak cell value: ${stats.max}, 95th percentile: ${stats.p95}.`}
      </div>

      {/* Main Map Viewport */}
      <div className="relative flex-1 w-full h-full">
        {isLoading && (
          <div className="absolute top-4 left-4 z-20 rounded bg-[#0e141f]/80 px-2.5 py-1 text-xs text-[#ff6b00] border border-[#2d3b55]">
            Loading telemetry...
          </div>
        )}

        {error && (
          <div className="absolute top-4 left-4 z-20 rounded bg-[#ef4444]/20 px-3 py-1.5 text-xs text-[#ef4444] border border-[#dc2626]">
            Failed to load spatial heatmap
          </div>
        )}

        <Map
          {...viewport}
          onMove={(evt) => setViewport(evt.viewState)}
          mapStyle={env.basemapStyleUrl}
          style={{ width: "100%", height: "100%" }}
          attributionControl={false}
        >
          <DeckGLOverlay layers={layers} />
          <NavigationControl position="top-right" />
        </Map>

        {/* Legend Overlay at Bottom Left */}
        <div className="absolute bottom-4 left-4 z-20">
          <MapLegend stats={stats} metric={metric} />
        </div>

        {/* Floating Tooltip */}
        <HexTooltip
          cell={hovered?.cell || null}
          x={hovered?.x || 0}
          y={hovered?.y || 0}
          metric={metric}
        />
      </div>
    </div>
  );
}
