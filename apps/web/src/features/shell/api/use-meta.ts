import { useQuery } from "@tanstack/react-query";
import { apiGet, type ApiResponse } from "@/lib/api/client";
import type { MetaData } from "../types";

export function useMeta() {
  return useQuery({
    queryKey: ["meta"],
    queryFn: () => apiGet<ApiResponse<MetaData>>("/meta"),
    staleTime: 5 * 60 * 1000,
  });
}
