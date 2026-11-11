import { describe, it, expect, beforeAll, afterAll, afterEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { FireCalendar } from "./fire-calendar";
import { ClimatologyStrip } from "./climatology-strip";
import { server } from "@/mocks/server";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe("FireCalendar Component", () => {
  it("renders alpha fixture with April–June season band and May 2020 marked extreme", async () => {
    renderWithClient(<FireCalendar />);

    // Wait for the calendar to load from mock
    await waitFor(() => {
      expect(screen.getByTestId("fire-calendar")).toBeInTheDocument();
    });

    // Check SeasonBand renders April – June bracket
    expect(screen.getByText(/Apr – Jun/)).toBeInTheDocument();
    expect(screen.getByText(/71% of annual fires/)).toBeInTheDocument();
    expect(screen.getByText(/★ May/)).toBeInTheDocument();

    // Check 2020 May cell is marked extreme
    const mayCell = screen.getByRole("gridcell", {
      name: /May 2020, 200 events, extreme anomaly/,
    });
    expect(mayCell).toBeInTheDocument();
    expect(mayCell).toHaveClass("border-2");
    expect(mayCell).toHaveClass("border-solid");
    expect(mayCell).toHaveClass("border-[#ef4444]");

    // Check non-color indicator symbol (◆ for extreme)
    expect(mayCell).toHaveTextContent("◆");
  });

  it("renders provisional month with hatched style indicator", async () => {
    renderWithClient(<FireCalendar />);

    await waitFor(() => {
      expect(screen.getByTestId("fire-calendar")).toBeInTheDocument();
    });

    const dec2025Cell = screen.getByRole("gridcell", {
      name: /December 2025.*provisional/i,
    });
    expect(dec2025Cell).toBeInTheDocument();
    expect(dec2025Cell).toHaveTextContent("*");
  });

  it("supports keyboard navigation: Enter or Space opens MonthDetailDrawer", async () => {
    renderWithClient(<FireCalendar />);

    await waitFor(() => {
      expect(screen.getByTestId("fire-calendar")).toBeInTheDocument();
    });

    const mayCell = screen.getByRole("gridcell", {
      name: /May 2020, 200 events, extreme anomaly/,
    });

    // Press Enter to activate cell
    fireEvent.keyDown(mayCell, { key: "Enter" });

    // Drawer should open with details
    await waitFor(() => {
      expect(screen.getByText("May 2020")).toBeInTheDocument();
    });
    expect(screen.getByText(/Extreme Anomaly/i)).toBeInTheDocument();
    expect(screen.getAllByText("200").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Historical May Baseline")).toBeInTheDocument();
  });

  it("handles empty grid state gracefully", async () => {
    server.use(
      http.get("*/api/calendar", () => {
        return HttpResponse.json({
          data: { grid: [], climatology: [], season: null },
          meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
        });
      })
    );

    renderWithClient(<FireCalendar />);

    await waitFor(() => {
      expect(screen.getByText(/No data available/i)).toBeInTheDocument();
    });
  });

  it("handles error state and provides a retry button", async () => {
    server.use(
      http.get("*/api/calendar", () => {
        return HttpResponse.json({ message: "Internal Error" }, { status: 500 });
      })
    );

    renderWithClient(<FireCalendar />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Retry/i })).toBeInTheDocument();
    });
  });
});

describe("ClimatologyStrip Component", () => {
  it("renders 12 months with mean values and ticks", () => {
    const climatology = [
      { month: 1, mean: 10, p50: 10, p90: 15, p95: 20 },
      { month: 2, mean: 12, p50: 10, p90: 18, p95: 25 },
      { month: 3, mean: 20, p50: 20, p90: 30, p95: 40 },
      { month: 4, mean: 80, p50: 80, p90: 90, p95: 100 },
      { month: 5, mean: 100, p50: 100, p90: 120, p95: 140 },
      { month: 6, mean: 60, p50: 60, p90: 75, p95: 85 },
      { month: 7, mean: 10, p50: 10, p90: 15, p95: 20 },
      { month: 8, mean: 10, p50: 10, p90: 15, p95: 20 },
      { month: 9, mean: 10, p50: 10, p90: 15, p95: 20 },
      { month: 10, mean: 10, p50: 10, p90: 15, p95: 20 },
      { month: 11, mean: 10, p50: 10, p90: 15, p95: 20 },
      { month: 12, mean: 10, p50: 10, p90: 15, p95: 20 },
    ];

    render(<ClimatologyStrip climatology={climatology} />);
    expect(screen.getByTestId("climatology-strip")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument(); // Peak month mean
  });
});
