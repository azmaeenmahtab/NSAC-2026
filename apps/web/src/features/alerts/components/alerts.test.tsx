import React from "react";
import { describe, it, expect, vi, beforeAll, afterAll, afterEach, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { server } from "@/mocks/server";
import { AlertBanner } from "./alert-banner";
import { AlertStateCard } from "./alert-state-card";
import { SubscribeForm } from "./subscribe-form";
import { SubscriptionConfirm } from "./subscription-confirm";
import type { ActiveAlerts } from "../types";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("Alerts Feature Components (alerts)", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  function renderWithQuery(ui: React.ReactElement) {
    return render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    );
  }

  describe("AlertBanner", () => {
    const activeAlertData: ActiveAlerts = {
      season_approaching: true,
      above_normal: true,
      current_month_class: "elevated",
      days_until_season: 14,
      reason: "Dry transitional weather detected.",
      provisional_as_of: "2026-10-31",
    };

    it("renders banner when season is approaching or above normal", () => {
      render(
        <AlertBanner
          areaId="PRESET-CHT"
          areaName="Chittagong Hill Tracts"
          alerts={activeAlertData}
        />
      );

      const banner = screen.getByTestId("alert-banner");
      expect(banner).toBeInTheDocument();
      expect(screen.getByText(/Fire Season Approaching/i)).toBeInTheDocument();
      expect(screen.getByText(/Chittagong Hill Tracts/i)).toBeInTheDocument();
      expect(screen.getByText(/14 days until historical season onset/i)).toBeInTheDocument();
      expect(screen.getByText(/provisional data as of 2026-10-31/i)).toBeInTheDocument();
    });

    it("does not render when conditions are normal and season is not approaching", () => {
      const quietAlertData: ActiveAlerts = {
        season_approaching: false,
        above_normal: false,
        current_month_class: "normal",
        days_until_season: null,
      };

      const { container } = render(
        <AlertBanner
          areaId="BGD"
          alerts={quietAlertData}
        />
      );

      expect(container.firstChild).toBeNull();
    });

    it("dismisses banner when close button is clicked", () => {
      render(
        <AlertBanner
          areaId="PRESET-CHT"
          alerts={activeAlertData}
        />
      );

      const closeBtn = screen.getByLabelText(/Dismiss alert banner/i);
      fireEvent.click(closeBtn);

      expect(screen.queryByTestId("alert-banner")).toBeNull();
    });
  });

  describe("AlertStateCard", () => {
    it("renders telemetry details and handles subscribe click", () => {
      const onSubscribe = vi.fn();
      const alertData: ActiveAlerts = {
        season_approaching: true,
        above_normal: false,
        current_month_class: "elevated",
        days_until_season: 10,
      };

      render(
        <AlertStateCard
          areaId="PRESET-CHT"
          areaName="Chittagong Hill Tracts"
          alerts={alertData}
          onSubscribeClick={onSubscribe}
        />
      );

      expect(screen.getByText("Early Warning Telemetry")).toBeInTheDocument();
      expect(screen.getByText("Active Advisory")).toBeInTheDocument();
      expect(screen.getByText("Approaching")).toBeInTheDocument();
      expect(screen.getByText("~10 days away")).toBeInTheDocument();

      const btn = screen.getByRole("button", { name: /Subscribe to Area Warnings/i });
      fireEvent.click(btn);
      expect(onSubscribe).toHaveBeenCalled();
    });
  });

  describe("SubscribeForm", () => {
    it("validates email and consent before submission", async () => {
      renderWithQuery(<SubscribeForm areaId="PRESET-CHT" />);

      const form = screen.getByTestId("subscribe-form");
      fireEvent.submit(form);

      // Expect validation error
      expect(await screen.findByRole("alert")).toHaveTextContent(
        /Please provide a valid email address/i
      );
    });

    it("submits valid subscription and displays confirmation message", async () => {
      renderWithQuery(<SubscribeForm areaId="PRESET-CHT" areaName="Chittagong Hill Tracts" />);

      const emailInput = screen.getByLabelText(/Email Address/i);
      fireEvent.change(emailInput, { target: { value: "test@forester.org" } });

      const consentCheck = screen.getByRole("checkbox");
      fireEvent.click(consentCheck);

      const submitBtn = screen.getByRole("button", { name: /Subscribe to Alerts/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(screen.getByTestId("subscribe-success")).toBeInTheDocument();
        expect(screen.getByText("Check your email")).toBeInTheDocument();
      });
    });

    it("handles 429 rate limit error gracefully", async () => {
      renderWithQuery(<SubscribeForm areaId="PRESET-CHT" />);

      const emailInput = screen.getByLabelText(/Email Address/i);
      fireEvent.change(emailInput, { target: { value: "rate429@forester.org" } });

      const consentCheck = screen.getByRole("checkbox");
      fireEvent.click(consentCheck);

      const submitBtn = screen.getByRole("button", { name: /Subscribe to Alerts/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(
          /maximum 5 requests per hour/i
        );
      });
    });
  });

  describe("SubscriptionConfirm", () => {
    it("confirms subscription when a valid token is provided", async () => {
      render(<SubscriptionConfirm token="valid-secret-token" />);

      await waitFor(() => {
        expect(screen.getByText("Subscription Confirmed")).toBeInTheDocument();
        expect(screen.getByText(/Your alert subscription is now active/i)).toBeInTheDocument();
      });
    });

    it("shows error when token is expired or invalid", async () => {
      render(<SubscriptionConfirm token="expired" />);

      await waitFor(() => {
        expect(screen.getByText("Confirmation Failed")).toBeInTheDocument();
        expect(screen.getByText(/expired or is invalid/i)).toBeInTheDocument();
      });
    });

    it("shows error when no token is provided", async () => {
      render(<SubscriptionConfirm token={null} />);

      await waitFor(() => {
        expect(screen.getByText("Confirmation Failed")).toBeInTheDocument();
        expect(screen.getByText(/No confirmation token was provided/i)).toBeInTheDocument();
      });
    });
  });
});
