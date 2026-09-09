import { afterEach, describe, expect, it, vi } from "vitest";

import {
  dismissRecurringSeries,
  getInsightSettings,
  listAntSpending,
  listRecurringSeries,
  restoreRecurringSeries,
  updateInsightSettings,
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

describe("insights api", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("listRecurringSeries consulta /insights/recurring", async () => {
    const fetchMock = mockFetchOnce([]);
    await listRecurringSeries("token-123");
    expect(fetchMock.mock.calls[0][0]).toContain("/insights/recurring");
  });

  it("dismissRecurringSeries envía POST con series_key", async () => {
    const fetchMock = mockFetchOnce(undefined, 204);
    await dismissRecurringSeries("token-123", "expense:NETFLIX");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/insights/recurring/dismiss");
    expect(JSON.parse(init.body as string)).toEqual({ series_key: "expense:NETFLIX" });
  });

  it("restoreRecurringSeries envía POST con series_key", async () => {
    const fetchMock = mockFetchOnce(undefined, 204);
    await restoreRecurringSeries("token-123", "expense:NETFLIX");
    expect(fetchMock.mock.calls[0][0]).toContain("/insights/recurring/restore");
  });

  it("listAntSpending consulta /insights/ant-spending con year y month", async () => {
    const fetchMock = mockFetchOnce([]);
    await listAntSpending("token-123", 2026, 3);
    expect(fetchMock.mock.calls[0][0]).toContain("/insights/ant-spending?year=2026&month=3");
  });

  it("getInsightSettings consulta /insights/settings", async () => {
    const fetchMock = mockFetchOnce({
      ant_max_amount: "10.00",
      ant_min_occurrences: 5,
      ant_min_aggregate: "30.00",
    });
    await getInsightSettings("token-123");
    expect(fetchMock.mock.calls[0][0]).toContain("/insights/settings");
  });

  it("updateInsightSettings hace PATCH con los campos cambiados", async () => {
    const fetchMock = mockFetchOnce({
      ant_max_amount: "15.00",
      ant_min_occurrences: 5,
      ant_min_aggregate: "30.00",
    });
    await updateInsightSettings("token-123", { ant_max_amount: "15.00" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/insights/settings");
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(init.body as string)).toEqual({ ant_max_amount: "15.00" });
  });
});
