import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiGet, apiGetData } from "./client";
import { ApiError } from "./errors";

describe("API Client (apiGet and apiGetData)", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("parses successful JSON responses and handles query parameters", async () => {
    const mockEnvelope = {
      data: [{ id: "BGD", name: "Bangladesh" }],
      meta: { dataVersion: "v1.0.0", asOf: "2026-10-31" },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockEnvelope,
    } as unknown as Response);

    const result = await apiGet<typeof mockEnvelope>("/areas", {
      level: "country",
      limit: 10,
    });

    expect(result).toEqual(mockEnvelope);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/areas?level=country&limit=10"),
      expect.objectContaining({ method: "GET" })
    );
  });

  it("unwraps data payload cleanly with apiGetData helper", async () => {
    const mockData = { version: "1.0" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        data: mockData,
        meta: { dataVersion: "v1.0.0", asOf: "2026-10-31" },
      }),
    } as unknown as Response);

    const data = await apiGetData<{ version: string }>("/meta");
    expect(data).toEqual(mockData);
  });

  it("throws typed ApiError on HTTP 404 with API error envelope", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: async () => ({
        error: {
          code: "NOT_FOUND",
          message: "Region BGD-ADM2-unknown not found",
          requestId: "req-404",
        },
      }),
    } as unknown as Response);

    await expect(apiGet("/areas/unknown")).rejects.toThrow(ApiError);
    try {
      await apiGet("/areas/unknown");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(404);
      expect(apiErr.code).toBe("NOT_FOUND");
      expect(apiErr.requestId).toBe("req-404");
    }
  });

  it("throws UPSTREAM_ERROR on network connection failures", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("Connection refused"));

    await expect(apiGet("/meta")).rejects.toThrow(ApiError);
    try {
      await apiGet("/meta");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(502);
      expect(apiErr.code).toBe("UPSTREAM_ERROR");
    }
  });
});

