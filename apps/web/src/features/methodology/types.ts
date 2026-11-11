export interface JumpMetricsData {
  naive_ratio: number;
  harmonized_ratio: number;
  overlap_cv_rmse?: number | null;
  overlap_cv_bias?: number | null;
  rank_correlation?: number | null;
}

export type JumpMetrics = JumpMetricsData;

export interface CalibrationUnitSummary {
  unit_id: string;
  name?: string;
  method: string;
  fallback: boolean;
  rmse?: number;
  bias?: number;
  rank_corr?: number;
  flag?: string;
}

export interface QQPoint {
  quantile: number;
  modis: number;
  viirs_raw: number;
  viirs_harmonized: number;
}

export interface MethodologyData {
  parameters: Record<string, unknown>;
  calibration_summary?: CalibrationUnitSummary[];
  jump_metrics?: JumpMetricsData | null;
  qq_data?: QQPoint[];
  limitations: string[];
}
