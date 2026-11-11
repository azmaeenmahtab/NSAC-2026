"use client";

import * as React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "./empty-state";
import { ErrorState } from "./error-state";
import { ApiError } from "@/lib/api/errors";

export interface QueryBoundaryProps<T = unknown> {
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  data?: T;
  isEmpty?: boolean | ((data: T) => boolean);
  onRetry?: () => void;
  loadingFallback?: React.ReactNode;
  emptyFallback?: React.ReactNode;
  children: React.ReactNode | ((data: T) => React.ReactNode);
}

export function QueryBoundary<T = unknown>({
  isLoading,
  isError,
  error,
  data,
  isEmpty,
  onRetry,
  loadingFallback,
  emptyFallback,
  children,
}: QueryBoundaryProps<T>) {
  if (isLoading) {
    if (loadingFallback) return <>{loadingFallback}</>;
    return (
      <div className="space-y-3 p-4" data-testid="query-loading">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (isError) {
    const apiError = error instanceof ApiError ? error : undefined;
    return (
      <div data-testid="query-error">
        <ErrorState
          title="Failed to load telemetry"
          message={error?.message || "An unexpected error occurred."}
          code={apiError?.code}
          requestId={apiError?.requestId}
          onRetry={onRetry}
        />
      </div>
    );
  }

  const checkEmpty = (): boolean => {
    if (typeof isEmpty === "boolean") return isEmpty;
    if (typeof isEmpty === "function" && data !== undefined) {
      return isEmpty(data);
    }
    if (Array.isArray(data)) return data.length === 0;
    if (data === null || data === undefined) return true;
    return false;
  };

  if (checkEmpty()) {
    if (emptyFallback) return <>{emptyFallback}</>;
    return (
      <div data-testid="query-empty">
        <EmptyState />
      </div>
    );
  }

  return (
    <div data-testid="query-content">
      {typeof children === "function" ? (children as (data: T) => React.ReactNode)(data as T) : children}
    </div>
  );
}
