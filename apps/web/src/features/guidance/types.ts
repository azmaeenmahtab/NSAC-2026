export type GuidanceStage =
  | "pre_season"
  | "in_season"
  | "post_season"
  | "extreme"
  | "off_season";

export type AudienceFilter = "all" | "community" | "land_manager" | "responder";

export interface GuidanceItem {
  id: string;
  stage: GuidanceStage;
  audience: string;
  text: string;
  source_title?: string;
  source_url?: string;
  verified: boolean;
}

export interface ActionPlannerProps {
  areaId: string;
  areaName?: string;
  month?: number;
  stage?: GuidanceStage;
}

