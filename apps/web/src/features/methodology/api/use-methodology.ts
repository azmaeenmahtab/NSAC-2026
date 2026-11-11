import { useQuery } from "@tanstack/react-query";
import { apiGet, type ApiResponse } from "@/lib/api/client";
import type { MethodologyData } from "../types";

export function useMethodology() {
  return useQuery({
    queryKey: ["methodology"],
    queryFn: ({ signal }) =>
      apiGet<ApiResponse<MethodologyData>>("/methodology", {}, { signal }),
    staleTime: 60 * 60 * 1000,
  });
}
