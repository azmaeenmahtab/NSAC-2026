import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryBoundary } from "./query-boundary";
import { ApiError } from "@/lib/api/errors";

describe("QueryBoundary", () => {
  it("renders loading skeleton when isLoading is true", () => {
    render(
      <QueryBoundary isLoading={true} isError={false}>
        <div>Payload content</div>
      </QueryBoundary>
    );

    expect(screen.getByTestId("query-loading")).toBeInTheDocument();
    expect(screen.queryByText("Payload content")).not.toBeInTheDocument();
  });

  it("renders error state and handles onRetry callback", () => {
    const handleRetry = vi.fn();
    const error = new ApiError(404, {
      code: "NOT_FOUND",
      message: "Region dataset not found",
      requestId: "req-123",
    });

    render(
      <QueryBoundary
        isLoading={false}
        isError={true}
        error={error}
        onRetry={handleRetry}
      >
        <div>Payload content</div>
      </QueryBoundary>
    );

    expect(screen.getByTestId("query-error")).toBeInTheDocument();
    expect(screen.getByText("Region dataset not found")).toBeInTheDocument();
    expect(screen.getByText(/NOT_FOUND/)).toBeInTheDocument();

    const retryBtn = screen.getByRole("button", { name: /retry/i });
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it("renders empty state when data is empty array", () => {
    render(
      <QueryBoundary isLoading={false} isError={false} data={[]}>
        {() => <div>Payload content</div>}
      </QueryBoundary>
    );

    expect(screen.getByTestId("query-empty")).toBeInTheDocument();
    expect(screen.getByText("No data available")).toBeInTheDocument();
    expect(screen.queryByText("Payload content")).not.toBeInTheDocument();
  });

  it("renders children when valid data is loaded", () => {
    render(
      <QueryBoundary
        isLoading={false}
        isError={false}
        data={[{ id: "test-cell", value: 42 }]}
      >
        {(data) => (
          <div>
            Cell count: {data.length}, First: {data[0].id}
          </div>
        )}
      </QueryBoundary>
    );

    expect(screen.getByTestId("query-content")).toBeInTheDocument();
    expect(screen.getByText("Cell count: 1, First: test-cell")).toBeInTheDocument();
  });
});
