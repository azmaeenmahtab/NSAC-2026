import React from "react";
import { describe, it, expect, beforeAll, afterAll, afterEach, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { server } from "@/mocks/server";
import { NearbyStationsPanel } from "./nearby-stations-panel";
import { buildMailtoHref, buildTelHref } from "../lib/contact-links";

beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  vi.restoreAllMocks();
});
afterAll(() => server.close());

describe("Nearby Fire Stations Feature (stations)", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
  });

  function renderPanel(areaId = "PRESET-CHT") {
    return render(
      <QueryClientProvider client={queryClient}>
        <NearbyStationsPanel areaId={areaId} />
      </QueryClientProvider>
    );
  }

  it("formats tel: and mailto: links safely", () => {
    expect(buildTelHref("102")).toBe("tel:102");
    expect(buildTelHref("+880 1730-336699")).toBe("tel:+8801730336699");

    const mailto = buildMailtoHref(
      null,
      "[HIGH Risk] Fire Alert Report",
      "Hello Station,\nPlease check."
    );
    expect(mailto).toContain("mailto:?");
    expect(mailto).toContain("subject=%5BHIGH%20Risk%5D%20Fire%20Alert%20Report");
    expect(mailto).toContain("body=Hello%20Station");
  });

  it("renders nearby stations, risk badge, direct dial, and one-click email links", async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByTestId("threat-level-badge")).toHaveTextContent("HIGH RISK");
    });

    const cards = screen.getAllByTestId("station-card");
    expect(cards).toHaveLength(2);
    expect(screen.getByText(/Rangamati Fire Service/i)).toBeInTheDocument();

    const callLinks = screen.getAllByRole("link", { name: /Call 102/i });
    expect(callLinks[0]).toHaveAttribute("href", "tel:102");

    const emergencyLinks = screen.getAllByRole("link", { name: /Emergency 999/i });
    expect(emergencyLinks[0]).toHaveAttribute("href", "tel:999");

    const emailLinks = screen.getAllByRole("link", { name: /Email Report/i });
    expect(emailLinks[0].getAttribute("href")).toContain("mailto:");
    expect(emailLinks[0].getAttribute("href")).toContain("HIGH%20Risk");
  });

  it("handles browser geolocation denial gracefully", () => {
    Object.defineProperty(navigator, "geolocation", {
      configurable: true,
      value: {
        getCurrentPosition: (_ok: PositionCallback, err: PositionErrorCallback) => {
          err({ code: 1, message: "Denied" } as GeolocationPositionError);
        },
      },
    });

    renderPanel();
    fireEvent.click(screen.getByRole("button", { name: /Use My Location/i }));
    expect(screen.getByRole("status")).toHaveTextContent(/permission denied/i);
  });
});

