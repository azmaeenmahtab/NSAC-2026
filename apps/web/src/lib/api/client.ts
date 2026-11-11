import { env } from "@/lib/env";
import { ApiError } from "./errors";

export interface ApiMeta {
  dataVersion?: string;
  asOf?: string;
  provisionalFrom?: string | null;
  [key: string]: unknown;
}

export interface ApiResponse<T> {
  data: T;
  meta: ApiMeta;
}

function buildUrl(endpoint: string, params?: Record<string, unknown>): string {
  let base: string;
  if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
    base = endpoint;
  } else {
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    const prefix = cleanEndpoint.startsWith("/api") ? "" : "/api";
    base = `${env.apiUrl}${prefix}${cleanEndpoint}`;
  }

  if (!params) return base;

  const url = new URL(base);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorData: { code?: string; message: string; requestId?: string; retryAfter?: number };
    try {
      const json = await res.json();
      if (json.error) {
        errorData = {
          code: json.error.code,
          message: json.error.message || `Request failed with status ${res.status}`,
          requestId: json.error.requestId,
        };
      } else {
        errorData = { message: `Request failed with status ${res.status}` };
      }
    } catch {
      errorData = { message: res.statusText || `Request failed with status ${res.status}` };
    }

    const retryAfterHeader = res.headers.get("Retry-After");
    if (retryAfterHeader) {
      const seconds = parseInt(retryAfterHeader, 10);
      if (!isNaN(seconds)) {
        errorData.retryAfter = seconds;
      }
    }

    throw new ApiError(res.status, errorData);
  }

  return res.json() as Promise<T>;
}

export async function apiGet<T>(
  endpoint: string,
  params?: Record<string, unknown>,
  options?: RequestInit
): Promise<T> {
  const url = buildUrl(endpoint, params);
  const res = await fetch(url, {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  return handleResponse<T>(res);
}

export async function apiPost<T>(
  endpoint: string,
  body?: unknown,
  options?: RequestInit
): Promise<T> {
  const url = buildUrl(endpoint);
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(options?.headers || {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...options,
  });

  return handleResponse<T>(res);
}

