import type { MetricType } from "@/features/areas";

export interface HeatmapCell {
  h3: string;
  value: number;
  frp_mw?: number | null;
  lat?: number | null;
  lon?: number | null;
}

export interface HeatmapStats {
  min: number;
  p50: number;
  p95: number;
  max: number;
  sum: number;
  count: number;
}

export interface HeatmapData {
  res: 5 | 6 | 7;
  metric: MetricType;
  from: string;
  to: string;
  cells: HeatmapCell[];
  stats: HeatmapStats;
}

export interface MapViewport {
  longitude: number;
  latitude: number;
  zoom: number;
  pitch: number;
  bearing: number;
}
