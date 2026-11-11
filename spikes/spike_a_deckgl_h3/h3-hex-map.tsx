"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { Map, NavigationControl, useControl } from "react-map-gl/maplibre";
import { MapboxOverlay, type MapboxOverlayProps } from "@deck.gl/mapbox";
import { H3HexagonLayer } from "@deck.gl/geo-layers";
import type { PickingInfo } from "@deck.gl/core";
import { interpolateInferno } from "d3-scale-chromatic";
import { rgb } from "d3-color";
import { gridDisk, latLngToCell } from "h3-js";
import "maplibre-gl/dist/maplibre-gl.css";

export interface HexCellDatum {
  h3: string;
  value: number;
}

const DEFAULT_BASEMAP_STYLE =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

const BANGLADESH_VIEW_STATE = {
  longitude: 90.3563,
  latitude: 23.685,
  zoom: 7,
  pitch: 35,
  bearing: 0,
};

function DeckGLOverlay(props: MapboxOverlayProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

export function generateSyntheticBangladeshHexes(count = 30_000): HexCellDatum[] {
  const center = latLngToCell(23.685, 90.3563, 7);
  const ring = gridDisk(center, 110).slice(0, count);
  return ring.map((h3Index, idx) => ({
    h3: h3Index,
    value: ((idx * 37) % 100) + 1,
  }));
}

export function infernoRgba(value: number, p95: number): [number, number, number, number] {
  const t = Math.max(0, Math.min(1, value / Math.max(1e-6, p95)));
  const c = rgb(interpolateInferno(t));
  return [c.r, c.g, c.b, 215];
}

export function H3HexMapSpike() {
  const [extruded, setExtruded] = useState<boolean>(true);
  const [hovered, setHovered] = useState<{ h3: string; value: number; x: number; y: number } | null>(
    null,
  );
  const [selectedH3, setSelectedH3] = useState<string | null>(null);
  const [fps, setFps] = useState<number>(60);
  const mountTimeRef = useRef<number>(performance.now());
  const [firstRenderMs, setFirstRenderMs] = useState<number | null>(null);

  const data = useMemo(() => generateSyntheticBangladeshHexes(30_000), []);
  const p95 = 95;

  useEffect(() => {
    let frames = 0;
    let last = performance.now();
    let rafId = 0;
    const tick = (now: number) => {
      frames += 1;
      if (now - last >= 1000) {
        setFps(Math.round((frames * 1000) / (now - last)));
        frames = 0;
        last = now;
      }
      rafId = requestAnimationFrame(tick);
    };
    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, []);

  const layers = useMemo(
    () => [
      new H3HexagonLayer<HexCellDatum>({
        id: "pyroscope-h3-layer",
        data,
        pickable: true,
        filled: true,
        extruded,
        wireframe: false,
        stroked: true,
        elevationScale: extruded ? 60 : 0,
        getHexagon: (d: HexCellDatum) => d.h3,
        getFillColor: (d: HexCellDatum) => infernoRgba(d.value, p95),
        getElevation: (d: HexCellDatum) => d.value,
        getLineColor: (d: HexCellDatum) =>
          d.h3 === selectedH3 ? [255, 255, 255, 255] : [0, 0, 0, 40],
        lineWidthMinPixels: 1,
        updateTriggers: {
          getLineColor: [selectedH3],
          getElevation: [extruded],
        },
        onHover: (info: PickingInfo<HexCellDatum>) => {
          if (info.object) {
            setHovered({
              h3: info.object.h3,
              value: info.object.value,
              x: info.x,
              y: info.y,
            });
          } else {
            setHovered(null);
          }
        },
        onClick: (info: PickingInfo<HexCellDatum>) => {
          if (info.object) {
            setSelectedH3(info.object.h3);
          }
        },
      }),
    ],
    [data, extruded, selectedH3],
  );

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative" }}>
      <Map
        initialViewState={BANGLADESH_VIEW_STATE}
        mapStyle={DEFAULT_BASEMAP_STYLE}
        onLoad={() => {
          if (firstRenderMs === null) {
            setFirstRenderMs(Math.round(performance.now() - mountTimeRef.current));
          }
        }}
      >
        <NavigationControl position="top-right" />
        <DeckGLOverlay layers={layers} interleaved={false} />
      </Map>

      <div
        style={{
          position: "absolute",
          top: 12,
          left: 12,
          background: "rgba(9, 9, 11, 0.88)",
          color: "#f4f4f5",
          padding: "10px 14px",
          borderRadius: 8,
          fontSize: 13,
        }}
      >
        <div>Cells: {data.length.toLocaleString()} (H3 r7)</div>
        <div>FPS: {fps} | First render: {firstRenderMs ?? "..."} ms</div>
        <div>Selected: {selectedH3 ?? "none"}</div>
        <button
          type="button"
          onClick={() => setExtruded((prev) => !prev)}
          style={{ marginTop: 6, padding: "4px 8px", cursor: "pointer" }}
        >
          Toggle {extruded ? "2D Flat" : "3D Extruded"}
        </button>
      </div>

      {hovered && (
        <div
          style={{
            position: "absolute",
            left: hovered.x + 12,
            top: hovered.y + 12,
            background: "rgba(9, 9, 11, 0.92)",
            color: "#fafafa",
            padding: "6px 10px",
            borderRadius: 6,
            pointerEvents: "none",
            fontSize: 12,
          }}
        >
          <strong>{hovered.h3.slice(0, 10)}…</strong>: {hovered.value.toFixed(1)} events
        </div>
      )}
    </div>
  );
}
