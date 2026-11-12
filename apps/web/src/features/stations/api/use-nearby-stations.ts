import { useQuery } from "@tanstack/react-query";
import { apiGetData } from "@/lib/api/client";
import type { NearbyStationsData } from "../types";

export interface UseNearbyStationsParams {
  areaId: string;
  lat?: number | null;
  lon?: number | null;
  limit?: number;
}

export function useNearbyStations({
  areaId,
  lat,
  lon,
  limit = 4,
}: UseNearbyStationsParams) {
  return useQuery<NearbyStationsData>({
    queryKey: ["stations", "nearby", areaId, lat ?? null, lon ?? null, limit],
    queryFn: () => {
      const params = new URLSearchParams({
        area_id: areaId,
        limit: String(limit),
      });
      if (lat !== null && lat !== undefined && lon !== null && lon !== undefined) {
        params.set("lat", String(lat));
        params.set("lon", String(lon));
      }
      return apiGetData<NearbyStationsData>(`/stations/nearby?${params.toString()}`);
    },
    staleTime: 60_000,
  });
}

