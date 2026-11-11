import { useQuery } from "@tanstack/react-query";
import { apiGet, type ApiResponse } from "@/lib/api/client";
import type { CalendarData } from "../types";

export function useCalendar(area = "PRESET-CHT") {
  return useQuery({
    queryKey: ["calendar", area],
    queryFn: ({ signal }) =>
      apiGet<ApiResponse<CalendarData>>("/calendar", { area }, { signal }),
    staleTime: 5 * 60 * 1000,
  });
}
