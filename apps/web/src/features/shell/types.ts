export interface MetaData {
  dataVersion: string;
  asOf: string;
  provisionalFrom?: string | null;
  attribution?: string;
  parametersSummary?: Record<string, unknown>;
  sources?: Array<{ file_name: string; sensor: string }>;
  counts?: Record<string, number>;
}
