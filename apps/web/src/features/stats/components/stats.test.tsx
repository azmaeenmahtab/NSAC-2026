import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { RankBadge } from "./rank-badge";
import { YearlyTable } from "./yearly-table";
import { YearlyBars } from "./yearly-bars";
import type { YearlyStatRow } from "../types";

const MOCK_ROWS: YearlyStatRow[] = [
  {
    year: 2020,
    harmonized_total: 185.0,
    frp_sum: 540.2,
    rank: 3,
    vs_mean_pct: 12.5,
    peak_month: 3,
  },
  {
    year: 2021,
    harmonized_total: 210.0,
    frp_sum: 620.0,
    rank: 1,
    vs_mean_pct: 27.8,
    peak_month: 3,
  },
  {
    year: 2022,
    harmonized_total: 145.0,
    frp_sum: 410.5,
    rank: 5,
    vs_mean_pct: -11.9,
    peak_month: 4,
  },
];

describe("Yearly Stats UI Components (stats)", () => {
  describe("RankBadge", () => {
    it("renders distinct highlight badge for rank #1", () => {
      render(<RankBadge rank={1} />);
      const badge = screen.getByTestId("rank-badge");
      expect(badge.textContent).toContain("#1 Peak");
      expect(badge.className).toContain("text-[#ef4444]");
    });

    it("renders appropriate badges for rank 2, 3 and lower ranks", () => {
      const { rerender } = render(<RankBadge rank={2} />);
      expect(screen.getByTestId("rank-badge").textContent).toBe("#2");

      rerender(<RankBadge rank={3} />);
      expect(screen.getByTestId("rank-badge").textContent).toBe("#3");

      rerender(<RankBadge rank={8} />);
      expect(screen.getByTestId("rank-badge").textContent).toBe("#8");
    });
  });

  describe("YearlyTable", () => {
    it("renders rows with formatted units, FRP and peak month", () => {
      render(<YearlyTable data={MOCK_ROWS} />);
      expect(screen.getByText("2020")).toBeInTheDocument();
      expect(screen.getByText("2021")).toBeInTheDocument();
      expect(screen.getByText("2022")).toBeInTheDocument();
      expect(screen.getByText("185")).toBeInTheDocument();
      expect(screen.getByText("540.2")).toBeInTheDocument();
      expect(screen.getAllByText("March").length).toBeGreaterThan(0);
      expect(screen.getByText("April")).toBeInTheDocument();
      expect(screen.getByText("+12.5%")).toBeInTheDocument();
      expect(screen.getByText("-11.9%")).toBeInTheDocument();
    });

    it("handles column sorting correctly", () => {
      render(<YearlyTable data={MOCK_ROWS} />);
      const rankHeader = screen.getByRole("button", { name: /Rank/i });

      // Click to sort by rank ascending
      fireEvent.click(rankHeader);
      let cells = screen.getAllByTestId("rank-badge");
      expect(cells[0].textContent).toContain("#1 Peak");

      // Click again to sort descending
      fireEvent.click(rankHeader);
      cells = screen.getAllByTestId("rank-badge");
      expect(cells[0].textContent).toBe("#5");
    });

    it("invokes onSelectYear when a row is clicked", () => {
      const onSelect = vi.fn();
      render(<YearlyTable data={MOCK_ROWS} onSelectYear={onSelect} />);
      const rowYear = screen.getByText("2021");
      fireEvent.click(rowYear);
      expect(onSelect).toHaveBeenCalledWith(2021);
    });
  });

  describe("YearlyBars", () => {
    it("renders chart and toggles accessible data table", () => {
      render(<YearlyBars data={MOCK_ROWS} selectedYear={2021} />);
      expect(
        screen.getByText("Annual Burning Totals (2000–Present)")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/MODIS-equivalent fire events/i)
      ).toBeInTheDocument();

      const toggleBtn = screen.getByRole("button", {
        name: /Show accessible table/i,
      });
      fireEvent.click(toggleBtn);

      expect(
        screen.getByRole("button", { name: /Hide accessible table/i })
      ).toBeInTheDocument();
      expect(screen.getByRole("table")).toBeInTheDocument();
    });
  });
});

