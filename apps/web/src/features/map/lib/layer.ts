import { H3HexagonLayer } from "@deck.gl/geo-layers";
import type { PickingInfo } from "@deck.gl/core";
import { infernoRgba } from "@/lib/color/scales";
import type { HeatmapCell } from "../types";

export interface CreateH3HexagonLayerOptions {
  data: HeatmapCell[];
  p95: number;
  is3d: boolean;
  selectedCell: string | null;
  onHover?: (info: PickingInfo<HeatmapCell>) => void;
  onClick?: (info: PickingInfo<HeatmapCell>) => void;
}

export function createH3HexagonLayer(options: CreateH3HexagonLayerOptions) {
  const { data, p95, is3d, selectedCell, onHover, onClick } = options;

  return new H3HexagonLayer<HeatmapCell>({
    id: "h3-fire-layer",
    data,
    pickable: true,
    wireframe: false,
    filled: true,
    extruded: is3d,
    stroked: !is3d || !!selectedCell,
    getHexagon: (d: HeatmapCell) => d.h3,
    getFillColor: (d: HeatmapCell) => infernoRgba(d.value, p95),
    getElevation: (d: HeatmapCell) =>
      is3d ? Math.min(d.value / Math.max(1e-6, p95), 4) * 8000 : 0,
    elevationScale: 1,
    getLineColor: (d: HeatmapCell) =>
      d.h3 === selectedCell ? [255, 255, 255, 255] : [0, 0, 0, 0],
    lineWidthMinPixels: 2,
    updateTriggers: {
      getFillColor: [p95],
      getElevation: [is3d, p95],
      getLineColor: [selectedCell],
    },
    onHover: onHover ? (info) => onHover(info as PickingInfo<HeatmapCell>) : undefined,
    onClick: onClick ? (info) => onClick(info as PickingInfo<HeatmapCell>) : undefined,
  });
}
