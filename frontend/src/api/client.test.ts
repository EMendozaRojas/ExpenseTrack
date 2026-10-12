import { afterEach, describe, expect, it, vi } from "vitest";

import { apiFetch, ApiError, authorizedFetch, setSessionRefresher } from "./client";

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

describe("renovación de la sesión", () => {
  const ok = { ok: true, status: 200, json: async () => ({ id: 1 }) };
  const unauthorized = { ok: false, status: 401, json: async () => ({ detail: "Token caducado" }) };

  afterEach(() => {
    vi.unstubAllGlobals();
    setSessionRefresher(null);
  });

  it("tras un 401 renueva el token y repite la petición una vez", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(unauthorized).mockResolvedValueOnce(ok);
    vi.stubGlobal("fetch", fetchMock);
    const refresher = vi.fn().mockResolvedValue("token-nuevo");
    setSessionRefresher(refresher);

    const result = await apiFetch<{ id: number }>("/accounts/", "token-caducado");

    expect(result).toEqual({ id: 1 });
    expect(refresher).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[1][1].headers.Authorization).toBe("Bearer token-nuevo");
  });

  it("si la renovación falla, devuelve el 401 original", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(unauthorized));
    setSessionRefresher(vi.fn().mockResolvedValue(null));

    await expect(apiFetch("/accounts/", "token-caducado")).rejects.toMatchObject({ status: 401 });
  });

  it("varias peticiones con 401 a la vez comparten una sola renovación", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init: RequestInit) =>
        Promise.resolve(
          (init.headers as Record<string, string>).Authorization === "Bearer token-nuevo"
            ? ok
            : unauthorized,
        ),
      ),
    );
    let finishRefresh: (token: string) => void = () => {};
    const refresher = vi.fn(
      () =>
        new Promise<string>((resolve) => {
          finishRefresh = resolve;
        }),
    );
    setSessionRefresher(refresher);

    const requests = [1, 2, 3].map(() => authorizedFetch("/x", "token-caducado"));
    await vi.waitFor(() => expect(refresher).toHaveBeenCalled());
    finishRefresh("token-nuevo");
    const responses = await Promise.all(requests);

    expect(refresher).toHaveBeenCalledTimes(1);
    expect(responses.map((response) => response.status)).toEqual([200, 200, 200]);
  });

  it("sin token no intenta renovar (login, registro)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(unauthorized));
    const refresher = vi.fn();
    setSessionRefresher(refresher);

    await expect(apiFetch("/auth/login", null)).rejects.toMatchObject({ status: 401 });
    expect(refresher).not.toHaveBeenCalled();
  });
});
