import { describe, it, expect, beforeAll, afterAll, afterEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { QQChart } from "./qq-chart";
import { JumpMetrics } from "./jump-metrics";
import { Limitations } from "./limitations";
import MethodologyPage from "@/app/methodology/page";
import { server } from "@/mocks/server";
import type { JumpMetricsType } from "../index";

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

describe("Methodology Page & Feature Components", () => {
  it("renders the complete methodology page with all sections loaded from API", async () => {
    renderWithClient(<MethodologyPage />);

    // Wait for data loading
    await waitFor(() => {
      expect(screen.getByTestId("method-steps")).toBeInTheDocument();
    });

    // Check header
    expect(
      screen.getByText("Harmonization of MODIS and VIIRS Hot Spots")
    ).toBeInTheDocument();

    // Check Step-by-Step Flow
    expect(screen.getByText("FIRMS Satellite Ingest")).toBeInTheDocument();
    expect(screen.getByText("ST-DBSCAN Fire Events")).toBeInTheDocument();
    expect(screen.getByText("H3 Hexagonal Indexing")).toBeInTheDocument();
    expect(screen.getByText("Quantile-Mapping Calibration")).toBeInTheDocument();
    expect(screen.getByText("Burning Activity Calendar")).toBeInTheDocument();

    // Check Jump Metrics
    expect(screen.getByTestId("jump-metrics")).toBeInTheDocument();
    expect(screen.getByText("2.99×")).toBeInTheDocument();
    expect(screen.getByText("1.00×")).toBeInTheDocument();
    expect(
      screen.getByText(/These metrics describe the empirical relationship in the data/i)
    ).toBeInTheDocument();

    // Check Validation Summary
    expect(screen.getByTestId("validation-summary")).toBeInTheDocument();
    expect(screen.getByText("4.20")).toBeInTheDocument();
    expect(screen.getByText("-0.10")).toBeInTheDocument();
    expect(screen.getByText("0.97")).toBeInTheDocument();

    // Check Q-Q Chart
    expect(screen.getByTestId("qq-chart")).toBeInTheDocument();

    // Check Parameters Table
    expect(screen.getByTestId("parameters-table")).toBeInTheDocument();
    expect(screen.getByText("confidence_filter")).toBeInTheDocument();

    // Check Sources List
    expect(screen.getByTestId("sources-list")).toBeInTheDocument();
    expect(screen.getByText("NASA FIRMS Active Fire Data")).toBeInTheDocument();

    // Check Limitations
    expect(screen.getByTestId("limitations")).toBeInTheDocument();
    expect(
      screen.getByText(/Active-fire counts are not burned area/i)
    ).toBeInTheDocument();
  });

  it("toggles between Chart and accessible Data Table in QQChart", () => {
    render(<QQChart />);

    expect(screen.getByTestId("recharts-qq-container")).toBeInTheDocument();

    const tableToggle = screen.getByRole("button", { name: "View Data Table" });
    fireEvent.click(tableToggle);

    // Chart container is hidden, data table is shown
    expect(screen.queryByTestId("recharts-qq-container")).not.toBeInTheDocument();
    expect(screen.getByText("Percentile")).toBeInTheDocument();
    expect(screen.getByText("MODIS Reference")).toBeInTheDocument();
    expect(screen.getByText("Raw VIIRS")).toBeInTheDocument();
    expect(screen.getByText("Harmonized VIIRS")).toBeInTheDocument();
    expect(screen.getByText("Residual Bias")).toBeInTheDocument();

    // Toggle back to chart
    fireEvent.click(screen.getByRole("button", { name: "Show Chart" }));
    expect(screen.getByTestId("recharts-qq-container")).toBeInTheDocument();
  });

  it("guarantees limitations are always rendered even if input list is empty or undefined", () => {
    const { rerender } = render(<Limitations limitations={[]} />);
    expect(screen.getByTestId("limitations")).toBeInTheDocument();
    expect(
      screen.getByText(/Active-fire counts are not burned area/i)
    ).toBeInTheDocument();

    rerender(<Limitations limitations={undefined} />);
    expect(screen.getByTestId("limitations")).toBeInTheDocument();
    expect(
      screen.getByText(/The calibration assumes the MODIS-VIIRS relationship/i)
    ).toBeInTheDocument();
  });

  it("omits JumpMetrics when metrics are missing or undefined", () => {
    const { container: emptyContainer } = render(<JumpMetrics metrics={null} />);
    expect(emptyContainer.firstChild).toBeNull();

    const { container: partialContainer } = render(
      <JumpMetrics metrics={{ naive_ratio: 3.0 } as unknown as JumpMetricsType} />
    );
    expect(partialContainer.firstChild).toBeNull();
  });
});
