export type BoundingBox = [number, number, number, number]; // [minX/west, minY/south, maxX/east, maxY/north]

export function parseBBox(str: string): BoundingBox | null {
  if (!str) return null;
  const prefix = "bbox:";
  const clean = str.startsWith(prefix) ? str.slice(prefix.length) : str;
  const parts = clean.split(",").map((p) => parseFloat(p.trim()));

  if (parts.length !== 4 || parts.some((p) => isNaN(p))) {
    return null;
  }

  const [w, s, e, n] = parts;
  return [w, s, e, n];
}

export function formatBBox(bbox: BoundingBox): string {
  const [w, s, e, n] = bbox;
  return `bbox:${w.toFixed(4)},${s.toFixed(4)},${e.toFixed(4)},${n.toFixed(4)}`;
}

export function getBBoxCenter(bbox: BoundingBox): [number, number] {
  const [w, s, e, n] = bbox;
  const lon = (w + e) / 2;
  const lat = (s + n) / 2;
  return [lon, lat];
}

export function calculateBBoxAreaKm2(bbox: BoundingBox): number {
  const [w, s, e, n] = bbox;
  const dLatKm = Math.abs(n - s) * 111.0;
  const midLatRad = (((s + n) / 2) * Math.PI) / 180;
  const dLonKm = Math.abs(e - w) * 111.0 * Math.cos(midLatRad);
  return Math.abs(dLatKm * dLonKm);
}

