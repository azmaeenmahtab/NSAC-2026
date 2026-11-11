export type AreaLevel = "country" | "adm1" | "adm2" | "preset" | "custom";

export interface AreaItem {
  id: string;
  name: string;
  level: AreaLevel;
  parent_id?: string | null;
  parent_name?: string | null;
  bbox: [number, number, number, number]; // [minX, minY, maxX, maxY]
  aliases?: string[];
}

export type MetricType = "harmonized" | "raw_modis" | "raw_viirs";

export interface ViewState {
  area: string;
  from: string; // YYYY-MM
  to: string; // YYYY-MM
  metric: MetricType;
  cell: string | null; // lowercase hex H3 index
}
