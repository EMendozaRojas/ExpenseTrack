import { afterEach, describe, expect, it, vi } from "vitest";

import { deleteAttachment, fetchAttachmentBlob, listAttachments, uploadAttachment } from "./api";

function mockFetchOnce(body: unknown, status = 200) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status,
    json: async () => body,
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("attachments api", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("listAttachments consulta /transactions/{id}/attachments", async () => {
    const fetchMock = mockFetchOnce([]);
    await listAttachments("token-123", 7);
    expect(fetchMock.mock.calls[0][0]).toContain("/transactions/7/attachments");
  });

  it("uploadAttachment envía multipart sin forzar Content-Type", async () => {
    const fetchMock = mockFetchOnce({ id: 1, filename: "recibo.png" });
    const file = new File(["a"], "recibo.png", { type: "image/png" });

    await uploadAttachment("token-123", 7, file);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/transactions/7/attachments");
    expect(init.method).toBe("POST");
    expect(init.headers.Authorization).toBe("Bearer token-123");
    expect(init.headers["Content-Type"]).toBeUndefined();
    expect((init.body as FormData).get("file")).toBe(file);
  });

  it("deleteAttachment hace DELETE sobre /attachments/{id}", async () => {
    const fetchMock = mockFetchOnce(undefined, 204);
    await deleteAttachment("token-123", 9);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/attachments/9");
    expect(init.method).toBe("DELETE");
  });

  it("fetchAttachmentBlob pide el binario con el header de auth", async () => {
    const blob = new Blob(["contenido"]);
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      blob: async () => blob,
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchAttachmentBlob("token-123", 9);

    expect(result).toBe(blob);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/attachments/9");
    expect(init.headers.Authorization).toBe("Bearer token-123");
  });
});
