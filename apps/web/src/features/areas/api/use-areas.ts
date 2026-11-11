import { useQuery } from "@tanstack/react-query";
import { apiGet, type ApiResponse } from "@/lib/api/client";
import type { AreaItem } from "../types";

export function useAreas() {
  return useQuery({
    queryKey: ["areas"],
    queryFn: () => apiGet<ApiResponse<AreaItem[]>>("/areas"),
    staleTime: 60 * 60 * 1000, // Reference area boundaries change rarely
  });
}
