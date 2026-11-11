import { useQuery } from "@tanstack/react-query";
import { apiGet, type ApiResponse } from "@/lib/api/client";
import type { SeriesPoint, MethodologyJumpMetrics } from "../types";

export interface UseSeriesParams {
  area?: string;
  from?: string;
  to?: string;
}

export function useSeries(params: UseSeriesParams = {}) {
  const { area = "PRESET-CHT", from, to } = params;

  return useQuery({
    queryKey: ["series", area, from, to],
    queryFn: ({ signal }) =>
      apiGet<ApiResponse<SeriesPoint[]>>(
        "/series",
        { area_id: area, from, to },
        { signal }
      ),
    staleTime: 5 * 60 * 1000,
  });
}

export function useMethodologyJump() {
  return useQuery({
    queryKey: ["methodology-jump"],
    queryFn: ({ signal }) =>
      apiGet<ApiResponse<MethodologyJumpMetrics>>("/methodology", {}, { signal }),
    staleTime: 60 * 60 * 1000,
  });
}

