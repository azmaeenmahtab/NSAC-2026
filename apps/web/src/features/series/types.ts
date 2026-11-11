export interface SeriesPoint {
  year: number;
  month: number;
  raw_modis?: number | null;
  raw_viirs?: number | null;
  naive_splice: number;
  harmonized: number;
  in_overlap: boolean;
  source_used: "modis_raw" | "viirs_calibrated";
  provisional: boolean;
}

export interface MethodologyJumpMetrics {
  method: string;
  calibration_window: string;
  naive_ratio: number;
  harmonized_ratio: number;
  jump_reduction_pct: number;
  limitations?: string[];
}

export type SeriesVisibility = {
  raw_modis: boolean;
  raw_viirs: boolean;
  naive_splice: boolean;
  harmonized: boolean;
};
