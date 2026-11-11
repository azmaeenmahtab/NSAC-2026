import { describe, it, expect } from "vitest";
import {
  parseBBox,
  isValidBBox,
  formatBBox,
  getBBoxCenter,
  calculateBBoxAreaKm2,
  type BoundingBox,
} from "./bbox";

describe("Bounding Box Utilities (bbox.ts)", () => {
  it("parses valid bbox strings with or without 'bbox:' prefix", () => {
    const parsed1 = parseBBox("bbox:88.1,21.5,92.6,26.4");
    expect(parsed1).toEqual([88.1, 21.5, 92.6, 26.4]);

    const parsed2 = parseBBox("88.1,21.5,92.6,26.4");
    expect(parsed2).toEqual([88.1, 21.5, 92.6, 26.4]);
  });

  it("rejects invalid bounding box strings or malformed numbers", () => {
    expect(parseBBox(null)).toBeNull();
    expect(parseBBox("")).toBeNull();
    expect(parseBBox("bbox:88.1,21.5,92.6")).toBeNull();
    expect(parseBBox("bbox:abc,21.5,92.6,26.4")).toBeNull();
  });

  it("rejects bbox where west >= east or south >= north", () => {
    // west >= east
    expect(isValidBBox([92.6, 21.5, 88.1, 26.4])).toBe(false);
    expect(isValidBBox([88.1, 21.5, 88.1, 26.4])).toBe(false);

    // south >= north
    expect(isValidBBox([88.1, 26.4, 92.6, 21.5])).toBe(false);
    expect(isValidBBox([88.1, 21.5, 92.6, 21.5])).toBe(false);
  });

  it("rejects out-of-range coordinates", () => {
    // lat > 90
    expect(isValidBBox([88.1, 21.5, 92.6, 95.0])).toBe(false);
    // lat < -90
    expect(isValidBBox([88.1, -95.0, 92.6, 26.4])).toBe(false);
    // lon > 180
    expect(isValidBBox([88.1, 21.5, 185.0, 26.4])).toBe(false);
    // lon < -180
    expect(isValidBBox([-185.0, 21.5, 92.6, 26.4])).toBe(false);
  });

  it("formats bbox correctly with formatBBox", () => {
    const bbox: BoundingBox = [91.8, 21.5, 92.8, 23.8];
    expect(formatBBox(bbox)).toBe("bbox:91.8,21.5,92.8,23.8");
  });

  it("computes bbox center coordinates accurately", () => {
    const bbox: BoundingBox = [90.0, 20.0, 92.0, 24.0];
    const center = getBBoxCenter(bbox);
    expect(center).toEqual([91.0, 22.0]);
  });

  it("computes approximate area in km²", () => {
    const bbox: BoundingBox = [91.0, 22.0, 92.0, 23.0]; // ~1 deg x 1 deg at 22.5 N
    const area = calculateBBoxAreaKm2(bbox);
    // 1 deg lat is ~111.32 km. 1 deg lon at 22.5 deg is ~102.8 km.
    // 111.32 * 102.8 ~= 11,443 km²
    expect(area).toBeGreaterThan(10000);
    expect(area).toBeLessThan(13000);
  });
});

