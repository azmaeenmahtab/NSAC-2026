export type AnomalyClass = "normal" | "elevated" | "extreme";

export interface CalendarCell {
  year: number;
  month: number;
  value: number;
  class: AnomalyClass;
  percentile_rank: number;
  provisional?: boolean;
}

export type CalendarCellData = CalendarCell;

export interface MonthClimatology {
  month: number;
  mean: number;
  p50: number;
  p90: number;
  p95: number;
}

export interface FireSeason {
  start_month: number;
  peak_month: number;
  end_month: number;
  share_of_annual: number;
}

export interface CalendarData {
  grid: CalendarCell[];
  climatology: MonthClimatology[];
  season: FireSeason;
}
