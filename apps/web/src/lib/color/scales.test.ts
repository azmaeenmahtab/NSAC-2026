import { describe, it, expect } from "vitest";
import {
  INFERNO_HEX_STEPS,
  INFERNO_RGBA_STEPS,
  getInfernoStepIndex,
  getInfernoStepHex,
  normalizeClipped,
  getInfernoRgba,
} from "./scales";
import { ANOMALY_CONFIGS } from "./legend";
import { formatYearMonth, formatNumber, formatPercentile } from "../format";

describe("Inferno Color Scales and Formatting", () => {
  it("provides exactly 8 Inferno hex and RGBA steps", () => {
    expect(INFERNO_HEX_STEPS).toHaveLength(8);
    expect(INFERNO_RGBA_STEPS).toHaveLength(8);
    expect(INFERNO_HEX_STEPS[0]).toBe("#000004");
    expect(INFERNO_HEX_STEPS[7]).toBe("#fcffa4");
  });

  it("maps numeric fire event counts to the appropriate Inferno step index", () => {
    expect(getInfernoStepIndex(0)).toBe(0);
    expect(getInfernoStepIndex(3)).toBe(1);
    expect(getInfernoStepIndex(10)).toBe(2);
    expect(getInfernoStepIndex(25)).toBe(3);
    expect(getInfernoStepIndex(50)).toBe(4);
    expect(getInfernoStepIndex(100)).toBe(5);
    expect(getInfernoStepIndex(200)).toBe(6);
    expect(getInfernoStepIndex(500)).toBe(7);

    expect(getInfernoStepHex(500)).toBe("#fcffa4");
  });

  it("clips normalization cleanly at p95", () => {
    expect(normalizeClipped(50, 100)).toBeCloseTo(0.5);
    expect(normalizeClipped(150, 100)).toBe(1.0);
    expect(normalizeClipped(-5, 100)).toBe(0);
    expect(normalizeClipped(50, 0)).toBe(0);
  });

  it("interpolates RGBA colors for deck.gl", () => {
    const zeroRgba = getInfernoRgba(0);
    expect(zeroRgba).toHaveLength(4);
    expect(zeroRgba[3]).toBe(230);

    const peakRgba = getInfernoRgba(1.0);
    expect(peakRgba[0]).toBeGreaterThan(200); // Yellow high red channel
    expect(peakRgba[1]).toBeGreaterThan(200); // Yellow high green channel
  });

  it("configures non-color cues for all anomaly classes", () => {
    expect(ANOMALY_CONFIGS.normal.symbol).toBe("●");
    expect(ANOMALY_CONFIGS.elevated.symbol).toBe("▲");
    expect(ANOMALY_CONFIGS.extreme.symbol).toBe("◆");
    expect(ANOMALY_CONFIGS.extreme.hex).toBe("#ef4444");
  });

  it("formats dates and numbers correctly", () => {
    expect(formatYearMonth(2021, 3)).toBe("March 2021");
    expect(formatPercentile(98)).toBe("98th");
    expect(formatPercentile(91)).toBe("91st");
    expect(formatPercentile(92)).toBe("92nd");
    expect(formatPercentile(93)).toBe("93rd");
    expect(formatNumber(12500)).toBe("12,500");
  });
});

