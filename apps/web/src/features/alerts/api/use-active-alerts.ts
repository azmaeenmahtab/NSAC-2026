import { useQuery } from "@tanstack/react-query";
import { apiGetData } from "@/lib/api/client";
import type { ActiveAlerts } from "../types";

export function useActiveAlerts(areaId: string) {
  return useQuery<ActiveAlerts>({
    queryKey: ["active-alerts", areaId],
    queryFn: async () => {
      const data = await apiGetData<ActiveAlerts>("/alerts/active", {
        area_id: areaId,
      });
      return data;
    },
    staleTime: 2 * 60 * 1000,
    enabled: Boolean(areaId),
  });
}

