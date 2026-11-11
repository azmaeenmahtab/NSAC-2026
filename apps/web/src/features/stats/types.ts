export interface YearlyStatRow {
  year: number;
  harmonized_total: number;
  frp_sum?: number;
  total_frp_mw?: number;
  total_events?: number;
  rank: number;
  vs_mean_pct: number;
  peak_month: number;
}

export type SortField =
  | "year"
  | "harmonized_total"
  | "frp_sum"
  | "rank"
  | "vs_mean_pct"
  | "peak_month";

export type SortDirection = "asc" | "desc";

export interface YearlyStatsProps {
  areaId: string;
  selectedYear?: number | null;
  onSelectYear?: (year: number) => void;
}

