"use client";

import { useState, useCallback, useMemo } from "react";
import type { MapViewport } from "../types";
import { getResolutionForZoom, type H3Resolution } from "../lib/resolution";
import { parseBBox, getBBoxCenter } from "@/features/areas";

export const DEFAULT_BANGLADESH_VIEW: MapViewport = {
  longitude: 90.3563,
  latitude: 23.685,
  zoom: 6.8,
  pitch: 30,
  bearing: 0,
};

export const DEFAULT_CHT_VIEW: MapViewport = {
  longitude: 92.2,
  latitude: 22.5,
  zoom: 7.8,
  pitch: 35,
  bearing: 0,
};

export function useMapViewport(initialArea = "PRESET-CHT") {
  const [viewport, setViewport] = useState<MapViewport>(() => {
    return initialArea === "BGD" ? DEFAULT_BANGLADESH_VIEW : DEFAULT_CHT_VIEW;
  });

  const res: H3Resolution = useMemo(() => {
    return getResolutionForZoom(viewport.zoom);
  }, [viewport.zoom]);

  const fitToBBox = useCallback((bboxStr: string) => {
    const bbox = parseBBox(bboxStr);
    if (!bbox) return;

    const [lon, lat] = getBBoxCenter(bbox);
    const spanLon = Math.abs(bbox[2] - bbox[0]);
    const spanLat = Math.abs(bbox[3] - bbox[1]);
    const maxSpan = Math.max(spanLon, spanLat);

    let targetZoom = 8.0;
    if (maxSpan > 4.0) targetZoom = 6.2;
    else if (maxSpan > 2.0) targetZoom = 7.0;
    else if (maxSpan > 1.0) targetZoom = 8.0;
    else if (maxSpan > 0.4) targetZoom = 9.0;
    else targetZoom = 10.0;

    setViewport((prev) => ({
      ...prev,
      longitude: lon,
      latitude: lat,
      zoom: targetZoom,
    }));
  }, []);

  const resetView = useCallback(() => {
    setViewport(DEFAULT_CHT_VIEW);
  }, []);

  return {
    viewport,
    setViewport,
    res,
    fitToBBox,
    resetView,
  };
}
