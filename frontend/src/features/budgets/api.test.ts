import { afterEach, describe, expect, it, vi } from "vitest";

import {
  copyBudgets,
  createBudget,
  deleteBudget,
  getCopyPreview,
  listBudgets,
  listPlannedMonths,
  listRecommendations,
  updateBudget,
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

  it("createBudget envía categoría, mes, monto y repetir", async () => {
    const fetchMock = mockFetchOnce({});
    const payload = { category_id: 5, year: 2026, month: 10, amount: "200.00", repeat: true };

    await createBudget("token-123", payload);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/budgets/");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual(payload);
  });

  it("updateBudget hace PUT sobre /budgets/{categoría}/{mes} con el alcance", async () => {
    const fetchMock = mockFetchOnce({});

    await updateBudget("token-123", 5, "2026-11", { amount: "250.00", scope: "following" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/budgets/5/2026-11");
    expect(init.method).toBe("PUT");
    expect(JSON.parse(init.body as string)).toEqual({ amount: "250.00", scope: "following" });
  });

  it("deleteBudget hace DELETE con el alcance en la query", async () => {
    const fetchMock = mockFetchOnce(undefined, 204);

    await deleteBudget("token-123", 5, "2026-11", "this");

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/budgets/5/2026-11?scope=this");
    expect(init.method).toBe("DELETE");
  });

  it("listPlannedMonths, getCopyPreview y listRecommendations usan sus rutas", async () => {
    const fetchMock = mockFetchOnce([]);

    await listPlannedMonths("token-123", 5, "2026-11");
    await getCopyPreview("token-123", 2026, 11);
    await listRecommendations("token-123", 5);
    await listRecommendations("token-123");

    const urls = fetchMock.mock.calls.map((call) => call[0] as string);
    expect(urls[0]).toContain("/budgets/5/planned?from=2026-11");
    expect(urls[1]).toContain("/budgets/copy-preview?year=2026&month=11");
    expect(urls[2]).toContain("/budgets/recommendations?category_id=5");
    expect(urls[3]).toMatch(/\/budgets\/recommendations$/);
  });

  it("copyBudgets hace POST con los items elegidos", async () => {
    const fetchMock = mockFetchOnce({ created: [5], skipped: [] });
    const payload = { year: 2026, month: 11, items: [{ category_id: 5, amount: "100.00" }] };

    await copyBudgets("token-123", payload);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/budgets/copy");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual(payload);
  });
});
