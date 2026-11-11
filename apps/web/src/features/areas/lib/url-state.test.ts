import { describe, it, expect } from "vitest";
import {
  parseViewState,
  serializeViewState,
  DEFAULT_VIEW_STATE,
} from "./url-state";
import type { ViewState } from "../types";

describe("URL State Handling (url-state.ts)", () => {
  it("preserves valid state across serialization and parsing (round-trip identity)", () => {
    const statesToTest: ViewState[] = [
      {
        area: "PRESET-CHT",
        from: "2020-01",
        to: "2025-12",
        metric: "harmonized",
        cell: null,
      },
      {
        area: "BGD-ADM2-rangamati",
        from: "2019-03",
        to: "2024-05",
        metric: "raw_viirs",
        cell: "87642825fffffff",
      },
      {
        area: "bbox:88.1,21.5,92.6,26.4",
        from: "2015-01",
        to: "2021-12",
        metric: "raw_modis",
        cell: null,
      },
    ];

    for (const original of statesToTest) {
      const searchParams = serializeViewState(original);
      const parsed = parseViewState(searchParams);
      expect(parsed).toEqual(original);
    }
  });

  it("replaces invalid area id with default area", () => {
    const params = new URLSearchParams("area=invalid!slug&from=2020-01&to=2025-12");
    const parsed = parseViewState(params);
    expect(parsed.area).toBe(DEFAULT_VIEW_STATE.area);
  });

  it("replaces malformed bbox with default area", () => {
    const params = new URLSearchParams("area=bbox:92.6,26.4,88.1,21.5"); // reversed west/east
    const parsed = parseViewState(params);
    expect(parsed.area).toBe(DEFAULT_VIEW_STATE.area);
  });

  it("corrects reversed dates (from > to) by swapping them", () => {
    const params = new URLSearchParams("from=2024-12&to=2020-01");
    const parsed = parseViewState(params);
    expect(parsed.from).toBe("2020-01");
    expect(parsed.to).toBe("2024-12");
  });

  it("falls back to default dates when malformed dates are given", () => {
    const params = new URLSearchParams("from=not-a-date&to=2025-99");
    const parsed = parseViewState(params);
    expect(parsed.from).toBe(DEFAULT_VIEW_STATE.from);
    expect(parsed.to).toBe(DEFAULT_VIEW_STATE.to);
  });

  it("falls back to harmonized when an invalid metric is passed", () => {
    const params = new URLSearchParams("metric=unknown_sensor");
    const parsed = parseViewState(params);
    expect(parsed.metric).toBe("harmonized");
  });

  it("ignores invalid cell values and parses valid 15-character hex cells", () => {
    const validParams = new URLSearchParams("cell=87642825FFFFFFF");
    expect(parseViewState(validParams).cell).toBe("87642825fffffff");

    const invalidParams = new URLSearchParams("cell=toolongcell12345678");
    expect(parseViewState(invalidParams).cell).toBeNull();

    const notHexParams = new URLSearchParams("cell=87642825zzzzzzz");
    expect(parseViewState(notHexParams).cell).toBeNull();
  });
});

