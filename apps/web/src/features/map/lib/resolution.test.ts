import { describe, it, expect } from "vitest";
import { getResolutionForZoom } from "./resolution";

describe("Map H3 Resolution by Zoom (resolution.ts)", () => {
  it("maps zoom levels below 6 to resolution 5", () => {
    expect(getResolutionForZoom(3)).toBe(5);
    expect(getResolutionForZoom(5)).toBe(5);
    expect(getResolutionForZoom(5.99)).toBe(5);
  });

  it("maps zoom levels between 6 and 8 to resolution 6", () => {
    expect(getResolutionForZoom(6.0)).toBe(6);
    expect(getResolutionForZoom(7.0)).toBe(6);
    expect(getResolutionForZoom(7.99)).toBe(6);
  });

  it("maps zoom levels 8 and above to resolution 7", () => {
    expect(getResolutionForZoom(8.0)).toBe(7);
    expect(getResolutionForZoom(9.0)).toBe(7);
    expect(getResolutionForZoom(12.0)).toBe(7);
  });
});

