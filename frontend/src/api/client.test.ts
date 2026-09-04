import { afterEach, describe, expect, it, vi } from "vitest";

import { apiFetch, ApiError } from "./client";

describe("apiFetch", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("adjunta el token como Bearer y devuelve el JSON parseado", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: 1 }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiFetch<{ id: number }>("/categories/", "token-123");

    expect(result).toEqual({ id: 1 });
    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers.Authorization).toBe("Bearer token-123");
  });

  it("devuelve undefined en respuestas 204", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, status: 204, json: async () => null }),
    );

    const result = await apiFetch<void>("/expenses/1", "token-123", { method: "DELETE" });

    expect(result).toBeUndefined();
  });

  it("lanza ApiError con el detail del backend cuando la respuesta falla", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 409,
        json: async () => ({ detail: "El email ya está registrado" }),
      }),
    );

    await expect(apiFetch("/auth/register")).rejects.toMatchObject({
      status: 409,
      message: "El email ya está registrado",
    });
  });

  it("extrae el primer mensaje cuando detail es una lista de errores de validación", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: async () => ({ detail: [{ msg: "El monto debe ser mayor a 0" }] }),
      }),
    );

    await expect(apiFetch("/expenses/")).rejects.toBeInstanceOf(ApiError);
    await expect(apiFetch("/expenses/")).rejects.toMatchObject({
      message: "El monto debe ser mayor a 0",
    });
  });

  it("usa un mensaje genérico si el cuerpo del error no es JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error("not json");
        },
      }),
    );

    await expect(apiFetch("/health")).rejects.toMatchObject({
      status: 500,
      message: "La petición falló con estado 500",
    });
  });
});
