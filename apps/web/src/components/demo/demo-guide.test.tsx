import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DemoGuide } from "./demo-guide";
import { Attribution } from "@/components/layout/attribution";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockSetArea = vi.fn();

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("demo=1"),
  usePathname: () => "/",
}));

vi.mock("@/features/areas", () => ({
  useViewState: () => ({
    area: "PRESET-CHT",
    setArea: mockSetArea,
  }),
}));

describe("Polish, Accessibility & Demo Guide Components (F09)", () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  describe("DemoGuide", () => {
    it("renders and steps through the 4 pitch steps with demo=1", () => {
      const onSelectView = vi.fn();
      render(<DemoGuide onSelectView={onSelectView} />);

      // Should automatically open when demo=1
      expect(screen.getByTestId("demo-guide-card")).toBeInTheDocument();
      expect(screen.getByText("PyroScope Pitch Guide")).toBeInTheDocument();
      expect(screen.getByText("Step 1/4")).toBeInTheDocument();
      expect(screen.getByText("1. Spatial Hex Density (Map)")).toBeInTheDocument();

      // Test next button
      const nextBtn = screen.getByLabelText("Next pitch step");
      fireEvent.click(nextBtn);

      expect(screen.getByText("Step 2/4")).toBeInTheDocument();
      expect(screen.getByText("2. The Hidden Jump (2012)")).toBeInTheDocument();

      // Test action button
      const actionBtn = screen.getByRole("button", { name: /Compare 3× Jump/i });
      fireEvent.click(actionBtn);
      expect(onSelectView).toHaveBeenCalledWith("series");

      // Step to step 3 and 4
      fireEvent.click(nextBtn);
      expect(screen.getByText("Step 3/4")).toBeInTheDocument();
      fireEvent.click(nextBtn);
      expect(screen.getByText("Step 4/4")).toBeInTheDocument();

      // Test minimize
      const closeBtn = screen.getByLabelText("Minimize pitch guide");
      fireEvent.click(closeBtn);
      expect(screen.getByText("Presentation Guide")).toBeInTheDocument();
    });
  });

  describe("Attribution Safety Dialog", () => {
    it("opens and closes the operational safety disclaimer dialog", () => {
      render(
        <QueryClientProvider client={queryClient}>
          <Attribution />
        </QueryClientProvider>
      );

      const safetyBtn = screen.getByRole("button", { name: "Safety Notice" });
      fireEvent.click(safetyBtn);

      const dialog = screen.getByRole("dialog");
      expect(dialog).toBeInTheDocument();
      expect(screen.getByText(/Operational Safety & Scientific Research Notice/i)).toBeInTheDocument();
      expect(screen.getByText(/tactical fire dispatch system/i)).toBeInTheDocument();
      expect(screen.getByText(/Bangladesh Fire Service and Civil Defence/i)).toBeInTheDocument();

      const ackBtn = screen.getByRole("button", { name: "Acknowledge & Close" });
      fireEvent.click(ackBtn);
      expect(screen.queryByRole("dialog")).toBeNull();
    });
  });
});
