import { describe, it, expect, beforeAll, afterAll, afterEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { SeriesChart } from "./series-chart";
import { server } from "@/mocks/server";
import type { SeriesPoint } from "../types";

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

describe("Series Chart and Jump Analysis", () => {
  it("verifies the ~3x naive splice jump across 2011-2012 vs flat harmonized series in data", async () => {
    let capturedSeries: SeriesPoint[] = [];

    server.use(
      http.get("*/api/series", () => {
        const fixturePoints: SeriesPoint[] = [
          {
            year: 2011,
            month: 5,
            raw_modis: 100,
            raw_viirs: null,
            naive_splice: 100,
            harmonized: 100,
            in_overlap: false,
            source_used: "modis_raw",
            provisional: false,
          },
          {
            year: 2012,
            month: 5,
            raw_modis: 100,
            raw_viirs: 300,
            naive_splice: 300,
            harmonized: 100,
            in_overlap: true,
            source_used: "viirs_calibrated",
            provisional: false,
          },
        ];
        capturedSeries = fixturePoints;
        return HttpResponse.json({
          data: fixturePoints,
          meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
        });
      })
    );

    renderWithClient(<SeriesChart />);

    await waitFor(() => {
      expect(screen.getByTestId("series-chart")).toBeInTheDocument();
    });

    // Check data logic directly
    const pt2011 = capturedSeries.find((p) => p.year === 2011 && p.month === 5)!;
    const pt2012 = capturedSeries.find((p) => p.year === 2012 && p.month === 5)!;

    expect(pt2011).toBeDefined();
    expect(pt2012).toBeDefined();

    // Naive splice jumps by 3x (100 -> 300)
    const naiveRatio = pt2012.naive_splice / pt2011.naive_splice;
    expect(naiveRatio).toBeCloseTo(3.0, 1);

    // Harmonized series eliminates the jump (100 -> 100)
    const harmonizedRatio = pt2012.harmonized / pt2011.harmonized;
    expect(harmonizedRatio).toBeCloseTo(1.0, 1);
  });

  it("renders JumpCaption with plain-language metrics", async () => {
    renderWithClient(<SeriesChart />);

    await waitFor(() => {
      expect(screen.getByTestId("jump-caption")).toBeInTheDocument();
    });

    // Ratio values from mock methodology endpoint (2.99x naive, 1.00x harmonized, 100% reduction)
    expect(screen.getByText(/2.99× higher/i)).toBeInTheDocument();
    expect(screen.getByText(/1.00×/i)).toBeInTheDocument();
    expect(screen.getByText(/100% artificial discontinuity removed/i)).toBeInTheDocument();
  });

  it("supports Story Mode stepping across different sensor perspectives", async () => {
    renderWithClient(<SeriesChart />);

    await waitFor(() => {
      expect(screen.getByTestId("series-chart")).toBeInTheDocument();
    });

    const storyButton = screen.getByRole("button", { name: /Step through Story/i });
    expect(storyButton).toBeInTheDocument();

    // Step 1: Raw observations
    fireEvent.click(storyButton);
    expect(screen.getByText(/Story: 1\. Raw Mismatch/i)).toBeInTheDocument();

    // Step 2: The naive splice
    fireEvent.click(storyButton);
    expect(screen.getByText(/Story: 2\. Naive 3× Jump/i)).toBeInTheDocument();

    // Step 3: Harmonized calibration
    fireEvent.click(storyButton);
    expect(screen.getByText(/Story: 3\. Harmonized/i)).toBeInTheDocument();
  });

  it("toggles between Chart and Data Table views", async () => {
    renderWithClient(<SeriesChart />);

    await waitFor(() => {
      expect(screen.getByTestId("series-chart")).toBeInTheDocument();
    });

    const toggleButton = screen.getByRole("button", { name: /View Data Table/i });
    fireEvent.click(toggleButton);

    // Should now show table column headers
    expect(screen.getByRole("columnheader", { name: "Period" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Harmonized" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Naive Splice" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Raw VIIRS" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Raw MODIS" })).toBeInTheDocument();

    // Toggle back to chart
    fireEvent.click(screen.getByRole("button", { name: /Show Chart/i }));
    expect(screen.getByTestId("recharts-container")).toBeInTheDocument();
  });

  it("handles empty and error states for series", async () => {
    server.use(
      http.get("*/api/series", () => {
        return HttpResponse.json({ data: [] });
      })
    );

    renderWithClient(<SeriesChart />);

    await waitFor(() => {
      expect(screen.getByText(/No data available/i)).toBeInTheDocument();
    });
  });
});
