import { useQuery } from "@tanstack/react-query";
import { apiGet, type ApiResponse } from "@/lib/api/client";
import type { HeatmapData } from "../types";
import type { MetricType } from "@/features/areas";
import type { H3Resolution } from "../lib/resolution";

export interface UseHeatmapParams {
  area?: string;
  from?: string;
  to?: string;
  metric?: MetricType;
  res?: H3Resolution;
}

export function useHeatmap(params: UseHeatmapParams) {
  const { area = "PRESET-CHT", from = "2020-01", to = "2025-12", metric = "harmonized", res = 7 } = params;

  return useQuery({
    queryKey: ["heatmap", area, from, to, metric, res],
    queryFn: ({ signal }) =>
      apiGet<ApiResponse<HeatmapData>>(
        "/heatmap",
        { area, from, to, metric, res },
        { signal }
      ),
    staleTime: 60 * 1000,
  });
}
