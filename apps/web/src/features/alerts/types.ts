export type AlertRule = "season_approaching" | "above_normal" | "both";

export interface ActiveAlerts {
  season_approaching: boolean;
  above_normal: boolean;
  current_month_class?: "normal" | "elevated" | "extreme";
  days_until_season?: number | null;
  reason?: string | null;
  provisional_as_of?: string | null;
}

export interface SubscriptionPayload {
  email: string;
  area_id: string;
  rule: AlertRule;
  lead_days: number;
}

export interface SubscriptionResponse {
  message: string;
  status: string;
}

export interface ConfirmResponse {
  confirmed: boolean;
}

