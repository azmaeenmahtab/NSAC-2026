import React from "react";
import { describe, it, expect, vi, beforeAll, afterAll, afterEach, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { server } from "@/mocks/server";
import { StageBadge } from "./stage-badge";
import { GuidanceDisclaimer } from "./guidance-disclaimer";
import { Checklist } from "./checklist";
import { ActionPlanner } from "./action-planner";
import type { GuidanceItem } from "../types";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const MOCK_ITEMS: GuidanceItem[] = [
  {
    id: "g-01",
    stage: "in_season",
    audience: "community",
    text: "Clear 10m defensible space around residential perimeters.",
    source_title: "Forest Guidelines",
    source_url: "https://example.com/guide",
    verified: true,
  },
  {
    id: "g-02",
    stage: "in_season",
    audience: "responder",
    text: "Pre-stage rapid response water tenders in high-risk H3 clusters.",
    source_title: "Beat SOP",
    source_url: "https://example.com/sop",
    verified: false,
  },
];

describe("Guidance and Wildland Action Planner Components (guidance)", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
  });

  function renderWithQuery(ui: React.ReactElement) {
    return render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    );
  }

  describe("StageBadge", () => {
    it("renders stage badges with descriptive labels", () => {
      const { rerender } = render(<StageBadge stage="pre_season" />);
      expect(screen.getByTestId("stage-badge").textContent).toContain("Pre-Season Readiness");

      rerender(<StageBadge stage="in_season" />);
      expect(screen.getByTestId("stage-badge").textContent).toContain("In Season Active");

      rerender(<StageBadge stage="extreme" />);
      expect(screen.getByTestId("stage-badge").textContent).toContain("Extreme Fire Threat");

      rerender(<StageBadge stage="post_season" />);
      expect(screen.getByTestId("stage-badge").textContent).toContain("Post-Season Recovery");
    });
  });

  describe("GuidanceDisclaimer", () => {
    it("renders the advisory disclaimer warning", () => {
      render(<GuidanceDisclaimer />);
      expect(
        screen.getByText(/Alerts, fire season stages, and action guidance are advisory/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/In emergency situations, always defer to official/i)
      ).toBeInTheDocument();
    });
  });

  describe("Checklist", () => {
    it("renders items with source links and verified tags", () => {
      render(<Checklist items={MOCK_ITEMS} />);

      expect(
        screen.getByText("Clear 10m defensible space around residential perimeters.")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Pre-stage rapid response water tenders in high-risk H3 clusters.")
      ).toBeInTheDocument();

      const sourceLink = screen.getByRole("link", { name: /Source: Forest Guidelines/i });
      expect(sourceLink).toHaveAttribute("href", "https://example.com/guide");
      expect(sourceLink).toHaveAttribute("target", "_blank");
      expect(sourceLink).toHaveAttribute("rel", "noopener noreferrer");

      // Verify "not yet verified" label on unverified items
      const unverified = screen.getByTestId("unverified-label");
      expect(unverified).toBeInTheDocument();
      expect(unverified.textContent).toBe("not yet verified");
    });

    it("allows interactive checkbox toggling", () => {
      render(<Checklist items={MOCK_ITEMS} />);
      const checkbox = screen.getByRole("checkbox", {
        name: /Mark task completed: Clear 10m defensible space/i,
      });

      expect(checkbox).not.toBeChecked();
      fireEvent.click(checkbox);
      expect(checkbox).toBeChecked();

      fireEvent.click(checkbox);
      expect(checkbox).not.toBeChecked();
    });
  });

  describe("ActionPlanner", () => {
    it("renders planner with audience filter tabs, print button, and disclaimer", async () => {
      const printSpy = vi.spyOn(window, "print").mockImplementation(() => {});

      renderWithQuery(
        <ActionPlanner areaId="PRESET-CHT" areaName="Chittagong Hill Tracts" month={3} stage="in_season" />
      );

      expect(screen.getByText("Wildland Action Planner")).toBeInTheDocument();
      expect(screen.getByText("In Season Active")).toBeInTheDocument();
      expect(screen.getByText("March")).toBeInTheDocument();
      expect(screen.getByText(/in Chittagong Hill Tracts/i)).toBeInTheDocument();

      // Check disclaimer is present
      expect(
        screen.getByText(/Alerts, fire season stages, and action guidance are advisory/i)
      ).toBeInTheDocument();

      // Check audience filtering
      await waitFor(() => {
        expect(
          screen.getByText(/Clear 10m defensible space around residential perimeters/i)
        ).toBeInTheDocument();
      });

      const respondersTab = screen.getByRole("button", { name: "Responders" });
      fireEvent.click(respondersTab);

      expect(
        screen.getByText("Pre-stage rapid response water tenders in high-risk H3 clusters.")
      ).toBeInTheDocument();

      // Test print button
      const printBtn = screen.getByRole("button", { name: /Printable Checklist/i });
      fireEvent.click(printBtn);
      expect(printSpy).toHaveBeenCalled();
    });
  });
});
