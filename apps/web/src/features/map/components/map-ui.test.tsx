import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { MapLegend } from "./legend";
import { MapControls } from "./map-controls";
import { HexTooltip } from "./hex-tooltip";
import { MetricToggle } from "./metric-toggle";
import { TimeRange } from "./time-range";

describe("Map UI Components", () => {
  it("renders MapLegend with unit labels and statistical markers", () => {
    const stats = {
      min: 0,
      p50: 18,
      p95: 42,
      max: 120,
      sum: 250,
      count: 10,
    };

    render(<MapLegend stats={stats} metric="harmonized" />);

    expect(screen.getByTestId("map-legend")).toBeInTheDocument();
    expect(
      screen.getByText("MODIS-equivalent fire events per cell")
    ).toBeInTheDocument();
    expect(screen.getByText("p95: 42")).toBeInTheDocument();
    expect(screen.getByText("Max: 120")).toBeInTheDocument();
  });

  it("renders MapLegend for raw metrics cleanly", () => {
    render(<MapLegend stats={null} metric="raw_viirs" />);

    expect(
      screen.getByText("Raw VIIRS hot spots per cell")
    ).toBeInTheDocument();
  });

  it("handles 2D/3D toggle and reset in MapControls", () => {
    const handleToggle3d = vi.fn();
    const handleReset = vi.fn();

    render(
      <MapControls
        is3d={true}
        onToggle3d={handleToggle3d}
        onResetView={handleReset}
        res={7}
        cellCount={500}
      />
    );

    const toggleBtn = screen.getByRole("button", { name: "3D Extruded" });
    fireEvent.click(toggleBtn);
    expect(handleToggle3d).toHaveBeenCalledTimes(1);

    const resetBtn = screen.getByRole("button", { name: "Reset View" });
    fireEvent.click(resetBtn);
    expect(handleReset).toHaveBeenCalledTimes(1);

    expect(screen.getByText("H3 r7")).toBeInTheDocument();
    expect(screen.getByText("500 cells")).toBeInTheDocument();
  });

  it("renders HexTooltip with cell metrics and FRP", () => {
    const cell = {
      h3: "87642825fffffff",
      value: 42,
      frp_mw: 150.5,
    };

    render(<HexTooltip cell={cell} x={100} y={150} metric="harmonized" />);

    expect(screen.getByTestId("hex-tooltip")).toBeInTheDocument();
    expect(screen.getByText("H3: 87642825fffffff")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("151 MW")).toBeInTheDocument();
  });

  it("handles MetricToggle changes", () => {
    const handleChange = vi.fn();
    render(<MetricToggle value="harmonized" onChange={handleChange} />);

    const viirsBtn = screen.getByText("Raw VIIRS");
    fireEvent.click(viirsBtn);
    expect(handleChange).toHaveBeenCalledWith("raw_viirs");
  });

  it("handles TimeRange month updates", () => {
    const handleChange = vi.fn();
    render(<TimeRange from="2020-01" to="2024-12" onChange={handleChange} />);

    const fromInput = screen.getByLabelText("Start month");
    fireEvent.change(fromInput, { target: { value: "2021-03" } });
    fireEvent.blur(fromInput);

    expect(handleChange).toHaveBeenCalledWith("2021-03", "2024-12");
  });
});
