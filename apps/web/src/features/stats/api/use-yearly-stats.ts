import { useQuery } from "@tanstack/react-query";
import { apiGetData } from "@/lib/api/client";
import type { YearlyStatRow } from "../types";

export function useYearlyStats(areaId: string) {
  return useQuery<YearlyStatRow[]>({
    queryKey: ["yearly-stats", areaId],
    queryFn: async () => {
      const data = await apiGetData<YearlyStatRow[]>("/stats/yearly", {
        area_id: areaId,
      });
      return data;
    },
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(areaId),
  });
}

