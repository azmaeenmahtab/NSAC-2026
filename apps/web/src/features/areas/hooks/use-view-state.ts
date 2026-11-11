"use client";

import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useCallback, useMemo } from "react";
import type { ViewState, MetricType } from "../types";
import { parseViewState, serializeViewState } from "../lib/url-state";

export function useViewState() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const state: ViewState = useMemo(() => {
    return parseViewState(searchParams);
  }, [searchParams]);

  const updateUrl = useCallback(
    (newState: ViewState) => {
      const params = serializeViewState(newState);
      const queryString = params.toString();
      const newUrl = queryString ? `${pathname}?${queryString}` : pathname;
      router.replace(newUrl, { scroll: false });
    },
    [pathname, router]
  );

  const setArea = useCallback(
    (areaId: string) => {
      // Switching areas clears the selected H3 cell
      updateUrl({ ...state, area: areaId, cell: null });
    },
    [state, updateUrl]
  );

  const setDateRange = useCallback(
    (from: string, to: string) => {
      updateUrl({ ...state, from, to });
    },
    [state, updateUrl]
  );

  const setMetric = useCallback(
    (metric: MetricType) => {
      updateUrl({ ...state, metric });
    },
    [state, updateUrl]
  );

  const setCell = useCallback(
    (cellId: string | null) => {
      updateUrl({ ...state, cell: cellId });
    },
    [state, updateUrl]
  );

  const setViewState = useCallback(
    (patch: Partial<ViewState>) => {
      updateUrl({ ...state, ...patch });
    },
    [state, updateUrl]
  );

  return {
    state,
    area: state.area,
    from: state.from,
    to: state.to,
    metric: state.metric,
    cell: state.cell,
    setArea,
    setDateRange,
    setMetric,
    setCell,
    setViewState,
  };
}
