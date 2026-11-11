import { describe, it, expect, beforeAll, afterAll, afterEach } from "vitest";
import { server } from "./server";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("MSW API Mocking", () => {
  it("fetches /api/meta successfully from mock server", async () => {
    const res = await fetch("http://localhost:8000/api/meta");
    expect(res.ok).toBe(true);

    const json = await res.json();
    expect(json.data.dataVersion).toBe("v0.1.0-fixtures");
    expect(json.data.asOf).toBe("2025-12-31");
    expect(json.meta.dataVersion).toBe("v0.1.0-fixtures");
  });

  it("fetches /api/areas from mock server", async () => {
    const res = await fetch("http://localhost:8000/api/areas");
    expect(res.ok).toBe(true);

    const json = await res.json();
    expect(json.data).toHaveLength(3);
    expect(json.data[0].id).toBe("BGD");
    expect(json.data[1].id).toBe("BGD-ADM2-alpha");
  });
});
