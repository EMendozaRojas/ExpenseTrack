import { afterEach, describe, expect, it, vi } from "vitest";

import {
  addContribution,
  createGoal,
  deleteContribution,
  deleteGoal,
  getProjection,
  listContributions,
  listGoals,
  updateGoal,
} from "./api";

function mockFetchOnce(body: unknown, status = 200) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status,
    json: async () => body,
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("goals api", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("listGoals consulta /goals/", async () => {
    const fetchMock = mockFetchOnce([]);
    await listGoals("token-123");
    expect(fetchMock.mock.calls[0][0]).toContain("/goals/");
  });

  it("createGoal envía el payload como JSON", async () => {
    const fetchMock = mockFetchOnce({ id: 1 });
    await createGoal("token-123", { name: "Viaje", target_amount: "1000.00" });
    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({ name: "Viaje", target_amount: "1000.00" });
  });

  it("updateGoal hace PATCH", async () => {
    const fetchMock = mockFetchOnce({ id: 1 });
    await updateGoal("token-123", 1, { status: "archived" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/goals/1");
    expect(init.method).toBe("PATCH");
  });

  it("deleteGoal hace DELETE", async () => {
    const fetchMock = mockFetchOnce(undefined, 204);
    await deleteGoal("token-123", 1);
    expect(fetchMock.mock.calls[0][1].method).toBe("DELETE");
  });

  it("addContribution envía amount y contributed_at", async () => {
    const fetchMock = mockFetchOnce({ id: 1 });
    await addContribution("token-123", 1, { amount: "50.00", contributed_at: "2026-03-01" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/goals/1/contributions");
    expect(JSON.parse(init.body as string)).toEqual({
      amount: "50.00",
      contributed_at: "2026-03-01",
    });
  });

  it("listContributions consulta /goals/{id}/contributions", async () => {
    const fetchMock = mockFetchOnce([]);
    await listContributions("token-123", 1);
    expect(fetchMock.mock.calls[0][0]).toContain("/goals/1/contributions");
  });

  it("deleteContribution hace DELETE sobre la aportación", async () => {
    const fetchMock = mockFetchOnce(undefined, 204);
    await deleteContribution("token-123", 1, 9);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/goals/1/contributions/9");
    expect(init.method).toBe("DELETE");
  });

  it("getProjection consulta /goals/{id}/projection", async () => {
    const fetchMock = mockFetchOnce({
      has_enough_data: false,
      monthly_pace: "0",
      months_remaining: null,
      projected_date: null,
    });
    await getProjection("token-123", 1);
    expect(fetchMock.mock.calls[0][0]).toContain("/goals/1/projection");
  });
});
