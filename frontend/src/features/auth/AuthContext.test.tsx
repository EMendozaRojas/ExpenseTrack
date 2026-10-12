import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { authorizedFetch } from "../../api/client";
import * as api from "./api";
import { AuthProvider } from "./AuthContext";
import { useAuth } from "./useAuth";

vi.mock("./api");

const demoUser = {
  id: 1,
  email: "demo@example.com",
  full_name: "Demo User",
  has_avatar: false,
  created_at: "2026-01-01T00:00:00Z",
};

describe("AuthContext", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetAllMocks();
  });

  it("inicia sesión y guarda el usuario", async () => {
    vi.mocked(api.login).mockResolvedValue({ access_token: "abc123", token_type: "bearer" });
    vi.mocked(api.fetchCurrentUser).mockResolvedValue(demoUser);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.login({ email: demoUser.email, password: "secret123" });
    });

    await waitFor(() => expect(result.current.user?.email).toBe(demoUser.email));
    expect(localStorage.getItem("expensetrack_token")).toBe("abc123");
  });

  it("cierra sesión y limpia el token guardado", async () => {
    vi.mocked(api.login).mockResolvedValue({ access_token: "abc123", token_type: "bearer" });
    vi.mocked(api.fetchCurrentUser).mockResolvedValue(demoUser);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.login({ email: demoUser.email, password: "secret123" });
    });
    await waitFor(() => expect(result.current.user).not.toBeNull());

    act(() => result.current.logout());

    expect(result.current.user).toBeNull();
    expect(localStorage.getItem("expensetrack_token")).toBeNull();
  });

  it("restaura la sesión a partir de un token guardado en localStorage", async () => {
    localStorage.setItem("expensetrack_token", "existing-token");
    vi.mocked(api.fetchCurrentUser).mockResolvedValue({
      id: 2,
      email: "restored@example.com",
      full_name: "Restored User",
      has_avatar: false,
      created_at: "2026-01-01T00:00:00Z",
    });

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await waitFor(() => expect(result.current.user?.email).toBe("restored@example.com"));
    expect(api.fetchCurrentUser).toHaveBeenCalledWith("existing-token");
  });

  it("descarta el token si ya no es válido", async () => {
    localStorage.setItem("expensetrack_token", "expired-token");
    vi.mocked(api.fetchCurrentUser).mockRejectedValue(new Error("401"));

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem("expensetrack_token")).toBeNull();
  });

  it("loginWithTokens guarda access y refresh token (callback de login social)", async () => {
    vi.mocked(api.fetchCurrentUser).mockResolvedValue(demoUser);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.loginWithTokens("access-abc", "refresh-xyz"));

    await waitFor(() => expect(result.current.user?.email).toBe(demoUser.email));
    expect(localStorage.getItem("expensetrack_token")).toBe("access-abc");
    expect(localStorage.getItem("expensetrack_refresh_token")).toBe("refresh-xyz");
  });

  it("logout revoca el refresh token guardado en el backend", async () => {
    vi.mocked(api.login).mockResolvedValue({
      access_token: "abc123",
      token_type: "bearer",
      refresh_token: "refresh-1",
    });
    vi.mocked(api.fetchCurrentUser).mockResolvedValue(demoUser);
    vi.mocked(api.logoutRequest).mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.login({ email: demoUser.email, password: "secret123" });
    });
    await waitFor(() => expect(result.current.user).not.toBeNull());

    act(() => result.current.logout());

    expect(api.logoutRequest).toHaveBeenCalledWith("refresh-1");
    expect(localStorage.getItem("expensetrack_refresh_token")).toBeNull();
  });

  it("al caducar el token lo renueva con el refresh token y guarda los nuevos", async () => {
    localStorage.setItem("expensetrack_token", "token-caducado");
    localStorage.setItem("expensetrack_refresh_token", "refresh-viejo");
    vi.mocked(api.fetchCurrentUser).mockResolvedValue(demoUser);
    vi.mocked(api.refreshRequest).mockResolvedValue({
      access_token: "token-nuevo",
      refresh_token: "refresh-nuevo",
      token_type: "bearer",
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: false, status: 401, json: async () => ({}) })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({}) });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    let status = 0;
    await act(async () => {
      status = (await authorizedFetch("/api/v1/accounts/", "token-caducado")).status;
    });

    expect(status).toBe(200);
    expect(api.refreshRequest).toHaveBeenCalledWith("refresh-viejo");
    expect(localStorage.getItem("expensetrack_token")).toBe("token-nuevo");
    expect(localStorage.getItem("expensetrack_refresh_token")).toBe("refresh-nuevo");
    expect(result.current.token).toBe("token-nuevo");
    vi.unstubAllGlobals();
  });

  it("si el refresh token ya no vale, cierra la sesión", async () => {
    localStorage.setItem("expensetrack_token", "token-caducado");
    localStorage.setItem("expensetrack_refresh_token", "refresh-revocado");
    vi.mocked(api.fetchCurrentUser).mockResolvedValue(demoUser);
    vi.mocked(api.refreshRequest).mockRejectedValue(new Error("401"));
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 401, json: async () => ({}) }),
    );

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await authorizedFetch("/api/v1/accounts/", "token-caducado");
    });

    expect(result.current.token).toBeNull();
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem("expensetrack_refresh_token")).toBeNull();
    vi.unstubAllGlobals();
  });
});
