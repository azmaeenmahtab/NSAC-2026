import { describe, it, expect, vi, beforeAll, afterAll, afterEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AreaSelector } from "./area-selector";
import { AreaBreadcrumb } from "./area-breadcrumb";
import { BBoxDraw } from "./bbox-draw";
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

describe("Area Selection UI Components", () => {
  it("renders AreaSelector with groups and handles search filtering", async () => {
    const handleSelect = vi.fn();
    renderWithClient(
      <AreaSelector selectedId="PRESET-CHT" onSelect={handleSelect} />
    );

    // Wait for mock areas to load
    await waitFor(() => {
      expect(screen.getByText("Chittagong Hill Tracts")).toBeInTheDocument();
    });

    expect(screen.getByText("Bangladesh")).toBeInTheDocument();
    expect(screen.getByText("Alpha District")).toBeInTheDocument();

    // Type into search filter
    const input = screen.getByLabelText("Filter areas");
    fireEvent.change(input, { target: { value: "alpha" } });

    expect(screen.getByText("Alpha District")).toBeInTheDocument();
    expect(screen.queryByText("Bangladesh")).not.toBeInTheDocument();

    // Click on Alpha District
    fireEvent.click(screen.getByText("Alpha District"));
    expect(handleSelect).toHaveBeenCalledWith("BGD-ADM2-alpha");
  });

  it("renders AreaBreadcrumb for presets and hierarchical areas", async () => {
    const handleAreaChange = vi.fn();
    renderWithClient(
      <AreaBreadcrumb
        currentAreaId="PRESET-CHT"
        onAreaChange={handleAreaChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Chittagong Hill Tracts")).toBeInTheDocument();
    });
    expect(screen.getByText("National")).toBeInTheDocument();

    fireEvent.click(screen.getByText("National"));
    expect(handleAreaChange).toHaveBeenCalledWith("BGD");
  });

  it("renders AreaBreadcrumb for custom bounding box", () => {
    renderWithClient(
      <AreaBreadcrumb currentAreaId="bbox:88.1,21.5,92.6,26.4" />
    );

    expect(
      screen.getByText(/BBox \[88.1°E, 21.5°N to 92.6°E, 26.4°N\]/)
    ).toBeInTheDocument();
  });

  it("validates coordinates in BBoxDraw and surfaces errors", () => {
    const handleSelectBBox = vi.fn();
    const handleClear = vi.fn();

    render(
      <BBoxDraw
        currentAreaId="PRESET-CHT"
        onSelectBBox={handleSelectBBox}
        onClear={handleClear}
      />
    );

    // Apply with reversed west/east: west = 95, east = 90
    const westInput = screen.getByLabelText(/West/i);
    const eastInput = screen.getByLabelText(/East/i);

    fireEvent.change(westInput, { target: { value: "95.0" } });
    fireEvent.change(eastInput, { target: { value: "90.0" } });

    fireEvent.click(screen.getByRole("button", { name: /Apply Bounding Box/i }));

    expect(
      screen.getByText(/West longitude must be strictly less than East longitude/i)
    ).toBeInTheDocument();
    expect(handleSelectBBox).not.toHaveBeenCalled();
  });
});
