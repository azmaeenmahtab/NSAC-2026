import type { ViewState, MetricType } from "../types";

export const DEFAULT_VIEW_STATE: ViewState = {
  area: "PRESET-CHT",
  from: "2020-01",
  to: "2025-12",
  metric: "harmonized",
  cell: null,
};

const VALID_METRICS: Set<MetricType> = new Set([
  "harmonized",
  "raw_modis",
  "raw_viirs",
]);

interface SearchParamsReader {
  get(name: string): string | null;
}

export function parseViewState(
  searchParams: SearchParamsReader | URLSearchParams | null
): ViewState {
  if (!searchParams) return { ...DEFAULT_VIEW_STATE };

  const area = searchParams.get("area") || DEFAULT_VIEW_STATE.area;
  const from = searchParams.get("from") || DEFAULT_VIEW_STATE.from;
  const to = searchParams.get("to") || DEFAULT_VIEW_STATE.to;

  const rawMetric = searchParams.get("metric") as MetricType;
  const metric: MetricType =
    rawMetric && VALID_METRICS.has(rawMetric) ? rawMetric : DEFAULT_VIEW_STATE.metric;

  const cell = searchParams.get("cell") || null;

  return {
    area,
    from,
    to,
    metric,
    cell,
  };
}

export function serializeViewState(state: ViewState): URLSearchParams {
  const params = new URLSearchParams();

  if (state.area) params.set("area", state.area);
  if (state.from) params.set("from", state.from);
  if (state.to) params.set("to", state.to);
  if (state.metric) params.set("metric", state.metric);
  if (state.cell) params.set("cell", state.cell);

  return params;
}

