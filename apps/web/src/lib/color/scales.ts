import { interpolateInferno } from "d3-scale-chromatic";
import { rgb } from "d3-color";

export function normalizeClipped(value: number, max: number): number {
  if (max <= 0) return 0;
  return Math.max(0, Math.min(1, value / max));
}

export function getInfernoRgba(
  t: number,
  alpha: number = 255
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

