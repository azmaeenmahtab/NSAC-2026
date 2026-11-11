import { describe, it, expect } from "vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import { DataStatusBadge } from "./data-status-badge";

describe("DataStatusBadge", () => {
  it("renders data version and as-of date cleanly", () => {
    render(<DataStatusBadge dataVersion="v1.0.0" asOf="2026-10-31" />);

    expect(screen.getByText("v1.0.0")).toBeInTheDocument();
    expect(screen.getByText("As of 2026-10-31")).toBeInTheDocument();
    expect(screen.queryByTestId("provisional-badge")).not.toBeInTheDocument();
  });

  it("renders provisional badge when provisionalFrom is present", () => {
    render(
      <DataStatusBadge
        dataVersion="v1.0.0"
        asOf="2026-10-31"
        provisionalFrom="2026-06-01"
      />
    );

    expect(screen.getByTestId("provisional-badge")).toBeInTheDocument();
    expect(screen.getByText("Provisional data included")).toBeInTheDocument();
  });

  it("does not render provisional badge when provisionalFrom is null or undefined", () => {
    const { rerender } = render(
      <DataStatusBadge dataVersion="v1.0.0" provisionalFrom={null} />
    );
    expect(screen.queryByTestId("provisional-badge")).not.toBeInTheDocument();

    rerender(<DataStatusBadge dataVersion="v1.0.0" provisionalFrom={undefined} />);
    expect(screen.queryByTestId("provisional-badge")).not.toBeInTheDocument();
  });
});
