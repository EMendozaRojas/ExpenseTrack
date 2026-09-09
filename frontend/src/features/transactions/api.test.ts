import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createAccount,
  createCategory,
  createTransaction,
  deleteTransaction,
  getDashboardSummary,
  getMonthlySummary,
  listAccounts,
  listCategories,
  listTransactions,
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

describe("transactions api", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("listCategories consulta /categories/ con el token", async () => {
    const fetchMock = mockFetchOnce([]);

    await listCategories("token-123");

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/categories/");
    expect(init.headers.Authorization).toBe("Bearer token-123");
  });

  it("createCategory envía el nombre como JSON", async () => {
    const fetchMock = mockFetchOnce({ id: 1, name: "Ocio" });

    await createCategory("token-123", "Ocio");

    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ name: "Ocio" });
  });

  it("listAccounts consulta /accounts/", async () => {
    const fetchMock = mockFetchOnce([]);

    await listAccounts("token-123");

    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain("/accounts/");
  });

  it("createAccount envía el payload como JSON", async () => {
    const fetchMock = mockFetchOnce({ id: 1 });

    await createAccount("token-123", { name: "Efectivo", type: "cash" });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ name: "Efectivo", type: "cash" });
  });

  it("listTransactions filtra por rango de fechas", async () => {
    const fetchMock = mockFetchOnce({ items: [], next_cursor: null });

    await listTransactions("token-123", "2026-08-01", "2026-08-31");

    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain("/transactions/?date_from=2026-08-01&date_to=2026-08-31");
  });

  it("createTransaction envía el payload del movimiento como JSON", async () => {
    const fetchMock = mockFetchOnce({ id: 1 });

    await createTransaction("token-123", {
      account_id: 1,
      amount: "-10.00",
      direction: "expense",
      posted_at: "2026-08-13",
      category_id: 1,
      note: "Cena",
    });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({
      account_id: 1,
      amount: "-10.00",
      direction: "expense",
      posted_at: "2026-08-13",
      category_id: 1,
      note: "Cena",
    });
  });

  it("deleteTransaction hace DELETE al id indicado", async () => {
    const fetchMock = mockFetchOnce(null, 204);

    await deleteTransaction("token-123", 7);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/transactions/7");
    expect(init.method).toBe("DELETE");
  });

  it("getMonthlySummary consulta /expenses/summary con year y month", async () => {
    const fetchMock = mockFetchOnce({ year: 2026, month: 8, total: "0", by_category: [] });

    await getMonthlySummary("token-123", 2026, 8);

    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain("/expenses/summary?year=2026&month=8");
  });

  it("getDashboardSummary consulta /dashboard/summary con year y month", async () => {
    const fetchMock = mockFetchOnce({
      year: 2026,
      month: 8,
      income_total: "0",
      expense_total: "0",
      net_total: "0",
      net_status: "a_favor",
      fixed_total: "0",
      variable_total: "0",
      by_category: [],
      incomplete_data: false,
      last_transaction_date: null,
    });

    await getDashboardSummary("token-123", 2026, 8);

    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain("/dashboard/summary?year=2026&month=8");
  });
});
