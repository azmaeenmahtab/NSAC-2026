export type H3Resolution = 5 | 6 | 7;

export function getResolutionForZoom(zoom: number): H3Resolution {
  if (zoom < 6.0) return 5;
  if (zoom < 8.0) return 6;
  return 7;
}


