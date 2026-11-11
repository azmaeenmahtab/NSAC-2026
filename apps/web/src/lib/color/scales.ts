import { interpolateInferno } from "d3-scale-chromatic";
import { rgb } from "d3-color";

export const INFERNO_THRESHOLDS = [1, 5, 20, 50, 100, 200, 500];

export function normalizeClipped(value: number, max: number): number {
  if (max <= 0) return 0;
  return Math.max(0, Math.min(1, value / max));
}

export function getInfernoRgba(
  t: number,
  alpha: number = 230
): [number, number, number, number] {
  const clampedT = Math.max(0, Math.min(1, t));
  const c = rgb(interpolateInferno(clampedT));
  return [c.r, c.g, c.b, alpha];
}

export function infernoRgba(
  value: number,
  p95: number
): [number, number, number, number] {
  const t = normalizeClipped(value, Math.max(1e-6, p95));
  return getInfernoRgba(t, 215);
}

export const INFERNO_HEX_STEPS: string[] = Array.from({ length: 8 }, (_, i) => {
  const c = rgb(interpolateInferno(i / 7));
  return c.formatHex
    ? c.formatHex()
    : `#${Math.round(c.r).toString(16).padStart(2, "0")}${Math.round(c.g).toString(16).padStart(2, "0")}${Math.round(c.b).toString(16).padStart(2, "0")}`;
});

export const INFERNO_RGBA_STEPS: [number, number, number, number][] = Array.from(
  { length: 8 },
  (_, i) => getInfernoRgba(i / 7, 230)
);

export function getInfernoStepIndex(count: number): number {
  for (let i = INFERNO_THRESHOLDS.length - 1; i >= 0; i--) {
    if (count >= INFERNO_THRESHOLDS[i]) {
      return i + 1;
    }
  }
  return 0;
}

export function getInfernoStepHex(count: number): string {
  const idx = getInfernoStepIndex(count);
  return INFERNO_HEX_STEPS[idx];
}
