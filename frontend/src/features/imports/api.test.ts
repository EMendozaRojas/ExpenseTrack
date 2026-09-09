import { afterEach, describe, expect, it, vi } from "vitest";

import { commitImport, uploadStatement } from "./api";

function mockFetchOnce(body: unknown, status = 200) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status,
    json: async () => body,
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("imports api", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("uploadStatement envía multipart con account_id y file, sin forzar Content-Type", async () => {
    const fetchMock = mockFetchOnce({
      id: 1,
      account_id: 5,
      filename: "extracto.csv",
      status: "previewed",
      range_start: "2026-03-01",
      range_end: "2026-03-03",
      created_at: "2026-03-04T00:00:00Z",
      new_count: 1,
      exact_duplicate_count: 0,
      probable_duplicate_count: 0,
      rows: [],
    });

    const file = new File(["a,b\n1,2"], "extracto.csv", { type: "text/csv" });
    await uploadStatement("token-123", 5, file);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/imports/");
    expect(init.method).toBe("POST");
    expect(init.headers.Authorization).toBe("Bearer token-123");
    expect(init.headers["Content-Type"]).toBeUndefined();
    expect(init.body).toBeInstanceOf(FormData);
    expect((init.body as FormData).get("account_id")).toBe("5");
    expect((init.body as FormData).get("file")).toBe(file);
  });

  it("uploadStatement lanza ApiError con el detail del backend", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: async () => ({ detail: "No se reconocen las columnas" }),
      }),
    );

    const file = new File(["a"], "extracto.csv", { type: "text/csv" });
    await expect(uploadStatement("token-123", 5, file)).rejects.toThrow(
      "No se reconocen las columnas",
    );
  });

  it("commitImport envía strategy y row_ids como JSON", async () => {
    const fetchMock = mockFetchOnce({
      id: 1,
      status: "committed",
      strategy: "append_new",
      inserted_count: 2,
      replaced_count: 0,
      skipped_count: 1,
    });

    await commitImport("token-123", 1, "append_new", [7, 8]);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/imports/1/commit");
    expect(JSON.parse(init.body as string)).toEqual({
      strategy: "append_new",
      row_ids: [7, 8],
    });
  });
});
