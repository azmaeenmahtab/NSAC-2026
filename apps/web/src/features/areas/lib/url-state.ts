import type { ViewState, MetricType } from "../types";
import { parseBBox, isValidBBox } from "./bbox";

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

const DATE_REGEX = /^\d{4}-(0[1-9]|1[0-2])$/;
const CELL_REGEX = /^[0-9a-fA-F]{15}$/;
const SLUG_REGEX = /^[a-zA-Z0-9_-]+$/;

interface SearchParamsReader {
  get(name: string): string | null;
}

export function parseViewState(
  searchParams: SearchParamsReader | URLSearchParams | null
): ViewState {
  if (!searchParams) return { ...DEFAULT_VIEW_STATE };

  let area = searchParams.get("area") || DEFAULT_VIEW_STATE.area;
  if (area.startsWith("bbox:")) {
    const bbox = parseBBox(area);
    if (!bbox || !isValidBBox(bbox)) {
      area = DEFAULT_VIEW_STATE.area;
    }
  } else if (!SLUG_REGEX.test(area)) {
    area = DEFAULT_VIEW_STATE.area;
  }

  let from = searchParams.get("from") || DEFAULT_VIEW_STATE.from;
  let to = searchParams.get("to") || DEFAULT_VIEW_STATE.to;

  if (!DATE_REGEX.test(from) || !DATE_REGEX.test(to)) {
    from = DEFAULT_VIEW_STATE.from;
    to = DEFAULT_VIEW_STATE.to;
  } else if (from > to) {
    const tmp = from;
    from = to;
    to = tmp;
  }

  const rawMetric = searchParams.get("metric") as MetricType;
  const metric: MetricType =
    rawMetric && VALID_METRICS.has(rawMetric) ? rawMetric : DEFAULT_VIEW_STATE.metric;

  const rawCell = searchParams.get("cell");
  const cell = rawCell && CELL_REGEX.test(rawCell) ? rawCell.toLowerCase() : null;

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
