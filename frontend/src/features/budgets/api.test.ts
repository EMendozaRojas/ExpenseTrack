import { afterEach, describe, expect, it, vi } from "vitest";

import { createBudget, deleteBudget, listBudgets, updateBudget } from "./api";

function mockFetchOnce(body: unknown, status = 200) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status,
    json: async () => body,
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("budgets api", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("listBudgets consulta /budgets/ con year y month", async () => {
    const fetchMock = mockFetchOnce([]);

    await listBudgets("token-123", 2026, 3);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/budgets/?year=2026&month=3");
    expect(init.headers.Authorization).toBe("Bearer token-123");
  });

  it("createBudget envía category_id y amount", async () => {
    const fetchMock = mockFetchOnce({ id: 1 });

    await createBudget("token-123", { category_id: 5, amount: "200.00" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/budgets/");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({ category_id: 5, amount: "200.00" });
  });

  it("updateBudget hace PATCH sobre /budgets/{id}", async () => {
    const fetchMock = mockFetchOnce({ id: 1 });

    await updateBudget("token-123", 1, { amount: "250.00" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/budgets/1");
    expect(init.method).toBe("PATCH");
  });

  it("deleteBudget hace DELETE sobre /budgets/{id}", async () => {
    const fetchMock = mockFetchOnce(undefined, 204);

    await deleteBudget("token-123", 1);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/budgets/1");
    expect(init.method).toBe("DELETE");
  });
});
