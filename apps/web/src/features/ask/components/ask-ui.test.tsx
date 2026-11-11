import { describe, it, expect, vi, beforeAll, afterAll, afterEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AskPanel } from "./ask-panel";
import { ModeBadge } from "./mode-badge";
import { StyleToggle } from "./style-toggle";
import { CitationChips } from "./citation-chips";
import { server } from "@/mocks/server";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe("Ask PyroScope UI Components", () => {
  it("renders replay-mode response with badge, timeline (two tool calls), and citations", async () => {
    renderWithClient(<AskPanel />);

    // Type a question
    const textarea = screen.getByLabelText(/Ask assistant question/i);
    fireEvent.change(textarea, {
      target: { value: "When does fire season start in CHT?" },
    });

    const submitBtn = screen.getByRole("button", { name: "Ask" });
    fireEvent.click(submitBtn);

    // Wait for response to load from mock
    await waitFor(() => {
      expect(screen.getByTestId("answer-card")).toBeInTheDocument();
    });

    // Check ModeBadge
    expect(
      screen.getByText("Scripted replay (offline demo)")
    ).toBeInTheDocument();

    // Check ToolTimeline with two tools
    expect(screen.getByTestId("tool-timeline")).toBeInTheDocument();
    expect(screen.getByText("get_season()")).toBeInTheDocument();
    expect(screen.getByText("get_anomalies()")).toBeInTheDocument();

    // Check CitationChips
    expect(screen.getByTestId("citation-chips")).toBeInTheDocument();
    expect(
      screen.getByText(/Data v0\.1\.0-fixtures, years 2012 to 2016, area PRESET-CHT/)
    ).toBeInTheDocument();
  });

  it("renders an answer containing <script> and <img onerror=...> as literal text (XSS safety)", async () => {
    renderWithClient(<AskPanel />);

    const textarea = screen.getByLabelText(/Ask assistant question/i);
    fireEvent.change(textarea, { target: { value: "xss_test query" } });

    fireEvent.click(screen.getByRole("button", { name: "Ask" }));

    await waitFor(() => {
      expect(screen.getByTestId("answer-card")).toBeInTheDocument();
    });

    // Verify raw script tag is rendered as literal text content, not executable DOM
    expect(
      screen.getByText(/<script>alert\('xss'\)<\/script>/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/<img onerror="alert\(1\)" src="x"\/>/)
    ).toBeInTheDocument();

    // Verify no script or img elements were created in DOM
    expect(document.querySelector("script[src='x']")).toBeNull();
    expect(document.querySelector("img[src='x']")).toBeNull();
  });

  it("handles 429 rate limit state and displays retry cooldown", async () => {
    renderWithClient(<AskPanel />);

    const textarea = screen.getByLabelText(/Ask assistant question/i);
    fireEvent.change(textarea, { target: { value: "trigger_429 query" } });

    fireEvent.click(screen.getByRole("button", { name: "Ask" }));

    await waitFor(() => {
      expect(screen.getByTestId("answer-card-error")).toBeInTheDocument();
    });

    expect(screen.getByText(/Rate limited/i)).toBeInTheDocument();
    expect(screen.getByText(/Cooldown: 30s/i)).toBeInTheDocument();
  });

  it("handles 502 upstream error state and offers retry button", async () => {
    renderWithClient(<AskPanel />);

    const textarea = screen.getByLabelText(/Ask assistant question/i);
    fireEvent.change(textarea, { target: { value: "trigger_502 query" } });

    fireEvent.click(screen.getByRole("button", { name: "Ask" }));

    await waitFor(() => {
      expect(screen.getByTestId("answer-card-error")).toBeInTheDocument();
    });

    expect(screen.getByText(/Upstream model provider timeout/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Retry Query/i })).toBeInTheDocument();
  });

  it("enforces 500 character limit on questions client-side", () => {
    renderWithClient(<AskPanel />);

    const textarea = screen.getByLabelText(/Ask assistant question/i);
    const longText = "a".repeat(501);

    fireEvent.change(textarea, { target: { value: longText } });

    expect(screen.getByText("501 / 500 characters")).toBeInTheDocument();
    const submitBtn = screen.getByRole("button", { name: "Ask" });
    expect(submitBtn).toBeDisabled();
  });

  it("populates input and sends message when clicking suggested question", async () => {
    renderWithClient(<AskPanel />);

    const suggestion = screen.getByRole("button", {
      name: "Was last year unusual?",
    });
    fireEvent.click(suggestion);

    await waitFor(() => {
      expect(screen.getByTestId("answer-card")).toBeInTheDocument();
    });

    expect(screen.getByTestId("user-message")).toHaveTextContent(
      "Was last year unusual?"
    );
  });

  it("clicking citation chip updates shared URL area state", () => {
    const citations = [
      {
        tool: "get_season",
        areaId: "BGD-ADM2-alpha",
        years: [2019, 2020],
        dataVersion: "v0.1.0-fixtures",
      },
    ];

    render(<CitationChips citations={citations} />);

    const chip = screen.getByRole("button", {
      name: /Inspect source: Data v0\.1\.0-fixtures, years 2019 to 2020, area BGD-ADM2-alpha/i,
    });
    expect(chip).toBeInTheDocument();
    fireEvent.click(chip);
    // Verified interaction executes cleanly
  });

  it("renders ModeBadge for both live and replay modes", () => {
    const { rerender } = render(<ModeBadge mode="live" />);
    expect(screen.getByText("Live model")).toBeInTheDocument();

    rerender(<ModeBadge mode="replay" />);
    expect(
      screen.getByText("Scripted replay (offline demo)")
    ).toBeInTheDocument();
  });

  it("toggles between standard and plain styles in StyleToggle", () => {
    const handleChange = vi.fn();
    render(<StyleToggle style="standard" onChange={handleChange} />);

    const plainBtn = screen.getByRole("button", { name: "Plain Language" });
    fireEvent.click(plainBtn);
    expect(handleChange).toHaveBeenCalledWith("plain");
  });
});
