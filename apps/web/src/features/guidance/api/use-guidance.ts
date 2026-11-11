import { useQuery } from "@tanstack/react-query";
import { apiGetData } from "@/lib/api/client";
import type { GuidanceItem } from "../types";

export function useGuidance(areaId: string, month?: number) {
  return useQuery<GuidanceItem[]>({
    queryKey: ["guidance", areaId, month],
    queryFn: async () => {
      const params: Record<string, unknown> = { area_id: areaId };
      if (month !== undefined) {
        params.month = month;
      }
      const data = await apiGetData<GuidanceItem[]>("/guidance", params);
      return data;
    },
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(areaId),
  });
}

