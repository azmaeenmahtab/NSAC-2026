export interface Citation {
  tool: string;
  areaId?: string | null;
  years?: number[];
  dataVersion: string;
}

export interface ToolCallLog {
  name: string;
  args: Record<string, unknown>;
  durationMs: number;
}

export interface AreaCandidate {
  id: string;
  name: string;
}

export interface AskResponse {
  answer: string;
  citations: Citation[];
  toolCalls: ToolCallLog[];
  mode: "live" | "replay";
  candidates?: AreaCandidate[];
}

export type AskStyle = "standard" | "plain";

export interface AskRequest {
  question: string;
  area_id?: string | null;
  style?: AskStyle;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  response?: AskResponse;
  isPending?: boolean;
  error?: string;
  isRateLimited?: boolean;
  retryAfterSeconds?: number;
}
